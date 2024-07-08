import functools
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

COMMON_HUGE_POOL = ThreadPoolExecutor(max_workers=256, thread_name_prefix="Common")
SINGLETON_POOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix="Single")


def submit(_executor, _fn, _done_callback=None, _args=None, _kwargs=None):
    """ 添加任务进线程池并添加回调 """
    if _kwargs is None:
        _kwargs = dict()
    if _args is None:
        future = _executor.submit(_fn, **_kwargs)
    else:
        future = _executor.submit(_fn, *_args, **_kwargs)
    return future

def run_in_executor(func):
    """ 在线程池中异步执行 """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        submit(_executor=COMMON_HUGE_POOL, _fn=func, _args=args, _kwargs=kwargs)

    return wrapper


def run_in_singleton(func):
    """ 在单例线程池中执行 """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        submit(_executor=SINGLETON_POOL, _fn=func, _args=args, _kwargs=kwargs)

    return wrapper


def run_in_new_thread(daemon=False, thread_name=None):
    """ 新建线程异步执行 (线程过多时效率很低，谨慎使用) """

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if thread_name:
                t = Thread(target=func, args=args, kwargs=kwargs, name=str(thread_name),
                           daemon=daemon)
            else:
                t = Thread(target=func, args=args, kwargs=kwargs, daemon=daemon)
            t.start()
        return wrapper
    return decorator