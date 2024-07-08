import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple, Dict

from a_songbo.binance_client.utils import type_util
from a_songbo.binance_client.utils.exchange_enum import SourceType, ExchangeType, InstrumentCategory, OrderStatus, \
    OffsetFlag, Direction
from a_songbo.binance_client.utils.id_gen import UlIdGenerator

# 多空和开平方向映射
DIRECTION_2VT = {
    (OffsetFlag.OPEN, Direction.LONG): ('BUY', 'LONG'),     # 开多
    (OffsetFlag.CLOSE, Direction.LONG): ('SELL', 'LONG'),   # 平多
    (OffsetFlag.OPEN, Direction.SHORT): ('SELL', 'SHORT'),  # 开空
    (OffsetFlag.CLOSE, Direction.SHORT): ('BUY', 'SHORT'),  # 平空
}
VT_2DIRECTION: Dict[tuple, tuple] = {v: k for k, v in DIRECTION_2VT.items()}


@dataclass
class RtnOrder:

    data: dict = field(default_factory=dict)

    @classmethod
    def convert_order_status(cls, status) -> OrderStatus:
        """ 转换报单状态
        NEW 新建订单
        PARTIALLY_FILLED 部分成交
        FILLED 全部成交
        CANCELED 已撤销
        PENDING_CANCEL 正在撤销中(目前不会遇到这个状态)
        REJECTED 订单被拒绝
        EXPIRED 订单过期(根据timeInForce参数规则)
        """
        if "FILLED" == status:
            return OrderStatus.ALL_TRADED
        if "CANCELED" == status:
            return OrderStatus.PART_TRADED
        if "EXPIRED" == status:
            return OrderStatus.NO_TRADE
        if "REJECTED" == status:
            return OrderStatus.ERROR
        return OrderStatus.UNKNOWN

    def __post_init__(self):
        self.data.setdefault("order_ref_id", 0)
        self.data.setdefault("parent_order_id", 0)

        self.data.setdefault("volume_traded", 0)
        self.data.setdefault("avg_price", self.limit_price)
        self.data.setdefault("turnover", type_util.get_precision_number(
            self.volume_traded * self.avg_price, precision=8))

        self.data.setdefault("update_time", self.insert_time)
        self.data.setdefault("trading_day", datetime.fromtimestamp(self.insert_time / 1000000000).strftime('%Y%m%d'))

        self.data.setdefault("error_id", 0)
        self.data.setdefault("error_msg", "")

        self.data.setdefault("order_status", OrderStatus.UNKNOWN)
        self.adjust_completed_order_status()

    def update_data(self, data: dict):
        self.data.update(data)
        self.__post_init__()

    @classmethod
    def convert_offset_side(cls, offset, side) -> Tuple[OffsetFlag, Direction]:
        return VT_2DIRECTION.get((offset, side))

    @classmethod
    def create_by_insert_req(cls, data: dict):
        offset_flag, direction = cls.convert_offset_side(
            offset=data["side"], side=data["positionSide"])
        status = data.get("status", "NEW")

        return cls(data=dict(
            order_id=data["newClientOrderId"],
            order_ref_id=data.get("orderId"),
            client_id=data.get("front_id", 0),
            account_id=data.get("account_id", ""),
            source_id=data.get("source_id", SourceType.BIAN_FUTURES),
            exchange_type=data.get("exchange_type", ExchangeType.BINANCE_F),
            instrument_category=data.get("instrument_category", InstrumentCategory.DIGICCY_FUTURES),
            instrument_type=data.get("instrument_type", ""),
            instrument=data["symbol"],
            status=status,
            order_status=cls.convert_order_status(status),
            volume=type_util.convert_to_float(data["quantity"]),
            volume_traded=0,
            volume_condition=data.get("reduceOnly"),
            time_condition=data.get("timeInForce", ""),
            limit_price=type_util.convert_to_float(data["price"]),
            avg_price=0,
            price_type=data['type'],
            offset=offset_flag,
            side=direction,
            hedge_flag=data.get("workingType"),
            trading_day=data["trading_day"],
            insert_time=int(time.time() * 1000000),
            cancel_delay_seconds=data.get("cancel_delay_seconds", 0),
        ))

    def update_by_rtn_data(self, data: dict):
        status = data.get("X", "NEW")

        volume_traded = type_util.convert_to_float(data["z"])
        avg_price = type_util.convert_to_float(data["ap"])
        turnover: float = type_util.get_precision_number(
            number=volume_traded * avg_price, precision=8)

        self.update_data(data=dict(
            order_ref_id=data.get("i"),
            update_time=data["T"] * 1000000,
            turnover=turnover,
            avg_price=avg_price,
            volume_traded=volume_traded,
            status=status,
            order_status=self.convert_order_status(status),
            commission=type_util.convert_to_float(data.get("n", 0)),
            commission_asset=data.get("N")))

    @classmethod
    def create_by_outside_rtn_data(cls, data):
        """
        {'s': 'BTCUSDT', 'c': 'autoclose-1711436538316664001', 'S': 'BUY', 'o': 'LIQUIDATION',
         'f': 'IOC', 'q': '0.002', 'p': '71045.51', 'ap': '0', 'sp': '0', 'x': 'NEW', 'X': 'NEW',
         'i': 296583397750, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT',
         'T': 1711436538340, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': False,
         'wt': 'CONTRACT_PRICE', 'ot': 'LIQUIDATION', 'ps': 'SHORT', 'cp': False, 'rp': '0',
         'pP': False, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}
        {'s': 'BTCUSDT', 'c': 'autoclose-1711436538316664001', 'S': 'BUY', 'o': 'LIQUIDATION',
         'f': 'IOC', 'q': '0.002', 'p': '71045.51', 'ap': '70814.10000', 'sp': '0',
         'x': 'TRADE', 'X': 'FILLED', 'i': 296583397750, 'l': '0.002', 'z': '0.002',
         'L': '70814.10', 'n': '0', 'N': 'USDT', 'T': 1711436538340, 't': 4800477277, 'b': '0',
         'a': '0', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIQUIDATION',
         'ps': 'SHORT', 'cp': False, 'rp': '-0.90020000', 'pP': False, 'si': 0, 'ss': 0,
         'V': 'NONE', 'pm': 'NONE', 'gtd': 0}
        """
        offset_flag, direction = RtnOrder.convert_offset_side(
            offset=data["S"], side=data["ps"])
        status = data.get("X", "NEW")

        volume_traded = type_util.convert_to_float(data["z"])
        avg_price = type_util.convert_to_float(data["ap"])
        turnover: float = type_util.get_precision_number(
            number=volume_traded * avg_price, precision=8)

        return cls(data=dict(
            order_id=data["c"],
            order_ref_id=data["i"],
            client_id="OUTSIDE",
            account_id=data.get("account_id", ""),
            source_id=data.get("ot", SourceType.BIAN_FUTURES),
            exchange_type=data.get("exchange_type", ExchangeType.BINANCE_F),
            instrument_category=data.get("instrument_category", InstrumentCategory.DIGICCY_FUTURES),
            instrument_type=data.get("instrument_type", ""),
            instrument=data["s"],
            status=status,
            order_status=cls.convert_order_status(status),
            volume=type_util.convert_to_float(data["q"]),
            volume_traded=volume_traded,
            volume_condition=data["R"],
            time_condition=data["f"],
            limit_price=type_util.convert_to_float(data["p"]),
            avg_price=avg_price,
            turnover=turnover,
            price_type=data.get("ot", "MARKET"),
            offset=offset_flag,
            side=direction,
            hedge_flag=data.get("wt"),
            trading_day=data.get("trading_day"),
            insert_time=data["T"] * 1000000,
            commission=type_util.convert_to_float(data.get("n", 0)),
            commission_asset=data.get("N"),
        ))


    def adjust_completed_order_status(self) -> OrderStatus:
        """ 根据成交数量判断实际状态 """
        order_status: OrderStatus = self.order_status

        if not OrderStatus.is_equals(OrderStatus.UNKNOWN, order_status):
            if self.volume_traded > 0:
                order_status = OrderStatus.ALL_TRADED if self.volume_traded >= self.volume \
                    else OrderStatus.PART_TRADED
            else:
                order_status = OrderStatus.ERROR if int(self.error_id) \
                    else OrderStatus.NO_TRADE
            self.data["order_status"] = order_status

        return order_status

    @property
    def error_id(self):
        return self.data.get("error_id", 0)

    @property
    def volume(self) -> float:
        """ 委托数量 """
        return type_util.convert_to_float(self.data["volume"])

    @property
    def status(self):
        return self.data["status"]

    @property
    def order_status(self) -> OrderStatus:
        order_status = OrderStatus.get_by_value(self.data.get("order_status"))
        if not order_status:
            order_status = self.order_status = self.convert_order_status(status=self.status)
        return order_status

    @order_status.setter
    def order_status(self, order_status: OrderStatus):
        self.data["order_status"] = OrderStatus.get_by_value(order_status)
        self.adjust_completed_order_status()

    @property
    def limit_price(self) -> float:
        """ 委托价 """
        return type_util.convert_to_float(self.data["limit_price"])

    @property
    def insert_time(self):
        return type_util.convert_to_float(self.data["insert_time"])

    @property
    def avg_price(self) -> float:
        """ 实际成交均价 """
        return type_util.convert_to_float(self.data.get("avg_price", 0))

    @avg_price.setter
    def avg_price(self, avg_price: float):
        self.data["avg_price"] = avg_price
        self.turnover = type_util.get_precision_number(
            self.volume_traded * self.avg_price, precision=8)

    @property
    def volume_traded(self) -> float:
        """ 实际成交数量 """
        return type_util.convert_to_float(self.data["volume_traded"])

    @volume_traded.setter
    def volume_traded(self, volume_traded):
        self.data["volume_traded"] = volume_traded
        self.turnover = type_util.get_precision_number(
            self.volume_traded * self.avg_price, precision=8)

    @property
    def turnover(self):
        return type_util.convert_to_float(self.data["turnover"])

    @turnover.setter
    def turnover(self, turnover):
        self.data["turnover"] = type_util.get_precision_number(
            number=turnover, precision=8)

    @property
    def id(self):
        return self.data.get("order_id")

    @property
    def trading_day(self):
        return self.data.get("trading_day")

    @property
    def hedge_flag(self):
        return self.data.get("hedge_flag", 0)

    @property
    def order_id(self):
        return self.data["order_id"]

    @property
    def order_ref_id(self):
        return self.data.get("order_ref_id", 0)

    @property
    def parent_order_id(self):
        return self.data.get("parent_order_id", 0)

    @property
    def client_id(self):
        return self.data.get("client_id", 0)

    @property
    def source_type(self):
        return self.data.get("source_id")

    @property
    def account_id(self):
        return self.data["account_id"]

    @property
    def exchange_type(self):
        return ExchangeType.get_by_value(self.data["exchange_type"])

    @property
    def instrument_category(self):
        return self.data["instrument_category"]

    @property
    def instrument_type(self):
        return self.data["instrument_type"]

    @property
    def instrument(self):
        return self.data["instrument"]

    @property
    def offset_flag(self) -> OffsetFlag:
        return OffsetFlag.get_by_value(self.data["offset"])

    @property
    def direction(self) -> Direction:
        return Direction.get_by_value(self.data["side"])


if __name__ == '__main__':
    pass

