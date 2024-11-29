import logging
import time
from datetime import datetime, timedelta

import pandas

from song_binance_client.strategy_server.strategys.bid import BidStrategy
from song_binance_client.strategy_server.strategys.breakout import BreakoutStrategy
from song_binance_client.strategy_server.strategys.stop_cover import StopLoss
from song_binance_client.utils.configs import Configs
from song_binance_client.utils.sys_exception import common_exception


class StrategyProcess:

    def __init__(self, gateway, params):
        self.reset_flag = False
        self.gateway = gateway
        self.td_gateway = self.gateway.td_gateway
        self.logger = None
        self.latest_price_list = []
        self.params = params
        self.cover_count = params['cover_count']

        self.strategy_list = []
        self.create_logger()

        self.load_strategy()



    def load_strategy(self):
        if 'breakout' in self.params['strategy_name']:
            self.get_klines()
            b = BreakoutStrategy(self, self.params)
            self.strategy_list.append(b)

        if 'bid' in self.params['strategy_name']:
            b = BidStrategy(self, self.params)
            self.strategy_list.append(b)

    def on_quote(self, quote):
        # quote['last_price'] = float(quote['last_price'])
        quote['is_closed'] = float(quote['is_closed'])

        for strategy in self.strategy_list:
            strategy.cal_indicator(quote)

        for strategy in self.strategy_list:
            strategy.cal_singal(quote)

    def get_klines(self, min_save_window=2100):
        st_time = int(time.time()) - min_save_window * 60
        end_time = int(time.time())
        self.download_data(st_time, end_time, self.params['instrument'], "1m")

    @common_exception(log_flag=True)
    def download_data(self, start_time, end_time, symbol='BTCUSDT', interval='1m'):
        st_time = start_time

        while st_time < end_time:
            df = self.get_future_data(st_time, symbol, interval)
            self.latest_price_list += df['close'].astype(float).to_list()
            st_time = st_time + 1000 * 60

    def get_future_data(self, st_time, symbol='BTCUSDT', interval='1m'):
        data = self.gateway.kline_client.klines(symbol, interval, limit=1000, startTime=int(st_time) * 1000)
        df = pandas.DataFrame(data)
        df.columns = ['start_time', 'open', 'high', 'low', 'close', 'vol', 'end_time',
                      'quote_asset_vol', 'number_of_trade', 'base_asset_volume', 'quote_asset_volume', 'n']
        df['start_time'] = df['start_time'].apply(lambda x: datetime.fromtimestamp(x / 1000))
        df['close_time'] = df['start_time'].apply(lambda x: x + timedelta(minutes=1))
        df['end_time'] = df['end_time'].apply(lambda x: datetime.fromtimestamp(x / 1000))
        df = df.sort_values(by='close_time')
        df = df[df['close_time'] <= datetime.now()]
        return df

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

