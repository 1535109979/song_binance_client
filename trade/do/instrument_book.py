from dataclasses import dataclass, field
from typing import List

from song_binance_client.utils import type_util
from song_binance_client.utils.exchange_enum import ExchangeType


@dataclass
class InstrumentBook:
    vt_symbol: str = None

    # 标的代码
    instrument: str = None
    # 交易所
    exchange_type: ExchangeType = None

    instrument_type: str = None
    instrument_cn: str = None
    # product_class: ProductClass = None

    # 最小报单价格跳动 price_tick
    min_price_step: str = "1"
    # 报单数量步进
    min_volume_step: str = "1"
    # 报单金额步进
    min_qty_volume_step: str = "1"

    # 最小报单数量
    min_volume_value: float = 1
    # 最大报单数量
    max_volume_value: float = 0
    # 最小报单金额
    min_qty_volume_value: float = 0
    # 最大持仓数量
    max_pos_volume_value: float = 0

    # 手续费 rate
    commission_rate: float = 0
    # 合约乘数 size
    contract_multiplier: int = 1
    # 保证金率
    long_margin_ratio: float = 1
    short_margin_ratio: float = 1

    # 当前合约的本位币
    base_instrument: str = field(default="USDT")

    # 当前合约状态
    status: str = field(default="TRADING")

    # 当前合约支持的最大倍数
    max_leverage: int = 1

    # 当前账号使用的杠杆倍数
    use_leverage: int = 1

    # { 杠杆倍数: 杠杆属性 }
    leverages_data: dict = field(default_factory=dict)

    def __post_init__(self):
        assert self.vt_symbol or (self.instrument and self.exchange_type)

        if self.vt_symbol:
            self.instrument, self.exchange_type = self.vt_symbol.split(".")
        else:
            self.vt_symbol = f"{self.instrument}.{str(self.exchange_type)}"

        self.exchange_type = ExchangeType.get_by_value(self.exchange_type)

        # if not self.product_class:
        #     self.product_class = ProductClass.F

        if not self.instrument_type:
            self.instrument_type = self.get_instrument_type()

        # if not self.instrument_cn:
        #     self.instrument_cn = ExchangeTimeConfig.get_instrument_type_cn(
        #         instrument_type=self.instrument_type) or self.instrument

    def get_instrument_type(self) -> str:
        return self.instrument[:-len(self.base_instrument)]

    def get_margin_ratio(self, leverage: int = None, **kwargs) -> float:
        if not leverage:
            leverage = self.use_leverage
        return 1 / leverage

    def update_data(self, data):
        self.status = data.get("status") or "TRADING"
        self.base_instrument = data.get("quoteAsset") or "USDT"

        self.instrument_type = data.get("baseAsset") or self.get_instrument_type()
        # self.product_class = ProductClass.get_by_value(
        #     data.get("product_class")) or self.product_class

        self.commission_rate: float = type_util.convert_to_float(
            value=data.get("liquidationFee"), default_value=0.00075)

        self.long_margin_ratio: float = self.get_margin_ratio()
        self.short_margin_ratio: float = self.long_margin_ratio

        self.min_price_step: str = "0.001"
        self.min_volume_step: str = "0.001"
        self.min_volume_value: float = 0.001
        self.max_volume_value: float = 0
        self.min_qty_volume_step: str = "1"
        self.min_qty_volume_value: float = 10
        self.max_pos_volume_value: float = 0

        filters_data: List[dict] = data.get("filters", [])
        for d in filters_data:
            filterType = d["filterType"]
            if "PRICE_FILTER" == filterType:
                self.min_price_step = type_util.convert_decimal_exp_str(
                    value=float(d.get("tickSize")), default_value=self.min_price_step)
                # self.min_price = type_util.convert_to_float(d.get("minPrice"))
                # self.max_price = type_util.convert_to_float(d.get("maxPrice"))
            elif "LOT_SIZE" == filterType:
                self.min_volume_step = type_util.convert_decimal_exp_str(
                    value=float(d.get("stepSize")), default_value=self.min_volume_step)
                self.min_volume_value = type_util.convert_to_float(
                    value=d.get("minQty"), default_value=self.min_volume_value)
                self.max_volume_value = type_util.convert_to_float(
                    value=d.get("maxQty"), default_value=self.max_volume_value)
            elif "MARKET_LOT_SIZE" == filterType:
                self.min_qty_volume_step = type_util.convert_decimal_exp_str(
                    value=float(d.get("stepSize")), default_value=self.min_qty_volume_step)
            elif "MIN_NOTIONAL" == filterType:
                self.min_qty_volume_value = type_util.convert_to_float(
                    value=d.get("notional"), default_value=self.min_qty_volume_value)
            elif "MAX_POSITION" == filterType:
                self.max_pos_volume_value = type_util.convert_to_float(
                    value=d.get("maxPosition"), default_value=self.max_pos_volume_value)
        return self
