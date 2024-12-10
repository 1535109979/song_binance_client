import time

from song_binance_client.utils.sys_exception import common_exception
from song_binance_client.trade.do.position import InstrumentPosition
from song_binance_client.utils.configs import Configs
from song_binance_client.utils.exchange_enum import Direction, OffsetFlag, OrderPriceType

class BidStrategy:
    def __init__(self, strategy_process, params):
        self.strategy_process = strategy_process
        self.logger = self.strategy_process.logger

        self.params = params
        self.peak = params['peak']
        self.tough = params['tough']
        self.cash = params['cash']
        self.last_couer_price = params['last_couer_price']
        self.cover_count = strategy_process.cover_count
        self.cover_decline_list = params['cover_decline_list']
        self.cover_muti_list = params['cover_muti_list']
        self.stop_profit_rate = params['stop_profit_rate']

    @common_exception(log_flag=True)
    def cal_indicator(self, quote):
        last_price = float(quote['last_price'])
        instrument = quote['symbol']


        if last_price > self.peak or not self.peak:
            self.peak = last_price

        if last_price < self.tough or not self.tough:
            self.tough = last_price

        long_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', Direction.LONG)

        short_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', Direction.SHORT)

        tough_rise_rate = (last_price / self.tough - 1) * 100
        peak_decline_rate = (1 - last_price / self.peak) * 100

        if long_position.volume:
            # breakout 做反手交易 之后 需要 重置
            if self.strategy_process.reset_flag:
                self.cover_count = 0
                self.last_couer_price = long_position.cost
                self.peak = last_price
                self.tough = last_price
                self.strategy_process.reset_flag = False
                return

            decline_rate = (last_price / self.last_couer_price - 1) * 100
            profit_rate = (last_price / long_position.cost - 1) * 100

            self.logger.info(
                f'<bid cal_indicator> LONG <cover_count={self.cover_count} {self.cover_decline_list[self.cover_count]}> '
                f'decline_rate = {decline_rate} profit_rate={profit_rate} '
                f'tough_rise_rate={tough_rise_rate} peak_decline_rate={peak_decline_rate} '
                f'peak={self.peak} tough={self.tough} l={last_price} '
                f'last_couer_price={self.last_couer_price}')


            if profit_rate > self.stop_profit_rate and peak_decline_rate > 0.2 and self.cover_count:
                self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.CLOSE,
                                                              Direction.LONG,
                                                              OrderPriceType.LIMIT, str(last_price),
                                                              long_position.volume)
                self.logger.info(f'<bid cal_indicator> stop_profit insert_order '
                                 f'{instrument} close long {last_price} {long_position.volume}')
                self.cover_count = 0
                self.peak = last_price
                self.tough = last_price
                return

            # 补仓次数达到上限
            if self.cover_count == len(self.cover_muti_list):
                self.logger.info(f'cover_count limit:cover_count times={self.cover_count}')
                return

            if decline_rate < - self.cover_decline_list[self.cover_count] and tough_rise_rate > 0.2:
                    self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.OPEN, Direction.LONG,
                                                                  OrderPriceType.LIMIT, str(last_price), 1,
                                                                  cash=self.cover_muti_list[self.cover_count] * self.cash,)
                    self.strategy_process.logger.info(f'<bid cal_indicator> cover insert_order  instrument={instrument} '
                                                      f'open LONG LIMIT price={str(last_price)} '
                                                      f'cash={self.cover_muti_list[self.cover_count] * self.cash}')
                    self.cover_count += 1
                    self.last_couer_price = last_price

        if short_position.volume:
            if self.strategy_process.reset_flag:
                self.cover_count = 0
                self.last_couer_price = short_position.cost
                self.peak = last_price
                self.tough = last_price
                self.strategy_process.reset_flag = False
                return

            decline_rate = (1 - last_price / self.last_couer_price) * 100
            profit_rate = (1 - last_price / short_position.cost) * 100
            self.logger.info(
                f'<bid cal_indicator> SHORT <cover_count={self.cover_count} {self.cover_decline_list[self.cover_count]}> '
                f'decline_rate = {decline_rate} profit_rate={profit_rate} '
                f'tough_rise_rate={tough_rise_rate}  peak_decline_rate={peak_decline_rate} '
                f'peak={self.peak} tough={self.tough} l={last_price} '
                f'last_couer_price={self.last_couer_price}')

            if profit_rate > self.stop_profit_rate and tough_rise_rate > 0.2 and self.cover_count:
                self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.CLOSE,
                                                              Direction.SHORT,
                                                              OrderPriceType.LIMIT, str(last_price),
                                                              short_position.volume)
                self.logger.info(f'<bid cal_indicator> stop_profit insert_order '
                                 f'{instrument} close short {last_price} {short_position.volume}')

                self.cover_count = 0
                self.peak = last_price
                self.tough = last_price
                return

            # 补仓次数达到上限
            if self.cover_count == len(self.cover_muti_list):
                self.logger.info(f'cover_count limit:cover_count times={self.cover_count}')
                return

            if decline_rate < - self.cover_decline_list[self.cover_count] and peak_decline_rate > 0.2:
                self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.OPEN, Direction.SHORT,
                                                              OrderPriceType.LIMIT, str(last_price), 1,
                                                              cash=self.cover_muti_list[self.cover_count] * self.cash, )

                self.strategy_process.logger.info(f'<bid cal_indicator> cover insert_order  instrument={instrument} '
                                                  f'open SHORT LIMIT price={str(last_price)} '
                                                  f'cash={self.cover_muti_list[self.cover_count] * self.cash}')
                self.last_couer_price = last_price
                self.cover_count += 1

    @common_exception(log_flag=True)
    def cal_singal(self, quote):
        pass

