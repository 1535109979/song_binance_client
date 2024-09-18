import logging
from datetime import datetime, timedelta

import pandas

from song_binance_client.strategy_server.strategys.breakout import BreakoutStrategy
from song_binance_client.strategy_server.strategys.stop_cover import StopLoss
from song_binance_client.utils.configs import Configs


class StrategyProcess:

    def __init__(self, gateway, params):
        self.gateway = gateway
        self.td_gateway = self.gateway.td_gateway
        self.logger = None
        self.latest_price_list = None
        self.params = params

        self.strategy_list = []
        self.create_logger()

        self.load_strategy()

    def load_strategy(self):
        # if self.strategy_config.get('stop_loss'):
        #     self.strategy_list.append(StopLoss(self, self.strategy_config['stop_loss']))
        if self.params['strategy_name'] == 'breakout':
            self.get_klines()

            self.strategy_list.append(BreakoutStrategy(self, self.params))

    def on_quote(self, quote):
        # quote['last_price'] = float(quote['last_price'])
        quote['is_closed'] = float(quote['is_closed'])

        for strategy in self.strategy_list:
            strategy.cal_indicator(quote)

        for strategy in self.strategy_list:
            strategy.cal_singal(quote)

    def get_klines(self):
        data = self.gateway.kline_client.klines(self.params['instrument'], "1m", limit=1000)

        df = pandas.DataFrame(data)
        df.columns = ['start_time', 'open', 'high', 'low', 'close', 'vol', 'end_time',
                      'quote_asset_vol', 'number_of_trade', 'base_asset_volume', 'quote_asset_volume', 'n']
        df['start_time'] = df['start_time'].apply(lambda x: datetime.fromtimestamp(x / 1000))
        df['close_time'] = df['start_time'].apply(lambda x: x + timedelta(minutes=1))

        df['end_time'] = df['end_time'].apply(lambda x: datetime.fromtimestamp(x / 1000))
        df = df.sort_values(by='close_time')
        df = df[df['close_time'] <= datetime.now()]
        self.latest_price_list = df['close'].astype(float).to_list()

    def create_logger(self):
        self.logger = logging.getLogger(f'bi_future_strategy_{self.params["instrument"]}')
        self.logger.setLevel(logging.DEBUG)
        log_fp = Configs.root_fp + f'song_binance_client/logs/strategy_logs/{self.params["instrument"]}.log'

        from logging.handlers import TimedRotatingFileHandler
        handler = TimedRotatingFileHandler(log_fp, when="midnight", interval=1, backupCount=7)
        handler.suffix = "%Y-%m-%d.log"  # 设置滚动后文件的后缀
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

