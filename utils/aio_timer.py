import asyncio
import logging
import threading

from a_songbo.binance_client.utils import thread
from a_songbo.binance_client.utils.lock import func_synchronized
from a_songbo.binance_client.utils.thread import COMMON_HUGE_POOL

logger = logging.getLogger('bi_future_ts')

def start_loop(loop):
    try:
        logger.info("<start> %s", loop)
        asyncio.set_event_loop(loop)
        loop.run_forever()
    except Exception as e:
        logger.exception(f"!!! {e} !!!")
    finally:
        loop.close()


class AioTimer(object):
    """
    使用协程实现的定时器
    """
    loop = None
    timer_thread = None

    @classmethod
    def new_timer(cls, _delay, _func, _daemonic=True, *args, **kwargs):
        if not _func or _delay is None or _delay < 0:
            logger.warning("missing delay or function! function=%s delay=%s",
                           _func, _delay)
            return

        cls._init(daemonic=_daemonic)
        task = TimerTask(_delay=_delay, _func=_func, *args, **kwargs)
        return asyncio.run_coroutine_threadsafe(cls._run(task=task), cls.loop)

    @classmethod
    async def _run(cls, task):
        try:
            if task.delay:
                await asyncio.sleep(task.delay)

            # logger.debug("<run> TimerTask.%s delay=%s function=%s",
            #              task.__hash__(), task.delay, task.function)
            thread.submit(_executor=COMMON_HUGE_POOL, _fn=task.call_func)
        except Exception as e:
            logger.exception(f"!!! {e} !!!")

    @classmethod
    @func_synchronized
    def _init(cls, daemonic=True):
        if not cls.loop:
            cls.loop = asyncio.new_event_loop()

        if not cls.timer_thread:
            cls.timer_thread = threading.Thread(
                target=start_loop, args=(cls.loop,), name="Timer", daemon=daemonic)
            cls.timer_thread.start()
            # logger.info("<start> %s", cls.timer_thread)


class TimerTask(object):

    def __init__(self, _delay, _func, *args, **kwargs):
        self.delay = _delay
        self.function = _func
        self.args = args
        self.kwargs = kwargs
        # logger.debug("<init> TimerTask.%s delay=%s function=%s",
        #              self.__hash__(), self.delay, self.function)

    def call_func(self):
        return self.function(*self.args, **self.kwargs)


