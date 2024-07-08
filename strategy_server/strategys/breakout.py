from a_songbo.binance_client.trade.do.position import InstrumentPosition
from a_songbo.binance_client.utils.exchange_enum import Direction, OffsetFlag, OrderPriceType
from decimal import Decimal


class BreakoutStrategy:
    def __init__(self, strategy_process, params):
        self.strategy_process = strategy_process

        self.open_direction = Direction.LONG
        self.windows = params['windows']
        self.open_volume = params['open_volume']
        self.interval_period = params['interval_period']
        self.roll_mean_period = params['roll_mean_period']

        self.am = []
        self.roll_mean_list = []
        self.last_n_min = self.last_n_max = None

        self.trade_first = True

    def cal_indicator(self, quote):
        if not quote.get('is_closed', 0):
            return

        last_price = quote['last_price']

        if len(self.am) < self.windows:
            self.am.append(last_price)
            if len(self.am) >= self.roll_mean_period:
                roll_mean = round(sum(self.am[-self.roll_mean_period:]) / self.roll_mean_period, 8)
                self.roll_mean_list.append(roll_mean)
            return

        self.am = self.am[-self.roll_mean_period * 2:]
        self.last_n_max = max(self.am[-self.windows:])
        self.last_n_min = min(self.am[-self.windows:])

        self.am.append(last_price)
        roll_mean = round(sum(self.am[-self.roll_mean_period:]) / self.roll_mean_period, 8)
        self.roll_mean_list.append(roll_mean)
        if len(self.roll_mean_list) > self.interval_period * 2:
            self.roll_mean_list = self.roll_mean_list[-self.interval_period * 2:]

    def cal_singal(self, quote):
        # 止损后 清空am 隔段时间再交易
        if self.strategy_process.stop_loss_flag:
            self.am = []
            self.strategy_process.logger.info('<cal_singal> after stop_loss clear am')
            self.strategy_process.stop_loss_flag = False

        if not quote.get('is_closed', 0):
            return

        last_price = quote['last_price']
        instrument = quote['symbol']

        if not self.last_n_min:
            return

        # 开仓方向
        open_direction = None
        if last_price < self.last_n_min:
            open_direction = self.open_direction
        elif last_price > self.last_n_max:
            open_direction = self.open_direction.get_opposite_direction()

        if not open_direction:
            return

        self.strategy_process.logger.info(f"<cal_singal>am={len(self.am)} l={last_price} min={self.last_n_min} "
                                 f"max={self.last_n_max} open_direction={open_direction} "
                                 )

        direction_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', open_direction)
        opposite_direction_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', open_direction.get_opposite_direction())

        self.strategy_process.logger.info(f'direction_position={direction_position}')
        self.strategy_process.logger.info(f'opposite_direction_position={opposite_direction_position}')

        if direction_position.volume:
            return
        else:
            if self.trade_first:
                if open_direction == Direction.LONG:
                    if last_price > self.roll_mean_list[-self.interval_period] > self.roll_mean_list[-self.interval_period * 2]:
                        return

                    trade_price = Decimal(last_price) + Decimal('0.001')
                else:
                    if last_price < self.roll_mean_list[-self.interval_period] < self.roll_mean_list[-self.interval_period * 2]:
                        return
                    trade_price = Decimal(last_price) - Decimal('0.001')
            else:
                trade_price = last_price

            self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.OPEN, open_direction,
                                         OrderPriceType.LIMIT, str(trade_price), self.open_volume)

            if opposite_direction_position.volume:
                self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.CLOSE, open_direction.get_opposite_direction(),
                                             OrderPriceType.LIMIT, str(trade_price), opposite_direction_position.volume)


