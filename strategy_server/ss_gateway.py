import time
from concurrent.futures import ThreadPoolExecutor

from a_songbo.binance_client.market.md_gateway import BiFutureMdGateway
from a_songbo.binance_client.strategy_server.strategy_process import StrategyProcess

from a_songbo.binance_client.trade.td_gateway import BiFutureTdGateway
from a_songbo.binance_client.utils.configs import Configs
from a_songbo.binance_client.utils.thread import submit


class BiFutureSsGateway:
    def __init__(self):
        # 启动行情
        self.ms_gateway = BiFutureMdGateway()
        self.ms_thread_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ms")
        # 启动交易
        self.td_gateway = BiFutureTdGateway()
        self.td_gateway.connect()
        self.logger = self.td_gateway.logger

        self.strategy_process_map = {}

        self.set_strategy_process()

    def set_strategy_process(self):
        for strategy_entity in Configs.strategy_list:
            instrument = strategy_entity['instrument']
            self.strategy_process_map[instrument] = StrategyProcess(self, strategy_entity)

    def start(self):
        submit(_executor=self.ms_thread_pool, _fn=self.ms_gateway.subscribe,
               _kwargs=dict(instrument=self.strategy_process_map.keys(),
                            on_quote=self.on_quote))

        print('---')

    def on_quote(self, quote):
        imstrument = quote['symbol']
        sp = self.strategy_process_map.get(imstrument)
        if sp:
            sp.on_quote(quote)


if __name__ == '__main__':
    BiFutureSsGateway().start()

    while 1:
        time.sleep(500)

