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

    @common_exception(log_flag=True)
    def cal_indicator(self, quote):
        last_price = float(quote['last_price'])
        instrument = quote['symbol']

        if last_price > self.peak:
            self.peak = last_price

        if last_price < self.tough:
            self.tough = last_price

        decline_rate = 0

        long_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', Direction.LONG)

        short_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', Direction.SHORT)

        if long_position.volume:
            decline_rate = (last_price / self.last_couer_price - 1) * 100
            profit_rate = (last_price / long_position.cost - 1) * 100
            rise_rate = (last_price / self.tough - 1) * 100
            self.logger.info(
                f'<cal_indicator> LONG <cover_count={self.cover_count} {self.cover_decline_list[self.cover_count]}> '
                f'decline_rate = {decline_rate} profit_rate={profit_rate} rise_rate={rise_rate} '
                f'peak={self.peak} tough={self.tough}')

            if decline_rate < - self.cover_decline_list[self.cover_count] and rise_rate > 0.005:
                self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.OPEN, Direction.LONG,
                                                              OrderPriceType.LIMIT, str(last_price), self.open_volume,
                                                              cash=self.cover_muti_list[self.cover_count] * self.cash,)
                self.strategy_process.logger.info(f'<cal_singal> insert_order  instrument={instrument} '
                                                  f'open LONG {OrderPriceType} price={str(last_price)} '
                                                  f'volume={self.open_volume} '
                                                  f'cash={self.cover_muti_list[self.cover_count] * self.cash}')

        if short_position.volume:
            decline_rate = (1 - last_price / self.last_couer_price) * 100
            profit_rate = (1 - last_price / short_position.cost) * 100
            rise_rate = (1 - last_price / self.peak) * 100
            self.logger.info(
                f'<cal_indicator> SHORT <cover_count={self.cover_count} {self.cover_decline_list[self.cover_count]}> '
                f'decline_rate = {decline_rate} profit_rate={profit_rate} rise_rate={rise_rate} '
                f'peak={self.peak} tough={self.tough}')

            if decline_rate < - self.cover_decline_list[self.cover_count] and rise_rate > 0.005:
                # self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.OPEN, Direction.SHORT,
                #                                               OrderPriceType.LIMIT, str(last_price), self.open_volume,
                #                                               cash=self.cover_muti_list[self.cover_count] * self.cash, )
                #
                self.strategy_process.logger.info(f'<cal_singal> insert_order  instrument={instrument} '
                                                  f'open SHORT {OrderPriceType} price={str(last_price)} '
                                                  f'volume={self.open_volume} '
                                                  f'cash={self.cover_muti_list[self.cover_count] * self.cash}')


    @common_exception(log_flag=True)
    def cal_singal(self, quote):
        pass