import os
from datetime import datetime

from peewee import *


class SqliteDatabaseManage:
    def __init__(self):
        self.root_fp = os.path.join(os.path.expanduser('~'))
        self.data_fp = self.root_fp + '/byt_pub/a_songbo/binance_client/database/'

    def get_connect(self, db_name=''):
        db_fp = self.data_fp + 'bian_f_data.db'
        db = SqliteDatabase(db_fp)
        db.connect()
        return db


class RtnTrade(Model):
    id = AutoField(primary_key=True)
    instrument = CharField()
    client_id = CharField()
    offset = CharField()
    side = CharField()
    volume = FloatField()
    price = FloatField()
    trading_day = CharField()
    trade_time = CharField()
    commission = FloatField()
    update_time = DateTimeField()

    class Meta:
        database = SqliteDatabaseManage().get_connect()
        table_name = 'rtn_trade'


class AccountValue(Model):
    id = AutoField(primary_key=True)
    balance = FloatField()
    update_time = DateTimeField()

    class Meta:
        database = SqliteDatabaseManage().get_connect()
        table_name = 'account_value'


if __name__ == '__main__':
    # RtnTrade.create_table()
    AccountValue.create_table()


    # save_rtn_trade = RtnTrade(
    #             instrument='instrument',
    #             client_id='client_id',
    #             offset='offset',
    #             side='side',
    #             volume=10,
    #             price=9,
    #             trading_day='245',
    #             trade_time='trade_time',
    #             commission='commission',
    #             update_time=datetime.now(),
    #         )
    # save_rtn_trade.save()


