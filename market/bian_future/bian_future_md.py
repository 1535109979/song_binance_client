import traceback
from typing import Optional
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient
import json
import time

from binance.websocket.websocket_client import BinanceWebsocketClient

from a_songbo.binance_client.utils.aio_timer import AioTimer
from a_songbo.binance_client.utils.sys_exception import common_exception


class BiFutureMd:
    def __init__(self, gateway):
        self.gateway = gateway
        # 获取柜台配置
        self.configs: dict = gateway.get_api_configs()

        self.client: Optional[UMFuturesWebsocketClient] = None

        # 当前进程登录次数
        self.reqUserLoginId = 0

        self.sub_instrument = []

        self.md_time_flag = 0
        self._add_check_md_timer(120)

    def _add_check_md_timer(self, interval):
        def _func():
            self._add_check_md_timer(interval)
            self._check_md_time_flag()

        AioTimer.new_timer(_delay=interval, _func=_func)

    @common_exception(log_flag=True)
    def _check_md_time_flag(self):
        ts = time.time() - self.md_time_flag
        self.logger.info(f'<_check_md_time_flag> ts={ts}')
        if not self.md_time_flag or ts < 60 * 6:
            return

        self.logger.warning("!! _check_md_time_flag !! %s", ts)

        if 60 * 5 < ts < 30 * 5:
            self.gateway.on_front_disconnected(
                "连续{}分钟没有收到行情".format(round(ts / 60, 1)))
            self._reconnect()

    @property
    def logger(self):
        return self.gateway.logger

    def connect(self):
        if self.client:
            self.logger.info("服务已连接.")
            return

        self.reqUserLoginId += 1
        self.client = UMFuturesWebsocketClient(
            stream_url=self.configs.get("stream_url"),
            is_combined=self.configs.get("is_combined", False),
            on_open=self._on_open,
            on_close=self._on_close,
            on_error=self._on_error,
            on_message=self._on_message)

        self.logger.info("<create_client> %s %s %s", self.reqUserLoginId, self.client, self.configs)

    def _reconnect(self):
        self.logger.info("<reconnect> %s %s", self.reqUserLoginId, self.client)
        time.sleep(5)
        self.client = None
        self.connect()
        self._resubscribe()

    def _resubscribe(self):
        self.logger.info(f"<_resubscribe> {self.sub_instrument}")
        if self.sub_instrument:
            for i in self.sub_instrument:
                self.subscribe(i)
                time.sleep(0.5)

    def _on_open(self, _):
        self.logger.info("<on_open> %s %s", self.reqUserLoginId, _)

    def _on_close(self, _):
        self.logger.info("<on_close> %s %s", self.reqUserLoginId, _)
        self.gateway.on_front_disconnected("on_client_close")
        self._reconnect()

    def _on_error(self, _, data):
        self.logger.error("<on_error> %s %s %s", self.reqUserLoginId, _, data)
        self.gateway.on_error(data)

    def _on_message(self, _, data):
        data = json.loads(data)

        if 'kline' == data.get('e'):
            self._on_kline_data(data)

    def _on_kline_data(self, data: dict):
        """ 收到行情
        {
          "e": "kline",     // Event type
          "E": 1638747660000,   // Event time
          "s": "BTCUSDT",    // Symbol
          "k": {
            "t": 1638747660000, // Kline start time
            "T": 1638747719999, // Kline close time
            "s": "BTCUSDT",  // Symbol
            "i": "1m",      // Interval
            "f": 100,       // First trade ID
            "L": 200,       // Last trade ID
            "o": "0.0010",  // Open price
            "c": "0.0020",  // Close price
            "h": "0.0025",  // High price
            "l": "0.0015",  // Low price
            "v": "1000",    // Base asset volume
            "n": 100,       // Number of trades
            "x": false,     // Is this kline closed?
            "q": "1.0000",  // Quote asset volume
            "V": "500",     // Taker buy base asset volume
            "Q": "0.500",   // Taker buy quote asset volume
            "B": "123456"   // Ignore
          }
        }
        """
        self.md_time_flag = time.time()

        k = data['k']
        if not k or k.get('f', 0) <= 0:
            return

        try:
            self.gateway.on_quote(quote={
                "id": int(data["E"]), "localtime": data["E"],
                "symbol": data["s"], "name": k["s"],
                "open_price": k['o'],
                "high_price": k['h'],
                "low_price": k['l'],
                "last_price": k['c'],
                "volume": k['v'],
                "turnover": k['q'],
                "is_closed": 1 if k['x'] else 0,
            })
        except Exception as e:
            traceback.print_exc()
            self.logger.error("<on_message> %s data: %s", e, data)

    def subscribe(self, instrument: list, interval="1m"):
        """ 订阅行情 """
        if not self.client:
            self.logger.error("!!! cannot subscribe !!! client=%s", self.client)
            return False

        for symbol in instrument:
            self.client.kline(symbol=symbol, interval=interval)
            self.logger.info("<subscribe_kline> %s %s", interval, symbol)
            self.sub_instrument.append(symbol)
            # 订阅过快会导致连接被服务端断开
            time.sleep(0.5)
        return True

    def unsubscribe(self, instrument, interval="1m"):
        """ 取消订阅行情 """
        if not self.client:
            self.logger.error("!!! cannot unsubscribe !!! client=%s", self.client)
            return False

        for symbol in instrument:
            self.client.kline(symbol=symbol, interval=interval,
                              action=BinanceWebsocketClient.ACTION_UNSUBSCRIBE)
            self.logger.info("<unsubscribe_kline> %s %s", interval, symbol)
            time.sleep(0.5)
        return True
