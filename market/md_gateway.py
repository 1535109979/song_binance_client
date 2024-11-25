import logging
import threading
import time
from asyncio import events
import traceback
import asyncio
from random import uniform

from sqlalchemy.sql.functions import random

from song_binance_client.grpc_files import ms_server_pb2
from song_binance_client.market.bian_future.bian_future_md import BiFutureMd
from song_binance_client.market.quote_writer import QuoteWriter
from song_binance_client.utils.configs import Configs
from song_binance_client.utils.dingding import Dingding


class BiFutureMdGateway:
    def __init__(self,mode=True):
        self.mode = mode
        self.sub_instruments = set()
        self.quote_subscriber = dict()
        self.create_logger()
        self.loop = events.new_event_loop()
        self.last_quote = {}

        self.client = BiFutureMd(self)
        if mode == True:
            self.login()

    def login(self):
        self.client.connect()
        Dingding.send_msg('行情服务启动成功')

    def get_api_configs(self):
        return {'stream_url': 'wss://fstream.binance.com'}

    def on_login(self):
        print('on_login')

    def add_subscribe(self, need_sub, quote_writer: QuoteWriter):
        if self.mode:
            self.client.subscribe(need_sub)
        else:
            threading.Thread(target=self.send_mock_quote).start()

        for symbol in need_sub:
            self.sub_instruments.update([symbol])
            if symbol not in quote_writer.subscribe_symbol:
                quote_writer.add_symbol([symbol])

    def send_mock_quote(self):
        data = {"e":"kline","E":1732259449367,"s":"ONDOUSDT","k":{"t":1732259400000, "T":1732259459999, "s":"BTCUSDT",
                "i":"1m", "f":5631843153, "L":5631844629, "o":"99036.00", "c":98997.40, "h":"99045.60",
                "l":"98991.10", "v":"38.940", "n":1476, "x":False, "q":"3855827.31040", "V":"20.363",
                                                          "Q":"2016311.85580", "B":"0"}}
        k = data['k']
        quote = {
            "id": int(data["E"]), "localtime": data["E"],
            "symbol": data["s"], "name": k["s"],
            "open_price": k['o'],
            "high_price": k['h'],
            "low_price": k['l'],
            "last_price": k['c'] * uniform(0.8, 1.2),
            "volume": k['v'],
            "turnover": k['q'],
            "is_closed": 1 if k['x'] else 0,
        }
        while True:
            self.on_quote(quote)
            time.sleep(0.5)

    def on_quote(self, quote):
        quote = {k: str(v) for k, v in quote.items() if v is not None}
        quote['ms_gateway_timestamp'] = str(time.time())
        if self.quote_subscriber:
            for p, q in self.quote_subscriber.items():
                if quote['symbol'] in q.subscribe_symbol:
                    self.send_quote(q, quote)
        self.logger.info(f'{quote["symbol"]} {quote["ms_gateway_timestamp"]}')

    def send_quote(self, q, quote):
        try:
            future = asyncio.run_coroutine_threadsafe(q.writer.write(self.create_grpc_reply(quote=quote)), self.loop)
            future.result()
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
    bi.add_subscribe(['BTCUSDT'], on_quote=on_quote)
