import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional, Dict, List

from binance.error import ClientError
from binance.um_futures import UMFutures
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient

from a_songbo.binance_client.trade.do.account import AccountBook
from a_songbo.binance_client.trade.do.position import InstrumentPosition
from a_songbo.binance_client.trade.do.rtn_order import RtnOrder
from a_songbo.binance_client.trade.do.rtn_trade import RtnTrade
from a_songbo.binance_client.utils import type_util
from a_songbo.binance_client.utils.aio_timer import AioTimer
from a_songbo.binance_client.utils.exchange_enum import OffsetFlag, Direction, OrderPriceType
from a_songbo.binance_client.utils.sys_exception import common_exception
from a_songbo.binance_client.utils.thread import submit


DIRECTION_2VT = {
    (OffsetFlag.OPEN, Direction.LONG): ('BUY', 'LONG'),     # 开多
    (OffsetFlag.CLOSE, Direction.LONG): ('SELL', 'LONG'),   # 平多
    (OffsetFlag.OPEN, Direction.SHORT): ('SELL', 'SHORT'),  # 开空
    (OffsetFlag.CLOSE, Direction.SHORT): ('BUY', 'SHORT'),  # 平空
}
VT_2DIRECTION: Dict[tuple, tuple] = {v: k for k, v in DIRECTION_2VT.items()}


class BiFutureTd:

    def __init__(self, gateway):
        self.gateway = gateway

        self.configs: dict = gateway.get_api_configs()

        self.on_data_thread_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="td")

        self.account_book = AccountBook()

        self.order_ref_id: int = 0

        # 已初始化好的标的列表 (完成启动后撤单等动作)
        self.ready_instruments = set()
        # 记录状态. 连接、登录、初始化、就绪
        self.ready: bool = False
        # 当前进程登录请求次数
        self.reqUserLoginId = 0

        # 报单id映射，用于关联成交回报 { order_id : RtnOrder }
        self.rtn_order_map: Dict[str, RtnOrder] = dict()
        # 延时撤单任务 { order_id : AioTimer }
        self.cancel_order_map = dict()

        # 接口客户端
        self.client = None
        # 监听客户端
        self._listen_client = None
        self._listen_key: Optional[str] = None
        self._listen_last_ping_ts: Optional[float] = 0

        self._add_restart_listen_timer()
        # query account   check ping
        self._add_query_account_timer(interval=120)

    def connect(self):
        if self.client:
            self.logger.warning("已登录，勿重复操作!")
            return

        self.client = self._create_client()

        self.query_account()

        self._start_listen()

    def _create_client(self):
        return UMFutures(key=self.configs["api_key"], secret=self.configs["secret_key"],
                         base_url=self.configs.get("base_url"))

    def _start_listen(self):
        """ 启动监听 """
        if not self._listen_key:
            self._listen_key = self.client.new_listen_key()["listenKey"]
            self.logger.info("<new_listen_key> %s %s", self.reqUserLoginId, self._listen_key)

        if not self._listen_client:
            self._listen_client = self._create_listen_client()
            self.logger.info("<create_listen_client> %s", self._listen_client)

        self.reqUserLoginId += 1
        self._listen_client.user_data(listen_key=self._listen_key)
        self.logger.info("<listen_user_data> %s %s", self.reqUserLoginId, self._listen_key)

    def _create_listen_client(self):
        return UMFuturesWebsocketClient(
            stream_url=self.configs["stream_url"],
            is_combined=self.configs.get("is_combined", False),
            on_message=self._on_user_data,
            on_open=self._on_listen_open,
            on_close=self._on_listen_close,
            on_error=self._on_listen_error,
            on_ping=self._on_listen_ping)

    def _restart_listen(self):
        new_listen_key = None
        try:
            # 更新 listenKey
            if self._listen_key:
                result: dict = self.client.renew_listen_key(listenKey=self._listen_key)
                self.logger.info("<renew_listen_key> %s %s", self.reqUserLoginId, result)

                if result and result.__contains__("listenKey"):
                    new_listen_key = result["listenKey"]
        except ClientError as e:
            self.logger.exception("!!! renew_listen_key failed %s !!! %s %s",
                                  e, self.reqUserLoginId, self._listen_key)
            # 取消原订阅
            self._unsubscribe_user_data()

        # 重新启动监听
        if not self._listen_key or (new_listen_key and self._listen_key != new_listen_key):
            self._listen_key = new_listen_key
            self._start_listen()

    def _unsubscribe_user_data(self):
        # 更改状态
        self.ready = False

        # 取消订阅 (实盘发现 user_data UNSUBSCRIBE不起作用)
        # self.logger.info("<unsubscribe_user_data> %s %s", self.reqUserLoginId, self._listen_key)
        # self._listen_client.user_data(listen_key=self._listen_key, action="UNSUBSCRIBE")
        self._listen_key = None

    def _on_listen_open(self, _):
        self.logger.info(f"<on_listen_open> {self.reqUserLoginId} {self._listen_key} {_}")

    def _on_listen_ping(self, _, data):
        self._listen_last_ping_ts = time.time()
        self.logger.info(f"<on_listen_ping> {self._listen_last_ping_ts} {data}")

    @common_exception(log_flag=True)
    def _check_listen_ping(self):
        """ 检测监听的数据流连接是否断开, 超过3分钟没有收到on_ping回调说明出现了问题, 连续两次没收到时重启 """
        ts = time.time() - self._listen_last_ping_ts
        self.logger.info(f'<_check_listen_ping>_listen_last_ping_ts={self._listen_last_ping_ts} ts={ts}')
        if not self._listen_last_ping_ts or ts < 60 * 6:
            return
        self.logger.warning("!! check_listen_ping !! %s", ts)

        if ts < 60 * 9:
            self.gateway.on_front_disconnected(
                "连续{}分钟没有收到on_ping回调".format(round(ts / 60, 1)))
            self.close()
            self._start_listen()
        else:
            self.gateway.stop()

    @common_exception(log_flag=True)
    def close(self):
        """ 关闭连接 """
        self.ready = False
        self.logger.info('ts api close')

        if self._listen_client:
            self._listen_client.stop()
            self._listen_client = None

    def _on_listen_error(self, _, data):
        self.ready = False
        self.logger.error(f"<on_listen_error> {self.reqUserLoginId} {self._listen_key} "
                          f"{self._listen_client} {data}")
        self.gateway.send_start_unsuccessful_msg(f"on_listen_error:{json.dumps(data)}")

    def _on_listen_close(self, _):
        self.ready = False
        self.logger.warning(f"<on_listen_close> {self.reqUserLoginId} {self._listen_key} "
                            f"{self._listen_client}")
        self.gateway.on_front_disconnected("on_listen_close")

        time.sleep(10)
        if self.ready:
            return

        self._listen_client = None
        self._restart_listen()

    @common_exception(log_flag=True)
    def query_account(self):
        if not self.client:
            self.logger.warning("当前状态不能发起请求! ready:%s client:%s", self.ready, self.client)
            return
        data: dict = self.client.account(**self._get_req_data())
        # self.logger.debug("<query_account> data.keys=%s", data.keys())
        # self.account_book.update_data(data)
        self._on_assets_data(data=data.get("assets"))

        # 更新账户持仓字典 (为防止并发更新问题, 启动完成后不再全量设置持仓信息)
        if not self.ready:
            self._on_positions_data(data=data.get("positions"))

    @common_exception(log_flag=True)
    def _on_assets_data(self, data: List[dict]):
        if not data:
            return
        # 遍历集合找到指定币的资产
        for d in data:
            if self.account_book.base_instrument == d.get("asset"):
                self.logger.info("<on_assets_data> %s", d)
                self.account_book.update_data(data=d)
                return True
        return False

    @common_exception(log_flag=True)
    def _on_positions_data(self, data: List[dict]):
        if not data:
            return
        for d in data:
            if not d.get("updateTime"):
                continue
            self.logger.info("<on_positions_data> %s", d)

            position: InstrumentPosition = self.account_book.get_instrument_position(
                f"{d['symbol']}.{self.gateway.exchange_type}",
                direction=Direction.get_by_value(d.get("positionSide")))
            old_volume = position.volume
            old_cost = position.cost

            if position.update_by_datas(d):
                self.logger.info("<position update_by_datas> %s", position)
                if self.ready:
                    self._check_position_consistency(position, old_volume, old_cost)

    def _check_position_consistency(self, position, volume, cost):
        inconsistency = volume != position.volume
        # 忽略万分之二以内的价格误差
        if not inconsistency and cost != position.cost:
            inconsistency = abs(position.cost - cost) > position.cost * 0.0002
        if inconsistency:
            error_msg = f"持仓信息不一致 !!! {position.instrument} {position.direction.value} " \
                        f"volume: {volume} ~~ {position.volume} cost: {cost} ~~ {position.cost} "
            self.gateway.send_position_error_msg(instrument=position.instrument, error=error_msg)
            self.gateway.on_account_update(instruments=position.instrument)

    @common_exception(log_flag=True)
    def _on_user_data(self, _, data):
        """ 处理交易所推送的用户数据
        https://binance-docs.github.io/apidocs/futures/en/#user-data-streams
        """
        d: dict = json.loads(data)
        self.logger.info(f'<_on_user_data> {d}')
        e = d.get('e')

        if not e:
            self.ready = True
            self.logger.info(f"<on_user_data> {self.reqUserLoginId} "
                             f"listen_key={self._listen_key} {d}")

            if self.reqUserLoginId == 1:
                # 添加定时器
                self._add_restart_listen_timer()
                self.gateway.on_account_update()
            else:
                # 发送启动成功通知
                self.gateway.send_start_msg(login_reqid=self.reqUserLoginId)
            return

        func_name = f"_on_user_data_{e}"
        process_func = getattr(self, func_name)
        if process_func:
            self.logger.info(d)
            # 放入线程池处理, 防止阻塞服务器回调
            # process_func(d)
            submit(_executor=self.on_data_thread_pool, _fn=process_func, _kwargs=dict(data=d))
        else:
            self.logger.warning("Cannot process user_data !! %s", data)

    @common_exception(log_flag=True)
    def _on_user_data_ACCOUNT_UPDATE(self, data: dict):
        """
        https://binance-docs.github.io/apidocs/futures/en/#event-balance-and-position-update
        2: {'e': 'ACCOUNT_UPDATE', 'T': 1710852999872, 'E': 1710852999872, 'm': 'ORDER',
            'a': {'B': [{'a': 'USDT', 'wb': '405.37646031', 'cw': '405.37646031', 'bc': '0'}],
                  'P': [{'s': 'EOSUSDT', 'pa': '-10.6', 'ep': '0.935', 'cr': '0', 'up': '-0.00619877',
                         'mt': 'cross', 'iw': '0', 'ps': 'SHORT', 'ma': 'USDT', 'bep': '0.9345325'}]}}
        """
        a = data.get("a")
        if a:
            # 更新账户资金
            for B in a.get("B", []):
                if self.account_book.base_instrument == B['a']:
                    self.account_book.balance = type_util.get_precision_number(
                        B.get("wb"), precision=8, default=0)
                    # self.account_book.avail += type_util.get_precision_number(
                    #     B.get("bc"), precision=LocalConfig.avail_precision, default=0)
                    self.gateway.on_account_update()
                    break

            # 更新账户持仓
            for P in a.get("P", []):
                direction = Direction.get_by_value(P['ps'])
                if direction:
                    position: InstrumentPosition = self.account_book.get_instrument_position(
                        f"{P['s']}.{self.gateway.exchange_type}", direction=direction)

                    # 为防止重复更新问题, 启动完成后不再全量设置持仓信息
                    if not self.ready:
                        position.volume = abs(type_util.get_precision_number(
                            P.get("pa", 0), precision=8))
                        position.open_avg = type_util.get_precision_number(
                            P.get("ep"), precision=8, default=0)
                        position.cost = type_util.get_precision_number(
                            P.get("bep"), precision=8, default=0)

                    position.cum_pnl = type_util.get_precision_number(
                        P.get("cr"), precision=8, default=0)
                    position.pnl = type_util.get_precision_number(
                        P.get("up"), precision=8, default=0)
                    position.isolated_wallet = type_util.get_precision_number(
                        P.get("iw"), precision=8, default=0)

                    position.update_margin_type(P.get("mt"))
                    self.logger.info("<position> %s P=%s", position, P)

    @common_exception(log_flag=True)
    def _on_user_data_ORDER_TRADE_UPDATE(self, data: dict):
        o = data.get("o")
        if o:
            order_id = o["c"]
            rtn_order: RtnOrder = self.rtn_order_map.get(order_id)
            if rtn_order:
                # 系统内的交易, 更新委托回报对象
                rtn_order.update_by_rtn_data(data=o)
            else:
                # 系统外的交易, 创建委托回报对象
                rtn_order = RtnOrder.create_by_outside_rtn_data(
                    self._updates_rtn_data(data=o, instrument=o["s"]))
                self.rtn_order_map[order_id] = rtn_order
                self.logger.info("<outside_rtn_order> %s", rtn_order)

            if o.get("t"):
                # 创建成交回报对象
                rtn_trade = RtnTrade.create_by_rtn_data(data=o, rtn_order=rtn_order)

                # 计算持仓信息
                position = self.account_book.update_by_trade_rtn(rtn_trade)
                self.logger.info("<position> %s", position)
                self.gateway.on_trade(rtn_trade)

            self.gateway.on_order(rtn_order)

            if rtn_order.order_status.is_completed():
                self.rtn_order_map.pop(order_id)
                if self.cancel_order_map.__contains__(order_id):
                    self.cancel_order_map.pop(order_id)

    def _on_user_data_listenKeyExpired(self, data: dict):
        """
        {"e": "listenKeyExpired",   // event type
         "E": "1699596037418",      // event time
         "listenKey": "OfYGbUzi3PraNagEkdKuFwUHn48brFsItTdsuiIXrucEvD0rhRXZ7I6URWfE8YE8"}
        """
        self.ready = False
        self._listen_key = None
        self.gateway.on_front_disconnected(data["e"])
        self._restart_listen()

    def _on_user_data_MARGIN_CALL(self, data: dict):
        """
        https://binance-docs.github.io/apidocs/futures/en/#event-margin-call
        {'e': 'MARGIN_CALL', 'E': 1711467398581,
         'p': [{'s': 'BTCUSDT', 'ps': 'SHORT', 'pa': '-0.002', 'mt': 'ISOLATED',
                'iw': '1.3289702', 'mp': '70260.8', 'up': '-0.63', 'mm': '0.562086'}]}
        """
        pass

    def _get_req_data(self, **kwargs) -> dict:
        """
        签名接口均需要传递timestamp参数, 其值应当是请求发送时刻的unix时间戳（毫秒）
        服务器收到请求时会判断请求中的时间戳，如果是5000毫秒之前发出的，则请求会被认为无效。这个时间窗口值可以通过发送可选参数recvWindow来自定义
        如果服务器计算得出客户端时间戳在服务器时间的‘未来’一秒以上，也会拒绝请求
        """
        recvWindow = self.configs.get("recvWindow")
        if recvWindow:
            kwargs.setdefault("recvWindow", recvWindow)
        return kwargs

    def _gen_order_id(self, max_ref_id_len=6) -> str:
        self.order_ref_id += 1
        return f"{str(self.order_ref_id).zfill(max_ref_id_len)}"

    def insert_order(self, instrument: str, offset_flag: OffsetFlag, direction: Direction,
                     order_price_type: OrderPriceType, price: float, volume: float,
                     cancel_delay_seconds: int = 0, **kwargs) -> str:
        """
        做多开仓=OPEN:LONG    做空开仓=OPEN:SHORT
        做多平仓=CLOSE:LONG   做空平仓=CLOSE:SHORT
        """
        if not self.ready:
            self.logger.warning("当前状态不能发起请求! ready:%s", self.ready)
            return self.gateway.gen_error_order_id(err_msg="NOT_READY")

        # # 防止启动后还有未撤销的挂单
        # if not self.ready_instruments.__contains__(instrument):
        #     self.cancel_order(instrument=instrument)
        #     self.ready_instruments.add(instrument)

        # 生成订单号
        client_order_id: str = self._gen_order_id()

        # 放入单例线程池执行以保持数据流顺序
        submit(_executor=self.on_data_thread_pool, _fn=self._new_order,
               _kwargs=dict(instrument=instrument, offset_flag=offset_flag, direction=direction,
                            order_price_type=order_price_type, price=price, volume=volume,
                            cancel_delay_seconds=cancel_delay_seconds,
                            client_order_id=client_order_id))
        return client_order_id

    def _new_order(self, instrument: str, offset_flag: OffsetFlag, direction: Direction,
                   order_price_type: OrderPriceType, price: float, volume: float,
                   client_order_id: str, cancel_delay_seconds: int = 0, **kwargs):
        offset_flag: OffsetFlag = OffsetFlag.OPEN \
            if OffsetFlag.is_open_by_name(offset_flag, direction) else OffsetFlag.CLOSE
        side, positionSide = DIRECTION_2VT[(offset_flag, direction)]

        req: dict = self._get_req_data(
            symbol=instrument, newClientOrderId=client_order_id, newOrderRespType="RESULT",
            side=side, positionSide=positionSide
        )

        if OrderPriceType.MARKET == order_price_type:
            req.update({
                'type': 'MARKET',
                'quantity': str(volume),
            })
        elif OrderPriceType.FAK == order_price_type:
            req.update({
                'type': 'LIMIT', 'timeInForce': "IOC",
                'quantity': str(volume), 'price': str(price),
            })
        elif OrderPriceType.FOK == order_price_type:
            req.update({
                'type': 'LIMIT', 'timeInForce': "FOK",
                'quantity': str(volume), 'price': str(price),
            })
        elif OrderPriceType.LIMIT == order_price_type:
            req.update({
                'type': 'LIMIT', 'timeInForce': "GTC",
                'quantity': str(volume), 'price': str(price),
            })
        else:
            return self.gateway.gen_error_order_id(
                err_msg=f"INVALID_ORDER_PRICE_TYPE:{order_price_type}")

        self.logger.info(f"<new_order> req={req} {offset_flag} {direction} "
                         f"{order_price_type} {cancel_delay_seconds} {price} {volume}")

        req_data: dict = req.copy()
        req_data.setdefault('price', price)
        req_data.setdefault('order_price_type', order_price_type)
        req_data.setdefault('cancel_delay_seconds', cancel_delay_seconds)
        rtn_order = RtnOrder.create_by_insert_req(
            self._updates_rtn_data(data=req_data, instrument=instrument))
        self.rtn_order_map[client_order_id] = rtn_order

        try:
            result: dict = self.client.new_order(**req)
            self.logger.info(f"<new_order> result={result}")

            # rtn_order.update_by_insert_result(data=result)
        except ClientError as e:
            self.logger.exception("!!! new_order error:%s !!!", e)

    def _updates_rtn_data(self, data: dict, instrument: str = None):
        data["trading_day"] = self.trading_day
        # data["instrument_category"] = self.gateway.instrument_category
        # data["source_id"] = self.gateway.source_type
        # data["exchange_type"] = self.gateway.exchange_type
        # data["account_id"] = self.gateway.account_id
        # if instrument:
        #     instrument_book: InstrumentBook = self.account_book.get_instrument_book(
        #         f"{instrument}.{self.gateway.exchange_type}")
        #     data["instrument_type"] = instrument_book.instrument_type
        return data

    def cancel_all_order(self, instrument):
        submit(_executor=self.on_data_thread_pool, _fn=self._cancel_all_order,
               _kwargs=dict(instrument=instrument))

    def _cancel_all_order(self, instrument):
        result: List[dict] = self.client.cancel_open_orders(instrument)
        self.logger.info(f"<cancel_open_orders> result={result}")

    def _add_restart_listen_timer(self, interval: float = 60 * 60 - 0.5):
        def _check():
            self._restart_listen()
            self._add_restart_listen_timer(interval)

        AioTimer.new_timer(_delay=interval, _func=_check)

    def _add_query_account_timer(self, interval):
        def _func():
            self._add_query_account_timer(interval)

            if self.ready:
                self.query_account()

            self._check_listen_ping()

        AioTimer.new_timer(_delay=interval, _func=_func)

    @property
    def logger(self):
        return self.gateway.logger

    def getTradingDay(self):
        return datetime.now().strftime('%Y%m%d')

    @property
    def trading_day(self):
        return self.getTradingDay()
