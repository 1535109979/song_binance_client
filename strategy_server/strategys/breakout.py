import numpy

from song_binance_client.trade.do.position import InstrumentPosition
from song_binance_client.utils.exchange_enum import Direction, OffsetFlag, OrderPriceType
from decimal import Decimal

from song_binance_client.utils.sys_exception import common_exception


class BreakoutStrategy:
    def __init__(self, strategy_process, params):
        self.strategy_process = strategy_process
        self.logger = self.strategy_process.logger

        self.params = params
        self.open_direction = Direction.LONG
        self.windows = params['windows']
        self.open_volume = params['open_volume']
        self.interval_period = params['interval_period']
        self.roll_mean_period = params['roll_mean_period']
        self.min_save_window = max(self.windows, self.interval_period * 2 + self.roll_mean_period)

        self.am = []
        self.roll_mean_list = []
        self.last_n_min = None
        self.last_n_max = None

        self.regressio_flag = None
        self.trend_flag = None

        self.load_last_price()

    def load_last_price(self):
        for c in self.strategy_process.latest_price_list:
            self.am.append(c)

        price_ma_list = numpy.convolve(
                self.am, numpy.ones(self.roll_mean_period) / self.roll_mean_period, mode="valid")
        self.roll_mean_list += list(price_ma_list)

    @common_exception(log_flag=True)
    def cal_indicator(self, quote):
        self.regressio_flag = None
        self.trend_flag = None

        if not quote.get('is_closed', 0):
            return

        last_price = float(quote['last_price'])

        if len(self.am) < self.min_save_window:
            self.am.append(last_price)
            if len(self.am) >= self.roll_mean_period:
                roll_mean = round(sum([float(x) for x in self.am[-self.roll_mean_period:]]) / self.roll_mean_period, 8)
                self.roll_mean_list.append(roll_mean)
            self.logger.info(f'<cal_indicator> less price: min_save_window={self.min_save_window} len am:{len(self.am)}')
            return

        self.am = self.am[-self.min_save_window:]
        self.last_n_max = max(self.am[-self.windows:])
        self.last_n_min = min(self.am[-self.windows:])

        self.am.append(last_price)
        roll_mean = round(sum([float(x) for x in self.am[-self.roll_mean_period:]]) / self.roll_mean_period, 8)
        self.roll_mean_list.append(roll_mean)
        self.roll_mean_list = self.roll_mean_list[-self.interval_period * 2:]

        if last_price < self.last_n_min:
            self.regressio_flag = 'LONG'
        elif last_price > self.last_n_max:
            self.regressio_flag = 'SHORT'

        if last_price > self.roll_mean_list[-self.interval_period] > self.roll_mean_list[-self.interval_period * 2]:
            self.trend_flag = 'LONG'
        elif last_price < self.roll_mean_list[-self.interval_period] < self.roll_mean_list[-self.interval_period * 2]:
            self.trend_flag = 'SHORT'

        self.logger.info(f'<cal_indicator> l={last_price} min={self.last_n_min} max={self.last_n_max} '
                         f'regressio_flag={self.regressio_flag} trend_flag={self.trend_flag}')

    @common_exception(log_flag=True)
    def cal_singal(self, quote):
        instrument = quote['symbol']
        last_price = quote['last_price']

        open_direction = self.open_direction
        trade_price = Decimal(last_price) - Decimal('0.005')
        self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.OPEN, open_direction,
                                                      OrderPriceType.LIMIT, str(trade_price), self.open_volume,
                                                      cash=self.params['roll_mean_period'])
        # print('---- send ----')
        return

        if not quote.get('is_closed', 0):
            return

        open_direction = None
        if not self.regressio_flag:
            pass
        else:
            if self.regressio_flag == 'LONG':
                if self.trend_flag == 'SHORT':
                    self.logger.info(f'<cal_singal> skip by ma: regressio_flag={self.regressio_flag} '
                                     f'trend_flag={self.trend_flag}')
                    return

                open_direction = self.open_direction
            elif self.regressio_flag == 'SHORT':
                if self.trend_flag == 'LONG':
                    self.logger.info(f'<cal_singal> skip by ma: regressio_flag={self.regressio_flag} '
                                     f'trend_flag={self.trend_flag}')
                    return
                open_direction = self.open_direction.get_opposite_direction()

        if not open_direction:
            return

        direction_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', open_direction)
        self.logger.info(f'direction_position={direction_position}')

        opposite_direction_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', open_direction.get_opposite_direction())
        self.logger.info(f'opposite_direction_position={opposite_direction_position}')

        if direction_position.volume:
            self.strategy_process.logger.info('<cal_singal> skip  holding position')
            return
        else:
            if open_direction == Direction.LONG:
                trade_price = Decimal(last_price) + Decimal('0.005')
            else:
                trade_price = Decimal(last_price) - Decimal('0.005')

            self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.OPEN, open_direction,
                                                          OrderPriceType.LIMIT, str(trade_price), self.open_volume)
            self.strategy_process.logger.info(f'<cal_singal> insert_order  instrument={instrument} '
                                              f'OffsetFlag={OffsetFlag} open_direction={open_direction} '
                                              f'OrderPriceType={OrderPriceType} price={str(trade_price)} '
                                              f'volume={self.open_volume}')

            if opposite_direction_position.volume:
                self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.CLOSE, open_direction.get_opposite_direction(),
                                                              OrderPriceType.LIMIT, str(trade_price), opposite_direction_position.volume)
                self.strategy_process.logger.info(f'<cal_singal> insert_order  instrument={instrument} '
                                                  f'OffsetFlag={OffsetFlag.CLOSE} open_direction={open_direction.get_opposite_direction()} '
                                                  f'OrderPriceType={OrderPriceType} price={str(trade_price)} '
                                                  f'volume={opposite_direction_position.volume} ')


