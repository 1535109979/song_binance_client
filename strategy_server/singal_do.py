from dataclasses import dataclass, field

from song_binance_client.utils.exchange_enum import Direction, OffsetFlag, OrderPriceType


@dataclass
class Signal:
    instrument: str
    offset_flag: OffsetFlag
    direction: Direction
    order_price_type: OrderPriceType
    price: str
    volume: str

