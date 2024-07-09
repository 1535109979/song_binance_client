from song_binance_client.trade.do.position import InstrumentPosition
from song_binance_client.utils.exchange_enum import Direction, OffsetFlag, OrderPriceType


class StopLoss:
    def __init__(self, strategy_process, params):
        self.strategy_process = strategy_process
        self.stop_loss_rate = params['stop_loss_rate']

    def cal_indicator(self, quote):
        pass

    def cal_singal(self, quote):
        if not quote.get('is_closed', 0):
            return
        last_price = float(quote['last_price'])
        instrument = quote['symbol']

        long_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', Direction.LONG)

        short_position: InstrumentPosition = self.strategy_process.td_gateway.account_book.get_instrument_position(
            f'{instrument}.{self.strategy_process.td_gateway.exchange_type}', Direction.SHORT)

        if long_position.cost:
            decline_rate = last_price / long_position.cost - 1
            self.strategy_process.logger.info(f'last_price={last_price} decline_rate={decline_rate} stop_loss_rate={self.stop_loss_rate}')

            if decline_rate < -self.stop_loss_rate:
                self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.CLOSE, Direction.LONG,
                                             OrderPriceType.LIMIT, str(float(last_price)), long_position.volume)

                self.strategy_process.stop_loss_flag = True
                self.strategy_process.logger.info(f'stop_loss=LONG')

        if short_position.cost:
            decline_rate = 1 - last_price / short_position.cost
            self.strategy_process.logger.info(f'last_price={last_price} decline_rate={decline_rate} stop_loss_rate={self.stop_loss_rate}')

            if decline_rate < -self.stop_loss_rate:
                self.strategy_process.td_gateway.insert_order(instrument, OffsetFlag.CLOSE, Direction.SHORT,
                                             OrderPriceType.LIMIT, str(float(last_price)), short_position.volume)
                self.strategy_process.stop_loss_flag = True
                self.strategy_process.logger.info(f'stop_loss=short')
