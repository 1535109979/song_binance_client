
import sys
import math
import numpy
from functools import lru_cache
from decimal import Decimal, ROUND_DOWN, ROUND_UP


def get_default_if_null(value, default=0):
    """ 判断是否 None 或 NAN """
    return default if (value is None or numpy.isnan(value)) else value


def valid_inf(value, default=0):
    """ 重置无效值 1.79769313486232e+308 ==> 0 """
    if value is None \
            or value in (numpy.inf, -numpy.inf) \
            or value > sys.maxsize \
            or value == sys.float_info.max:
        value = default
    return value


def convert_to_str(value, default_value=None) -> str:
    return str(value) if value is not None else default_value


def convert_to_int(value, default_value=None) -> int:
    return int(value) if value is not None else default_value


def convert_to_float(value, default_value=None) -> float:
    return float(value) if value is not None else default_value


def convert_decimal_exp_str(value, default_value=None) -> str:
    # 去掉小数位后面的0  如：1.0 => 1; 0.000100 => 0.001
    return '{:g}'.format(value) if value else default_value


def quantize_decimal(value, exp="1e-08", round_down=True) -> Decimal:
    if not value:
        return Decimal(0)

    rounding = None
    if round_down is not None:
        if round_down is True:
            rounding = ROUND_DOWN
        elif round_down is False:
            rounding = ROUND_UP
        else:
            rounding = round_down
    return quantize_rounding_decimal(value=value, exp=exp, rounding=rounding)


def quantize_rounding_decimal(value, exp="1e-08", rounding=None) -> Decimal:
    if not value:
        return Decimal(0)

    value = Decimal(str(value))
    step = Decimal(str(exp))
    if step <= 1:
        return value.quantize(step, rounding=rounding)
    else:
        # 针对整数的取整, 默认向下取整 (return value // step * step 也可以)
        r = value % step
        if r and rounding and rounding.endswith("_UP"):
            value += step
        return value - r


def get_precision_number(number, precision=8, round_down=False, default=0) -> float:
    if not number:
        return default

    number = float(number)
    precision = int(precision)
    if round_down:
        number -= get_precision_min_value(precision) / 2
    return number if precision is None or precision < 0 else round(number, int(precision))


@lru_cache(maxsize=10)
def get_precision_min_value(precision=8) -> float:
    return math.pow(0.1, int(precision))


def get_precision_str(number, precision=8) -> str:
    """科学计数法转换为指定小数位数"""
    if number is not None:
        return ("{:.%sf}" % precision).format(float(number))


def get_precision_float(number, precision=8) -> float:
    """科学计数法转换为指定小数位"""
    number = get_precision_str(number=number, precision=precision)
    if number is not None:
        return float(number)
