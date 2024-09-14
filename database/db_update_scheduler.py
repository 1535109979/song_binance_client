import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from peewee import fn

from song_binance_client.database.bian_f_dbm import TableLatestTime, Subtest
from song_binance_client.utils.configs import Configs


class DbUpdatedScheduler:
    def __init__(self):
        self.create_logger()
        self.scheduler = BlockingScheduler()
        self.tables_latest_update_time = dict()
        self.load_tables_latest_update_time()

    def start(self):
        self.scheduler.add_job(self.check_tables_update, 'interval', seconds=3)
        self.scheduler.start()

    def check_tables_update(self):
        max_update_time = Subtest.select(fn.MAX(Subtest.update_time)).scalar()

        print(max_update_time)

    def load_tables_latest_update_time(self):
        dates = TableLatestTime.select()
        for data in dates:
            print(data)

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


if __name__ == '__main__':
    DbUpdatedScheduler().start()
