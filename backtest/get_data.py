import sqlite3
from datetime import datetime

import pandas
import pandas as pd
from binance.spot import Spot as Client
from binance.um_futures import UMFutures
pandas.set_option("expand_frame_repr", False)


class BinanceData:

    def __init__(self, mode='future'):
        self.spot_client = Client()
        self.future_client = UMFutures()
        self.mode = mode

    def download_data(self, start_time, end_time, symbol='BTCUSDT', interval='1m'):
        st_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timestamp()
        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S').timestamp()

        while st_time < end_time:
            if self.mode == 'spot':
                df = self.get_spot_data(st_time, symbol, interval)
            elif self.mode == 'future':
                df = self.get_future_data(st_time, symbol, interval)
            print(df)
            self.save_data(df, table_name=self.mode+'_'+symbol.lower())
            st_time = st_time + 1000 * 60

    def save_data(self, df, table_name='spot_data'):
        with sqlite3.connect('binance_quote_data.db') as conn:
            df.to_sql(table_name, conn, if_exists='append', index=False)

    def get_future_data(self, st_time, symbol='BTCUSDT', interval='1m'):
        data = self.future_client.klines(symbol, interval, limit=1000, startTime=int(st_time) * 1000)
        df = pandas.DataFrame(data)
        df.columns = ['start_time', 'open', 'high', 'low', 'close', 'vol', 'end_time',
                      'quote_asset_vol', 'number_of_trade', 'base_asset_volume', 'quote_asset_volume', 'n']
        df['start_time'] = df['start_time'].apply(lambda x: datetime.fromtimestamp(x / 1000))
        df['end_time'] = df['end_time'].apply(lambda x: datetime.fromtimestamp(x / 1000))
        return df

    def get_spot_data(self, st_time, symbol='BTCUSDT', interval='1m'):
        data = self.spot_client.klines(symbol, interval, limit=1000, startTime=int(st_time) * 1000)
        df = pandas.DataFrame(data)
        df.columns = ['start_time', 'open', 'high', 'low', 'close', 'vol', 'end_time',
                      'quote_asset_vol', 'number_of_trade', 'base_asset_volume', 'quote_asset_volume', 'n']
        df['start_time'] = df['start_time'].apply(lambda x: datetime.fromtimestamp(x / 1000))
        df['end_time'] = df['end_time'].apply(lambda x: datetime.fromtimestamp(x / 1000))
        return df


if __name__ == '__main__':
    BinanceData().download_data('2024-07-04 11:39:00', '2024-07-08 12:00:00', symbol='LTCUSDT')

