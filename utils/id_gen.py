from abc import ABC

import ulid

from a_songbo.binance_client.utils import iter_util


class IdGenerator(ABC):
    ENCODING = "utf-8"
    def get_id(self, routing_key=None):
        raise NotImplementedError()


class UlIdGenerator(IdGenerator):

    def get_id(self, routing_key=None):
        return self.get_default_id()

    @classmethod
    def get_default_id(cls, uni_keys=None, max_len=24):
        if uni_keys:
            ks = "".join(map(str, iter_util.get_iter(uni_keys)))\
                .replace('-', '').replace('_', '').replace('.', '')
            return "{}{}".format(ks, ulid.ulid()[2:])[:max_len]
        else:
            return ulid.ulid()[-max_len:]



