from functools import wraps
from time import perf_counter
from .logger import log


def timed(func):
    """
    装饰器：记录函数执行时间，日志 INFO 输出。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = perf_counter()
        res = func(*args, **kwargs)
        elapsed = perf_counter() - t0
        log.info("%s() took %.3f s", func.__name__, elapsed)
        return res
    return wrapper
