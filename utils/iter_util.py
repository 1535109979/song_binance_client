from collections import defaultdict
from typing import Iterable


def get_iter(obj):
    """
    判断是否是可迭代类型，如果不是则转为list
    :param obj: 对象
    :return:    可迭代对象
    """
    if obj is None:
        return []
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [obj]
    if isinstance(obj, Iterable):
        return list(obj)
    return [obj]


def group_by_key(obj_list, key_func):
    if obj_list:
        dd = defaultdict(list)
        for o in get_iter(obj_list):
            dd[key_func(o)].append(o)
        return dd