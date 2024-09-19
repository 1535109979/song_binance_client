import logging
import time
from copy import copy
from datetime import datetime
from decimal import Decimal

from song_binance_client.database.bian_f_dbm import RtnTrade, AccountValue
from song_binance_client.trade.future_api import BiFutureTd
from song_binance_client.utils.aio_timer import AioTimer
from song_binance_client.utils.configs import Configs
from song_binance_client.utils.dingding import Dingding
from song_binance_client.utils.exchange_enum import OffsetFlag, Direction, OrderPriceType, ExchangeType
from song_binance_client.utils.sys_exception import common_exception


class BiFutureTdGateway:
    def __init__(self, ss_gateway):
        self.logger = ss_gateway.logger
        self.client = BiFutureTd(self)
        self.account_book = self.client.account_book
        self.open_orders_map = {}
        self.trade_order_timer = None

    def connect(self):
        self.client.connect()

    @common_exception(log_flag=True)
    def insert_order(self, instrument: str, offset_flag: OffsetFlag, direction: Direction,
                      order_price_type: OrderPriceType, price: float, volume: float,
                      cancel_delay_seconds: int = 0, **kwargs) -> str:
        """ 向交易所报单
        做多开仓=OPEN:LONG    做空开仓=OPEN:SHORT
        做多平仓=CLOSE:LONG   做空平仓=CLOSE:SHORT
        """
        instrument_book = self.account_book.get_instrument_book(instrument + f'.{self.exchange_type}')
        min_volume_muti = int(1 / float(instrument_book.min_volume_step))
        min_price_step = instrument_book.min_price_step

        if offset_flag == OffsetFlag.OPEN:
            if direction == Direction.LONG:
                trade_price = Decimal(price) + Decimal(min_price_step) * 10
            elif direction == Direction.SHORT:
                trade_price = Decimal(price) - Decimal(min_price_step) * 10
        elif offset_flag == OffsetFlag.CLOSE:
            if direction == Direction.LONG:
                trade_price = Decimal(price) - Decimal(min_price_step) * 10
            elif direction == Direction.SHORT:
                trade_price = Decimal(price) + Decimal(min_price_step) * 10

        if 'cash' in kwargs:
            volume = kwargs['cash'] / float(price)
            volume = round(volume * min_volume_muti) / min_volume_muti
            self.logger.info(f'cal vol: min_volume_muti={min_volume_muti} cash={kwargs["cash"]} '
                             f'price={trade_price} volume={volume}')

        req = {
            'instrument': instrument,
            'offset_flag': offset_flag,
            'direction': direction,
            'order_price_type': order_price_type,
            'price': str(trade_price),
            'volume': str(volume),
            'cancel_delay_seconds': cancel_delay_seconds,
        }
        self.logger.info(f'<insert_order> instrument={instrument} offset_flag={offset_flag} direction={direction} '
                         f'order_price_type={order_price_type} trade_price={trade_price} volume={volume}')

        client_order_id = self.client.insert_order(
            **req, **kwargs)

        return client_order_id

    def on_order(self, rtn_order):
        pass

    @common_exception(log_flag=True)
    def on_trade(self, rtn_trade):
        save_rtn_trade = RtnTrade(
            instrument=rtn_trade.instrument,
            client_id=rtn_trade.client_id,
            offset=rtn_trade.offset_flag,
            side=rtn_trade.direction,
            volume=rtn_trade.volume,
            price=rtn_trade.price,
            trading_day=rtn_trade.trading_day,
            trade_time=rtn_trade.trade_time,
            commission=rtn_trade.commission,
            update_time=datetime.now(),
        )
        save_rtn_trade.save()

    def cancel_cancel_all_order(self, instrument):
        self.client.cancel_all_order(instrument)

    def get_api_configs(self):
        return Configs.api_config

    def send_position_error_msg(self, instrument, error):
        self.logger.error(f"<send_position_error_msg> {instrument} {error}")
        self.send_msg(f"<send_position_error_msg> {instrument} {error}")

    def send_start_unsuccessful_msg(self, msg):
        self.logger.error(f"<send_start_unsuccessful_msg> {msg}")
        self.send_msg(f"<send_start_unsuccessful_msg> {msg}")

    def send_start_msg(self, login_reqid):
        self.logger.info(f"<send_start_msg> {login_reqid}")
        self.send_msg(f"<send_start_msg> {login_reqid}")

    @common_exception(log_flag=True)
    def on_account_update(self):
        account_value = AccountValue(
            balance=self.account_book.balance,
            update_time=datetime.now(),
        )
        account_value.save()
        self.logger.info(f"<on_account_update> balance={self.account_book.balance}")

    def on_front_disconnected(self, msg):
        self.logger.info(f"<on_front_disconnected> {msg}")
        self.send_msg(msg)

    def gen_error_order_id(self, err_msg):
        self.send_msg(err_msg)

    @property
    def exchange_type(self):
        return ExchangeType.BINANCE_F

    def send_msg(self, msg):
        Dingding.send_msg(msg)


if __name__ == '__main__':
    td = BiFutureTdGateway()
    td.connect()

    time.sleep(5)
    # posi = td.account_book.get_instrument_position(f'EOSUSDT.{td.exchange_type}', Direction.LONG)
    # print(posi)

    td.insert_order('EOSUSDT', OffsetFlag.OPEN, Direction.LONG,
                    OrderPriceType.LIMIT, 0.79, 10)

    while 1:
        pass
