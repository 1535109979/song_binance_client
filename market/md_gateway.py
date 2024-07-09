import logging

from song_binance_client.market.bian_future.bian_future_md import BiFutureMd
from song_binance_client.utils.configs import Configs
from song_binance_client.utils.dingding import Dingding


class BiFutureMdGateway:
    def __init__(self):
        self.create_logger()
        self.client = BiFutureMd(self)
        self.login()

    def login(self):
        self.client.connect()

    def get_api_configs(self):
        return {'stream_url': 'wss://fstream.binance.com'}

    def on_login(self):
        print('on_login')

    def subscribe(self, instrument: list, on_quote=None):
        if on_quote:
            self.on_quote = on_quote

        self.client.subscribe(instrument)

    def on_quote(self, quote):
        print(quote)

    def create_logger(self):
        self.logger = logging.getLogger('bi_future_ms')
        self.logger.setLevel(logging.DEBUG)
        log_fp = Configs.root_fp + 'song_binance_client/logs/bi_future_ms.log'
        file_handler = logging.FileHandler(log_fp)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def on_error(self, msg):
        self.logger.error(msg)
        Dingding.send_msg(msg)

    def on_front_disconnected(self, msg):
        self.logger.error(msg)
        Dingding.send_msg(msg)


def on_quote(quote):
    print('data:', quote)


if __name__ == '__main__':
    bi = BiFutureMdGateway()
    bi.subscribe(['BTCUSDT'], on_quote=on_quote)
