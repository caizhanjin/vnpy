from dataclasses import dataclass
from datetime import datetime

from vnpy.trader.constant import (
    Exchange, Interval
)
from vnpy.trader.object import BaseData


@dataclass
class BarData(BaseData):
    """
    Candlestick bar data of a certain trading period.
    """

    symbol: str
    exchange: Exchange
    datetime: datetime  # bar的开始时间
    trading_day: str = ""   # JinAdd: '%Y-%m-%d'

    interval: Interval = None  # constant.py Internal 1m, 1h, 1d, 1w .etc
    volume: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
