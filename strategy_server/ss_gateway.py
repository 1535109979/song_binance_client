import logging
import time
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtSensors import qoutputrange
from binance.um_futures import UMFutures
from song_binance_client.market.md_gateway import BiFutureMdGateway
from song_binance_client.market.ms_grpc.ms_grpc_stub import BianMarketStub
from song_binance_client.strategy_server.strategy_process import StrategyProcess

from song_binance_client.trade.td_gateway import BiFutureTdGateway
from song_binance_client.utils.configs import Configs
from song_binance_client.utils.dingding import Dingding
from song_binance_client.utils.sys_exception import common_exception


class BiFutureSsGateway:
    def __init__(self):
        self.ms_stub = None
        self.logger = None
        self.strategy_process_map = {}
        self.create_logger()
        self.td_gateway = BiFutureTdGateway(self)
        self.kline_client = UMFutures()

        self.set_strategy_process()

    def set_strategy_process(self):
        for params in Configs.strategy_list:
            instrument = params['instrument']
            self.strategy_process_map[instrument] = StrategyProcess(self, params)
            self.logger.info(f'load strategy: {instrument} {params}')

    @common_exception(log_flag=True)
    def start(self):
        self.ms_stub = BianMarketStub()
        self.ms_stub.subscribe_stream_in_new_thread(
            instruments=self.strategy_process_map.keys(),
            # instruments=['BTCUSDT'],
            on_quote=self.on_quote)

        # 启动交易
        self.td_gateway.connect()
        self.logger = self.td_gateway.logger

        self.send_msg('策略服务启动成功')

    def on_quote(self, quote):
        quote = {k: str(v) for k, v in quote.items() if v is not None}
        imstrument = quote['symbol']
        sp = self.strategy_process_map.get(imstrument)
        if sp:
            sp.on_quote(quote)

    def create_logger(self):
        self.logger = logging.getLogger('bi_future_ss')
        self.logger.setLevel(logging.DEBUG)

        log_fp = Configs.root_fp + 'song_binance_client/logs/bi_future_ss.log'
        from logging.handlers import TimedRotatingFileHandler
        handler = TimedRotatingFileHandler(log_fp, when="midnight", interval=1, backupCount=7)
        handler.suffix = "%Y-%m-%d.log"  # 设置滚动后文件的后缀
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def send_msg(self, msg):
        Dingding.send_msg(msg)


if __name__ == '__main__':
    BiFutureSsGateway().start()

    while 1:
        time.sleep(500)

