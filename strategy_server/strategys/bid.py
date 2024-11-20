from song_binance_client.utils.sys_exception import common_exception
from song_binance_client.trade.do.position import InstrumentPosition
from song_binance_client.utils.configs import Configs
from song_binance_client.utils.exchange_enum import Direction, OffsetFlag, OrderPriceType

class BidStrategy:
    def __init__(self, strategy_process, params):
        self.cover_count = strategy_process.cover_count




    @common_exception(log_flag=True)
    def cal_singal(self, quote):
        last_price = float(quote['last_price'])
        instrument = quote['symbol']

        long_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', Direction.LONG)

        short_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', Direction.SHORT)


