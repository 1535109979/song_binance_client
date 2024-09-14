import logging
import time
from asyncio import events
import traceback
import asyncio

from song_binance_client.grpc_files import ms_server_pb2
from song_binance_client.market.bian_future.bian_future_md import BiFutureMd
from song_binance_client.market.quote_writer import QuoteWriter
from song_binance_client.utils.configs import Configs
from song_binance_client.utils.dingding import Dingding


class BiFutureMdGateway:
    def __init__(self):
        self.sub_instruments = set()
        self.quote_subscriber = dict()
        self.create_logger()
        self.loop = events.new_event_loop()

        self.client = BiFutureMd(self)
        self.login()

    def login(self):
        self.client.connect()
        # Dingding.send_msg('行情服务启动成功')

    def get_api_configs(self):
        return {'stream_url': 'wss://fstream.binance.com'}

    def on_login(self):
        print('on_login')

    def add_subscribe(self, need_sub, quote_writer: QuoteWriter):
        self.client.subscribe(need_sub)

        for symbol in need_sub:
            self.sub_instruments.update([symbol])
            if symbol not in quote_writer.subscribe_symbol:
                quote_writer.add_symbol([symbol])

    def on_quote(self, quote):
        quote = {k: str(v) for k, v in quote.items() if v is not None}
        quote['ms_gateway_timestamp'] = str(time.time())
        if self.quote_subscriber:
            for p, q in self.quote_subscriber.items():
                if quote['symbol'] in q.subscribe_symbol:
                    self.send_quote(q, quote)

    def send_quote(self, q, quote):
        try:
            asyncio.run_coroutine_threadsafe(q.writer.write(self.create_grpc_reply(quote=quote)), self.loop)
        except:
            traceback.print_exc()

    def create_grpc_reply(self, quote):
        return ms_server_pb2.Quote(quote=quote)

    def add_subscriber(self, peer, context):
        quote_writer = QuoteWriter(context)
        self.quote_subscriber[peer] = quote_writer
        return quote_writer

    def get_or_create_subscriber(self,peer,context):
        quote_writer = self.quote_subscriber.get(peer)
        if not quote_writer:
            quote_writer = self.add_subscriber(peer,context)
        return quote_writer

    def create_logger(self):
        self.logger = logging.getLogger('bi_future_ms')
        self.logger.setLevel(logging.DEBUG)
        log_fp = Configs.root_fp + 'song_binance_client/logs/bi_future_ms.log'

        from logging.handlers import TimedRotatingFileHandler
        handler = TimedRotatingFileHandler(log_fp, when="midnight", interval=1, backupCount=7)
        handler.suffix = "%Y-%m-%d.log"  # 设置滚动后文件的后缀
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

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
