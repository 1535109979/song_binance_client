import functools
import logging
import traceback
from logging.handlers import TimedRotatingFileHandler

from song_binance_client.utils.configs import Configs
from song_binance_client.utils.dingding import Dingding

logger = logging.getLogger('common_exception')
logger.setLevel(logging.DEBUG)
log_fp = Configs.root_fp + f'song_binance_client/logs/common_exception.log'
handler = TimedRotatingFileHandler(log_fp, when="midnight", interval=1, backupCount=7)
handler.suffix = "%Y-%m-%d.log"  # 设置滚动后文件的后缀
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def common_exception(log_flag: bool = None):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                traceback.print_exc()
                log_msg = "!!!error= %s !!! %s" % (e, kwargs)
                logger.exception(log_msg)
                if log_flag:
                    logger.info(log_msg)
                    Dingding.send_msg(log_msg, isatall=True)

        return wrapper

    return decorator

