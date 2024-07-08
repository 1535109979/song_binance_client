import functools
import time
from threading import RLock


def func_synchronized(func):
    func.__lock__ = RLock()

    @functools.wraps(func)
    def lock_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return lock_func


def instance_synchronized(func):
    """ 对象锁 """

    @functools.wraps(func)
    def lock_func(self, *args, **kwargs):
        if not hasattr(self, "__instance_lock__"):
            self.__instance_lock__ = RLock()
        with self.__instance_lock__:
            return func(self, *args, **kwargs)

    return lock_func


def exec_limiter(interval_seconds=1, need_log=True):
    """
    限流器
    :param interval_seconds:    间隔多少秒才能调用一次
    """

    def decorator(func):
        func.__exec_timestamp__ = 0
        func.__exec_lock__ = RLock()

        @functools.wraps(func)
        def wrapper(*args, **kw):
            with func.__exec_lock__:
                exec_timestamp = time.time()
                interval = exec_timestamp - func.__exec_timestamp__
                if interval <= interval_seconds:
                    return
                func.__exec_timestamp__ = exec_timestamp
                return func(*args, **kw)

        return wrapper

    return decorator