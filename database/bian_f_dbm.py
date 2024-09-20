import os
from datetime import datetime

from peewee import *

from song_binance_client.utils.configs import Configs


class SqliteDatabaseManage:
    def __init__(self):
        self.data_fp = Configs.root_fp + 'song_binance_client/database/'

    def get_connect(self, db_name=''):
        db_fp = self.data_fp + 'bian_f_data.db'
        db = SqliteDatabase(db_fp)
        db.connect()
        return db


class TradeInfo(Model):
    id = AutoField(primary_key=True)
    instrument = CharField()
    order_id = CharField()
    client_id = CharField()
    offset = CharField()
    side = CharField()
    volume = FloatField()
    price = FloatField()
    trading_day = CharField()
    trade_time = CharField()
    profit = FloatField()
    commission = FloatField()
    commission_asset = CharField()
    update_time = DateTimeField()

    class Meta:
        database = SqliteDatabaseManage().get_connect()
        table_name = 'trade_info'


class OrderInfo(Model):
    id = AutoField(primary_key=True)
    instrument = CharField()
    order_id = CharField()
    client_id = CharField()
    offset = CharField()
    side = CharField()
    volume = FloatField()
    price = FloatField()
    trading_day = CharField()
    status = CharField()
    trade_time = CharField()
    commission = FloatField()
    commission_asset = CharField()
    update_time = DateTimeField()

    class Meta:
        database = SqliteDatabaseManage().get_connect()
        table_name = 'order_info'


class AccountValue(Model):
    id = AutoField(primary_key=True)
    balance = FloatField()
    update_time = DateTimeField()

    class Meta:
        database = SqliteDatabaseManage().get_connect()
        table_name = 'account_value'


class TableLatestTime(Model):
    id = AutoField(primary_key=True)
    name = CharField()
    update_time = DateTimeField()

    class Meta:
        database = SqliteDatabaseManage().get_connect()
        table_name = 'tables_latest_update_time'


class Subtest(Model):
    id = AutoField(primary_key=True)
    balance = FloatField()
    update_time = DateTimeField()

    class Meta:
        database = SqliteDatabaseManage().get_connect()
        table_name = 'sub_table'


if __name__ == '__main__':
    # RtnTrade.create_table()
    AccountValue.create_table()
    # Subtest.create_table()
    # TableLatestTime.create_table()
    OrderInfo.create_table()
    TradeInfo.create_table()

    # save_data = Subtest(
    #     balance=1,
    #     update_time=datetime.now(),
    # )
    # save_data.save()

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


