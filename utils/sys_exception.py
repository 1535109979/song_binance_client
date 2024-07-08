import functools
import logging
import traceback

from a_songbo.binance_client.utils.dingding import Dingding

logger = logging.getLogger('bi_future_ts')


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

