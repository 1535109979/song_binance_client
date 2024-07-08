from dataclasses import dataclass, field

from a_songbo.binance_client.trade.do.rtn_trade import RtnTrade
from a_songbo.binance_client.utils import type_util
from a_songbo.binance_client.utils.exchange_enum import Direction, MarginType, OffsetFlag


@dataclass
class InstrumentPosition:
    instrument: str
    direction: Direction

    volume: float = 0  # 持仓数量
    cost: float = 0  # 持仓成本价
    open_avg: float = 0  # 开仓均价 (以官方开仓均价为准)
    margin: float = 0  # 占用资金 (保证金)

    pnl: float = 0

    # 当前持仓的开仓数额
    open_amount: float = 0
    # 持仓成本数额 (数量 * 价格)
    cost_amount: float = 0

    # 持仓杠杆倍数
    leverage: int = 1
    # 保证金模式 全仓:CROSSED 逐仓:ISOLATED
    margin_type: MarginType = MarginType.CROSSED

    # if ISOLATED position
    isolated_wallet: float = 0

    # 用于区分持仓对象是否只是默认创建但没有数据更新的
    default: bool = True

    # 已处理的成交id
    trade_ids: list = field(default_factory=list)

    def update_by_datas(self, data: dict) -> bool:
        if not data:
            return False
        self.default = False

        self.volume = abs(type_util.convert_to_float(data.get("positionAmt"), 0))
        self.open_avg = type_util.convert_to_float(data.get('entryPrice'), 0)
        self.cost = type_util.convert_to_float(data.get("breakEvenPrice"), 0)
        self.open_amount = self.open_avg * self.volume
        self.cost_amount = self.cost * self.volume

        self.margin = type_util.convert_to_float(data.get("positionInitialMargin"), 0)
        self.leverage = type_util.convert_to_int(data.get("leverage"), 1)
        self.isolated_wallet = type_util.convert_to_float(data.get("isolatedWallet"), 0)
        self.pnl = type_util.convert_to_float(data.get("unrealizedProfit"), 0)

        self.update_margin_type(data.get("isolated"))
        return True

    def update_margin_type(self, margin_type):
        if margin_type is None or margin_type is False \
                or str(margin_type).upper().startswith("CROSS"):
            self.margin_type = MarginType.CROSSED
        else:
            self.margin_type = MarginType.ISOLATED

    def update_by_trade_rtn(self, rtn: RtnTrade):
        if rtn.trade_id in self.trade_ids:
            return

        if len(self.trade_ids) > 35:
            self.trade_ids = self.trade_ids[-20:]
        self.trade_ids.append(rtn.trade_id)

        # 计算持仓数量
        offset_side: int = OffsetFlag.get_offset_side(
            offset_flag=rtn.offset_flag, direction=rtn.direction)
        self.volume = type_util.get_precision_number(
            number=self.volume + rtn.volume * offset_side, precision=8)

        if self.volume:
            # 计算开仓均价
            if OffsetFlag.is_open_by_name(rtn.offset_flag):
                self.open_amount += rtn.turnover
                self.open_avg = type_util.get_precision_number(
                    number=self.open_amount / self.volume, precision=8)

            # 计算持仓均价
            self.cost_amount += rtn.turnover * offset_side
            self.cost_amount += rtn.commission * rtn.direction.value
            self.cost = type_util.get_precision_number(
                number=self.cost_amount / self.volume, precision=8)
        else:
            self.clear_pos()

    def clear_pos(self):
        self.cost = 0
        self.open_avg = 0
        self.margin = 0
        self.open_amount = 0
        self.cost_amount = 0
        self.pnl = 0

@dataclass
class InstrumentPositionBook:
    """ 合约多空方向持仓信息 """
    vt_symbol: str

    def __post_init__(self):
        self.instrument, self.exchange = self.vt_symbol.split('.')
        self.long_position = self.create_position(direction=Direction.LONG)
        self.short_position = self.create_position(direction=Direction.SHORT)
        self.positions = {"LONG": self.long_position, "SHORT": self.short_position}

    def create_position(self, direction: Direction):
        return InstrumentPosition(instrument=self.instrument, direction=direction)

    def get_by_direction(self, direction: Direction) -> InstrumentPosition:
        """ 获取指定方向的持仓信息对象 """
        if Direction.is_equals(Direction.SHORT, direction):
            return self.short_position
        else:
            return self.long_position

