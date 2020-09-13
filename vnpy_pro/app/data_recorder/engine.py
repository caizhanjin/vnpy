from vnpy.trader.constant import Exchange
from vnpy.trader.object import BarData, TickData
from datetime import time
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.utility import extract_vt_symbol


from vnpy.app.data_recorder.engine import RecorderEngine


class RecorderEnginePro(RecorderEngine):

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine)
        # 非交易时间
        self.drop_start = time(3, 15)
        self.drop_end = time(8, 45)

        # 大连、上海、郑州交易所，小节休息
        self.rest_start = time(10, 15)
        self.rest_end = time(10, 30)

    def record_tick(self, tick: TickData):
        """
        抛弃非交易时间校验数据
        """
        tick_time = tick.datetime.time()
        if not self.is_trading(tick.vt_symbol, tick_time):
            return

        super().record_tick(tick)

    def record_bar(self, bar: BarData):
        """
        抛弃非交易时间校验数据
        """
        bar_time = bar.datetime.time()
        if not self.is_trading(bar.vt_symbol, bar_time):
            return

        super().record_bar(bar)

    def is_trading(self, vt_symbol, current_time) -> bool:
        """
        交易时间，过滤校验Tick
        """
        symbol, exchange = extract_vt_symbol(vt_symbol)

        if self.drop_start <= current_time < self.drop_end:
            return False
        if exchange in [Exchange.DCE, Exchange.SHFE, Exchange.CZCE]:
            if self.rest_start <= current_time < self.rest_end:
                return False
        return True

