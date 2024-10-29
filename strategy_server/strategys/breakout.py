import time

import numpy

from song_binance_client.trade.do.position import InstrumentPosition
from song_binance_client.utils.configs import Configs
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

        self.signal_flag = None

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
                roll_mean = round(sum([float(x) for x in self.am[-self.roll_mean_period:]]) / self.roll_mean_period, 4)
                self.roll_mean_list.append(roll_mean)
            self.logger.info(f'<cal_indicator>less price:min_save_window={self.min_save_window} len am:{len(self.am)}')
            return

        self.am = self.am[-self.min_save_window:]
        self.last_n_max = max(self.am[-self.windows:])
        self.last_n_min = min(self.am[-self.windows:])
        self.min_dr = last_price / self.last_n_min - 1
        self.max_dr = last_price / self.last_n_max - 1

        self.am.append(last_price)
        roll_mean = round(sum([float(x) for x in self.am[-self.roll_mean_period:]]) / self.roll_mean_period, 4)
        self.roll_mean_list.append(roll_mean)
        self.roll_mean_list = self.roll_mean_list[-self.interval_period * 2:]

        if last_price < self.last_n_min:
            self.regressio_flag = Direction.LONG
        elif last_price > self.last_n_max:
            self.regressio_flag = Direction.SHORT

        if last_price > self.roll_mean_list[-self.interval_period] > self.roll_mean_list[-self.interval_period * 2]:
            self.trend_flag = Direction.LONG
        elif last_price < self.roll_mean_list[-self.interval_period] < self.roll_mean_list[-self.interval_period * 2]:
            self.trend_flag = Direction.SHORT

        if self.regressio_flag:
            if self.regressio_flag != self.trend_flag:
                self.signal_flag = [self.regressio_flag,time.time(),0]

        if self.signal_flag:
            if (self.signal_flag[0] == Direction.LONG and self.signal_flag[0] != self.trend_flag and
                    time.time() - self.signal_flag[1] < Configs.signal_reserve_time and self.min_dr > Configs.dr):
                self.signal_flag[2] = 1
            if (self.signal_flag[0] == Direction.SHORT and self.signal_flag[0] != self.trend_flag  and
                    time.time() - self.signal_flag[1] < Configs.signal_reserve_time and self.max_dr < -Configs.dr):
                self.signal_flag[2] = 1

        self.logger.info(f'<cal_indicator> l={last_price} min={self.last_n_min} max={self.last_n_max} '
                         f'min_dr={self.min_dr} max_dr={self.max_dr}'
                         f'{self.roll_mean_list[-self.interval_period]} '
                         f'{self.roll_mean_list[-self.interval_period * 2]} '
                         f'regressio_flag={self.regressio_flag} trend_flag={self.trend_flag} '
                         f'signal_flag={self.signal_flag}')

    @common_exception(log_flag=True)
    def cal_singal(self, quote):
        instrument = quote['symbol']
        last_price = quote['last_price']

        if not quote.get('is_closed', 0):
            return

        self.strategy_process.logger.info(f'<cal_singal> signal_flag={self.signal_flag}')

        if not self.signal_flag:
            pass
        else:
            if not self.signal_flag[2] or time.time() - self.signal_flag[1] > Configs.signal_reserve_time:
                return

            signal_direction = self.signal_flag[0]

            direction_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
                f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', signal_direction)
            self.logger.info(f'direction_position={direction_position}')

            opposite_direction_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
                f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', signal_direction.get_opposite_direction())
            self.logger.info(f'opposite_direction_position={opposite_direction_position}')

            if direction_position.volume:
                #   信号方向 有持仓
                self.strategy_process.logger.info('<cal_singal> skip holding position')
                return
            else:
                # 有信号反方向持仓
                if opposite_direction_position.volume:

                    self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.CLOSE,
                                                                  signal_direction.get_opposite_direction(),
                                                                  OrderPriceType.LIMIT, str(last_price),
                                                                  opposite_direction_position.volume)
                    self.strategy_process.logger.info(f'<cal_singal> insert_order  instrument={instrument} '
                                                      f'OffsetFlag=close '
                                                      f'direction={self.regressio_flag.get_opposite_direction()} '
                                                      f'OrderPriceType={OrderPriceType.LIMIT} price={str(last_price)} '
                                                      f'volume={opposite_direction_position.volume} ')

                self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.OPEN, signal_direction,
                                                              OrderPriceType.LIMIT, str(last_price), self.open_volume,
                                                              cash=self.params['cash'])
                self.strategy_process.logger.info(f'<cal_singal> insert_order  instrument={instrument} '
                                                  f'OffsetFlag=open direction={self.regressio_flag} '
                                                  f'OrderPriceType={OrderPriceType} price={str(last_price)} '
                                                  f'volume={self.open_volume} cash={self.params["cash"]}')

                self.signal_flag = None
