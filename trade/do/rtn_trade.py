from dataclasses import dataclass, field

from a_songbo.binance_client.trade.do.rtn_order import RtnOrder
from a_songbo.binance_client.utils import type_util
from a_songbo.binance_client.utils.exchange_enum import OffsetFlag, Direction, ExchangeType


@dataclass
class RtnTrade:
    data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.data.setdefault("id", self.data.get('trade_id'))
        self.data.setdefault("close_today_volume", 0)
        self.data.setdefault("turnover", type_util.get_precision_number(
            self.volume * self.price, precision=8))

    @classmethod
    def create_by_rtn_data(cls, data: dict, rtn_order: RtnOrder):
        return cls(data=dict(
            trade_id=data["t"],
            order_id=rtn_order.order_id,
            order_ref_id=rtn_order.order_ref_id,
            parent_order_id=rtn_order.parent_order_id,
            client_id=rtn_order.client_id,
            source_id=rtn_order.source_type,
            account_id=rtn_order.account_id,
            exchange_type=rtn_order.exchange_type,
            instrument_category=rtn_order.instrument_category,
            instrument_type=rtn_order.instrument_type,
            instrument=rtn_order.instrument,
            offset=rtn_order.offset_flag,
            side=rtn_order.direction,
            hedge_flag=rtn_order.hedge_flag,
            volume=type_util.convert_to_float(data["l"]),
            price=type_util.convert_to_float(data["L"]),
            profit=type_util.convert_to_float(data.get("rp", 0)),  # 盈利金额
            margin=type_util.convert_to_float(data.get("a", 0)),  # 受影响的保证金金额
            trading_day=rtn_order.trading_day,
            trade_time=data['T'] * 1000000,
            commission=type_util.convert_to_float(data.get("n", 0)),
            commission_asset=data.get("N"),
        ))

    @property
    def volume(self) -> float:
        return type_util.convert_to_float(self.data["volume"])

    @property
    def price(self) -> float:
        return type_util.convert_to_float(self.data["price"])

    @property
    def parent_order_id(self):
        return self.data.get("parent_order_id", 0)

    @property
    def client_id(self):
        return self.data.get("client_id", 0)

    @property
    def profit(self):
        return self.data.get("profit", 0)

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
    def trade_time(self):
        return type_util.convert_to_int(self.data["trade_time"])

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

    @property
    def trading_day(self):
        return self.data.get("trading_day")

    @property
    def hedge_flag(self):
        return self.data.get("hedge_flag", 0)

    @property
    def margin(self):
        return type_util.convert_to_float(self.data.get("margin"), default_value=0)

    @property
    def trade_id(self):
        return self.data["trade_id"]

    @property
    def turnover(self):
        return type_util.convert_to_float(self.data["turnover"])

    @property
    def commission(self):
        return type_util.convert_to_float(self.data.get("commission"), default_value=0)

