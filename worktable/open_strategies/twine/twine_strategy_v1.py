"""
不使用vnpy_pro版
"""
import copy

from vnpy.app.cta_strategy import (
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
)

from vnpy.trader.constant import Interval, Direction, Offset
from vnpy.app.cta_strategy.template import CtaSignal

from vnpy.app.cta_strategy.template import CtaTemplate
from vnpy.trader.utility import ArrayManager


class Renko(object):
    """
    renko砖型图模块
    """

    def __init__(
            self,
            jump_price,
            symbol=None,
            exchange=None,
            gateway_name=None,
            chart=None,
            on_bar_callback=None,
    ):
        self.jump_price = jump_price
        self.symbol = symbol
        self.exchange = exchange
        self.gateway_name = gateway_name

        self.bar = None
        self.bars = ArrayManager(30)

        self.up = None
        self.down = None
        self.datetime = None
        self.volume = None

        self.KLine_chart_dict = chart
        self.on_bar_callback = on_bar_callback

    def update_tick(self, tick: TickData):
        pre_price = tick.last_price

        if self.up is None:
            self.up = pre_price
            self.down = pre_price
            self.datetime = tick.datetime
            self.volume = tick.volume

            self.bar = BarData(
                symbol=tick.symbol,
                exchange=tick.exchange,
                datetime=tick.datetime,
                gateway_name=tick.gateway_name,
                open_price=pre_price,
                high_price=pre_price,
                low_price=pre_price,
                close_price=pre_price,
            )

        self.update_pre_price(pre_price)
        self.datetime = tick.datetime
        self.volume += tick.volume

    def update_bar(self, bar: BarData):
        pre_price = bar.close_price
        if self.up is None:
            self.up = pre_price
            self.down = pre_price
            self.datetime = bar.datetime
            self.volume = bar.volume

            self.bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=bar.datetime,
                gateway_name=bar.gateway_name,
                open_price=pre_price,
                high_price=pre_price,
                low_price=pre_price,
                close_price=pre_price,
            )

        self.update_pre_price(pre_price)
        self.datetime = bar.datetime
        self.volume += bar.volume

    def update_pre_price(self, pre_price):
        if pre_price >= self.up + self.jump_price:
            self.down = self.up
            self.up += self.jump_price
            self.add_bar(True)

            self.init_bar(self.up)
            if pre_price > self.up:
                self.update_pre_price(pre_price)

        elif pre_price <= self.down - self.jump_price:
            self.up = self.down
            self.down -= self.jump_price
            self.add_bar(False)

            self.init_bar(self.down)
            if pre_price < self.down:
                self.update_pre_price(pre_price)

        else:
            self.bar.high_price = max(self.bar.high_price, pre_price)
            self.bar.low_price = min(self.bar.low_price, pre_price)

    def add_bar(self, up_or_down):
        """
        :param up_or_down: True:up, False:down
        """
        if up_or_down:
            self.bar.close_price = self.up
            self.bar.open_price = self.down
        else:
            self.bar.close_price = self.down
            self.bar.open_price = self.up

        self.bar.volume = self.volume
        self.bars.update_bar(self.bar)
        if self.on_bar_callback:
            self.on_bar_callback(self.bar)

        self.volume = 0
        self.bar.datetime = self.datetime

        if self.KLine_chart_dict is not None:
            self.KLine_chart_dict.update_bar(self.bar)

    def init_bar(self, pre_price):
        self.bar.high_price = pre_price
        self.bar.low_price = pre_price

    def save_data_to_csv(self):
        pass


class TwineSignal(CtaSignal):

    def __init__(
            self,
            main_self,
            time_period=15,
            chart=None,
            on_trade_signal1=None,
            on_trade_signal2=None,
            on_trade_signal3=None,
    ):
        """
        :param main_self:
        :param time_period: 时间周期
        :param chart: 画图工具
        :param on_trade_signal1: 1类买卖点回调函数
        :param on_trade_signal2: 2类买卖点回调函数
        :param on_trade_signal3: 3类买卖点回调函数
        """
        super().__init__()

        self.main_self = main_self
        self.on_trade_signal1 = on_trade_signal1
        self.on_trade_signal2 = on_trade_signal2
        self.on_trade_signal3 = on_trade_signal3

        self.bg_min = BarGenerator(self.on_bar, time_period, self.on_x_min, Interval.MINUTE)
        self.am = self.am_x_min = ArrayManager(5)

        self.past_bar = None
        self.past_high_price = None
        self.past_low_price = None
        self.base_high_price = None
        self.base_low_price = None
        self.base_signal = None  # 最小分型划，1上升 -1下降
        self.is_jump = False  # 是否跳空
        self.datetime_count = {}  # 为tick datetime去重设计

        self.brush_signal = None  # 当前笔信号，1上升笔，-1下降笔
        self.brush_signal_special1 = 0  # 用来处理分型出来前跳空的特殊情况  底1，顶2
        self.brush_signal_special2 = 0  # 用来处理分型出来后跳空的特殊情况
        self.brush_datetime_special = None  # 用来处理分型出来后跳空的特殊情况
        self.brush_past_datetime = None
        self.brush_bars = []  # 当前笔K线数
        self.brush_handle_bars = []  # 当前笔处理后K线数

        self.bars = []  # 基础分型总计K线数
        self.handle_bars = []  # 基础分型包含处理后K线数
        self.shape_dict = {}  # 分型列表
        self.brush_dict = {}  # 笔列表

        self.four_list = []
        self.center_shape_list = []  # 中枢分型列表
        self.center_list = []  # 分型列表
        self.center_signal = None  # 中枢首笔标志信号：1首笔上升，-1首笔下降
        self.center_signal_true = None  # 上中枢标志：1上升中枢，-1下降中枢
        self.center_list = []  # 分型列表

        # 1类买卖点
        self.trade_signal_num1 = {}
        self.trade_signal_num2 = {}
        self.trade_signal_num2_2 = {}
        self.trade_signal_num3 = {}

        self.brush_datetime_list = {}
        self.KLine_chart_dict = chart
        self.point_list = [] if chart is None else self.KLine_chart_dict.point_list
        self.area_list = [] if chart is None else self.KLine_chart_dict.area_list

    def on_tick(self, tick: TickData):
        self.bg_min.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.bg_min.update_bar(bar)

    def on_x_min(self, bar: BarData):
        self.am_x_min.update_bar(bar)
        if not self.am_x_min.inited:
            return

        if not self.base_high_price:
            self.base_high_price = bar.high_price
            self.past_high_price = bar.high_price
            self.base_low_price = bar.low_price
            self.past_low_price = bar.low_price

        bar.datetime = self.get_diff_datetime(bar.datetime)
        high_price = bar.high_price
        low_price = bar.low_price

        """分型处理"""
        # 上升
        if high_price > self.base_high_price and low_price > self.base_low_price:
            if self.brush_signal_special2 == -2 and self.is_jump:
                self.shape_dict[self.brush_datetime_special]["interval_down"] \
                    = self.shape_dict[self.brush_datetime_special]["interval_down_back"]
            self.brush_signal_special2 = 0

            if self.base_signal == 1 and low_price > self.base_high_price:
                self.is_jump = True

            self.handle_bars.append({
                "high_price": self.base_high_price,
                "low_price": self.base_low_price,
            })

            # 上升K线
            if self.base_signal == 1:
                pass

            # 底分型
            else:
                self.trade_signal = None
                self.brush_signal_special2 = 1
                self.brush_datetime_special = self.past_bar.datetime

                if self.brush_signal_special1 == 1:
                    _past_high_price = self.base_high_price
                else:
                    _past_high_price = self.past_high_price

                self.base_signal = 1
                self.shape_dict[self.past_bar.datetime] = {
                    "datetime": self.past_bar.datetime,
                    "signal": -1,
                    "value": self.base_low_price,
                    "interval_up": max(_past_high_price, self.base_high_price, high_price),
                    "interval_up_back": max(_past_high_price, self.base_high_price),
                    "interval_down": self.base_low_price,
                    "bar": copy.deepcopy(self.past_bar),
                    "bars": copy.deepcopy(self.bars),
                    "handle_bars": copy.deepcopy(self.handle_bars),
                }

                """画笔处理"""
                # 确认上顶分型，暂定当前底分型
                self.brush_handle_bars = self.brush_handle_bars[:] + self.handle_bars[:]
                if self.brush_signal is None:
                    self.brush_signal = -1

                else:
                    if self.brush_signal == 1:
                        interval_up = self.shape_dict[self.past_bar.datetime]["interval_up_back"]
                        interval_down = self.shape_dict[self.past_bar.datetime]["interval_down"]
                        past_interval_up = interval_up if self.brush_past_datetime is None else \
                            self.shape_dict[self.brush_past_datetime]["interval_up"]
                        past_interval_down = interval_down if self.brush_past_datetime is None else \
                            self.shape_dict[self.brush_past_datetime]["interval_down"]

                        if (self.is_jump or (len(self.brush_bars) >= 4 and len(self.brush_handle_bars) > 2)) \
                                and not (interval_up < past_interval_up and interval_down > past_interval_down) \
                                and not (interval_up > past_interval_up and interval_down < past_interval_down):

                            # 确认上顶分型
                            if self.brush_past_datetime:

                                self.brush_dict[self.brush_past_datetime] = self.shape_dict[self.brush_past_datetime]
                                if self.brush_past_datetime in self.brush_datetime_list.keys():
                                    self.brush_datetime_list[self.brush_past_datetime] = \
                                        self.shape_dict[self.brush_past_datetime]["value"]
                                    self.KLine_chart_dict.list_dict["signal"] = list(self.brush_datetime_list.values())

                                """中枢处理"""
                                self.list_fixed_length(self.four_list, self.brush_past_datetime, 4)
                                if self.center_signal is None:
                                    self.judge_center_signal()
                                else:
                                    zg, zd, gg, dd = self.get_center_info(is_skip_last=True)
                                    if self.shape_dict[self.brush_past_datetime]["value"] < zd:

                                        """交易信号判定：3卖"""
                                        if self.on_trade_signal3:
                                            self.on_trade_signal3("short", bar)
                                        current_value = self.brush_dict[self.brush_past_datetime]["value"]
                                        self.point_list.append({
                                            "name": "3卖", "color": "#53FA00",
                                            "datetime": self.brush_past_datetime, "y": current_value,
                                        })
                                        self.trade_signal_num3[self.brush_past_datetime] = {
                                            "datetime": bar.datetime,
                                            "value": bar.close_price,
                                            "shape": self.brush_past_datetime,
                                        }

                                        self.center_signal_true = -1
                                        self.center_list.append({
                                            "signal": self.center_signal_true,
                                            "shape_list": copy.deepcopy(self.center_shape_list),
                                            "out_length": self.shape_dict[self.center_shape_list[-2]]["value"]
                                                          - self.shape_dict[self.center_shape_list[-1]]["value"],
                                            "zg": zg, "zd": zd, "gg": gg, "dd": dd,
                                            "trade_signal_num1": copy.deepcopy(self.trade_signal_num1),
                                            "trade_signal_num2": copy.deepcopy(self.trade_signal_num2),
                                            "trade_signal_num2_2": copy.deepcopy(self.trade_signal_num2_2),
                                            "trade_signal_num3": copy.deepcopy(self.trade_signal_num3),
                                        })
                                        self.area_list.append({
                                            "x": (self.center_shape_list[0], self.center_shape_list[-2]),
                                            "y": (zg, zd),
                                            "border_color": "#ef232a" if self.center_signal_true == 1 else "#14b143"
                                        })
                                        self.center_signal = None
                                        self.trade_signal_num1 = {}
                                        self.trade_signal_num2 = {}
                                        self.trade_signal_num2_2 = {}
                                        self.trade_signal_num3 = {}

                                    else:
                                        self.center_shape_list.append(self.brush_past_datetime)

                                """交易信号判定"""
                                if self.center_signal is not None:
                                    zg, zd, gg, dd = self.get_center_info()
                                    brush_dict_keys = list(self.brush_dict.keys())
                                    trade_signal_shape = self.brush_dict[self.brush_past_datetime]
                                    trade_signal_shape2 = self.brush_dict[brush_dict_keys[-2]]
                                    current_value = trade_signal_shape["value"]

                                    if self.center_signal_true == 1:
                                        """1卖"""
                                        compare_length = current_value - trade_signal_shape2["value"]
                                        if compare_length < self.center_list[-1]["out_length"] and current_value >= gg:
                                            if self.on_trade_signal1:
                                                self.on_trade_signal1("short", bar)
                                            self.point_list.append({
                                                "name": "1卖", "color": "#336600",
                                                "datetime": self.brush_past_datetime, "y": current_value,
                                            })
                                            self.trade_signal_num1[self.brush_past_datetime] = {
                                                "trade_datetime": bar.datetime,
                                                "trade_value": bar.close_price,
                                                "signal_datetime": self.brush_past_datetime,
                                            }

                                        """2卖"""
                                        trade_signal_num1_keys = list(self.trade_signal_num1.keys())
                                        trade_signal_num2_keys = list(self.trade_signal_num2.keys())
                                        if len(trade_signal_num1_keys) - len(trade_signal_num2_keys) == 1 \
                                                and self.brush_past_datetime not in trade_signal_num1_keys \
                                                and current_value < self.brush_dict[trade_signal_num1_keys[-1]]["value"]:
                                            if self.on_trade_signal2:
                                                self.on_trade_signal2("short", bar)
                                            self.point_list.append({
                                                "name": "2卖", "color": "#4D9900",
                                                "datetime": self.brush_past_datetime, "y": current_value,
                                            })
                                            self.trade_signal_num2[self.brush_past_datetime] = {
                                                "datetime": bar.datetime,
                                                "value": bar.close_price,
                                                "shape": self.brush_past_datetime,
                                            }

                            self.brush_signal = -1
                            self.brush_past_datetime = self.past_bar.datetime
                            self.brush_bars = []
                            self.brush_handle_bars = []

                        else:
                            pass
                    else:
                        if self.brush_past_datetime is not None \
                                and self.base_low_price < self.shape_dict[self.brush_past_datetime]["value"]:
                            self.brush_past_datetime = self.past_bar.datetime
                            self.brush_bars = []
                            self.brush_handle_bars = []

                if low_price > self.base_high_price:
                    self.is_jump = True
                else:
                    self.is_jump = False

                self.bars = []
                self.handle_bars = []

            self.past_high_price = self.base_high_price
            self.past_low_price = self.base_low_price
            self.base_high_price = high_price
            self.base_low_price = low_price
            self.brush_signal_special1 = 0

        # 下降
        elif high_price < self.base_high_price and low_price < self.base_low_price:
            if self.brush_signal_special2 == -1 and self.is_jump:
                self.shape_dict[self.brush_datetime_special]["interval_up"] \
                    = self.shape_dict[self.brush_datetime_special]["interval_up_back"]
            self.brush_signal_special2 = 0

            if self.base_signal == -1 and high_price < self.base_low_price:
                self.is_jump = True

            self.handle_bars.append({
                "high_price": self.base_high_price,
                "low_price": self.base_low_price,
            })

            # 顶分型
            if self.base_signal == 1:
                self.trade_signal = None
                self.brush_signal_special2 = 2
                self.brush_datetime_special = self.past_bar.datetime

                if self.brush_signal_special1 == 2:
                    _past_low_price = self.base_low_price
                else:
                    _past_low_price = self.past_low_price

                self.base_signal = -1
                self.shape_dict[self.past_bar.datetime] = {
                    "datetime": self.past_bar.datetime,
                    "signal": 1,
                    "value": self.base_high_price,
                    "interval_up": self.base_high_price,
                    "interval_down": min(_past_low_price, self.base_low_price, low_price),
                    "interval_down_back": min(_past_low_price, self.base_low_price),
                    "bar": copy.deepcopy(self.past_bar),
                    "bars": copy.deepcopy(self.bars),
                    "handle_bars": copy.deepcopy(self.handle_bars),
                }

                """画笔处理"""
                # 确认上底分型，暂定当前顶分型
                self.brush_handle_bars = self.brush_handle_bars[:] + self.handle_bars[:]
                if self.brush_signal is None:
                    self.brush_signal = 1
                    self.brush_past_datetime = self.past_bar.datetime

                else:
                    if self.brush_signal == 1:
                        if self.brush_past_datetime is not None \
                                and self.base_high_price > self.shape_dict[self.brush_past_datetime]["value"]:
                            self.brush_past_datetime = self.past_bar.datetime
                            self.brush_bars = []
                            self.brush_handle_bars = []

                    else:
                        interval_up = self.shape_dict[self.past_bar.datetime]["interval_up"]
                        interval_down = self.shape_dict[self.past_bar.datetime]["interval_down_back"]
                        past_interval_up = interval_up if self.brush_past_datetime is None else \
                            self.shape_dict[self.brush_past_datetime]["interval_up"]
                        past_interval_down = interval_down if self.brush_past_datetime is None else \
                            self.shape_dict[self.brush_past_datetime]["interval_down"]

                        if (self.is_jump or (len(self.brush_bars) >= 4 and len(self.brush_handle_bars) > 2)) \
                                and not (interval_up < past_interval_up and interval_down > past_interval_down) \
                                and not (interval_up > past_interval_up and interval_down < past_interval_down):

                            if self.brush_past_datetime:

                                self.brush_dict[self.brush_past_datetime] = self.shape_dict[self.brush_past_datetime]
                                if self.brush_past_datetime in self.brush_datetime_list.keys():
                                    self.brush_datetime_list[self.brush_past_datetime] \
                                        = self.shape_dict[self.brush_past_datetime]["value"]
                                    self.KLine_chart_dict.list_dict["signal"] = list(self.brush_datetime_list.values())

                                """中枢处理"""
                                self.list_fixed_length(self.four_list, self.brush_past_datetime, 4)
                                if self.center_signal is None:
                                    self.judge_center_signal()
                                else:
                                    zg, zd, gg, dd = self.get_center_info(is_skip_last=True)
                                    if self.shape_dict[self.brush_past_datetime]["value"] > zg:

                                        """交易信号判定：3买"""
                                        if self.on_trade_signal3:
                                            self.on_trade_signal3("long", bar)
                                        current_value = self.brush_dict[self.brush_past_datetime]["value"]
                                        self.point_list.append({
                                            "name": "3买", "color": "#FF4D82",
                                            "datetime": self.brush_past_datetime, "y": current_value,
                                        })
                                        self.trade_signal_num3[self.brush_past_datetime] = {
                                            "datetime": bar.datetime,
                                            "value": bar.close_price,
                                            "shape": self.brush_past_datetime,
                                        }

                                        self.center_signal_true = 1
                                        self.center_list.append({
                                            "signal": self.center_signal_true,
                                            "shape_list": copy.deepcopy(self.center_shape_list),
                                            "out_length": self.shape_dict[self.center_shape_list[-1]]["value"]
                                                          - self.shape_dict[self.center_shape_list[-2]]["value"],
                                            "zg": zg, "zd": zd, "gg": gg, "dd": dd,
                                            "trade_signal_num1": copy.deepcopy(self.trade_signal_num1),
                                            "trade_signal_num2": copy.deepcopy(self.trade_signal_num2),
                                            "trade_signal_num2_2": copy.deepcopy(self.trade_signal_num2_2),
                                            "trade_signal_num3": copy.deepcopy(self.trade_signal_num3),
                                        })
                                        self.area_list.append({
                                            "x": (self.center_shape_list[0], self.center_shape_list[-2]),
                                            "y": (zg, zd),
                                            "border_color": "#ef232a" if self.center_signal_true == 1 else "#14b143"
                                        })
                                        self.center_signal = None
                                        self.trade_signal_num1 = {}
                                        self.trade_signal_num2 = {}
                                        self.trade_signal_num2_2 = {}
                                        self.trade_signal_num3 = {}

                                    else:
                                        self.center_shape_list.append(self.brush_past_datetime)

                                """交易信号判定 59B300 00F000 2EFF2E"""
                                if self.center_signal is not None:
                                    zg, zd, gg, dd = self.get_center_info()
                                    brush_dict_keys = list(self.brush_dict.keys())
                                    trade_signal_shape = self.brush_dict[self.brush_past_datetime]
                                    trade_signal_shape2 = self.brush_dict[brush_dict_keys[-2]]
                                    current_value = trade_signal_shape["value"]

                                    if self.center_signal_true == -1:
                                        """1买"""
                                        compare_length = trade_signal_shape2["value"] - current_value
                                        if compare_length < self.center_list[-1]["out_length"] and current_value <= dd:
                                            if self.on_trade_signal1:
                                                self.on_trade_signal1("long", bar)
                                            self.point_list.append({
                                                "name": "1买", "color": "#CC003D",
                                                "datetime": self.brush_past_datetime, "y": current_value,
                                            })
                                            self.trade_signal_num1[self.brush_past_datetime] = {
                                                "datetime": bar.datetime,
                                                "value": bar.close_price,
                                                "shape": self.brush_past_datetime,
                                            }

                                        """2买"""
                                        trade_signal_num1_keys = list(self.trade_signal_num1.keys())
                                        trade_signal_num2_keys = list(self.trade_signal_num2.keys())
                                        if len(trade_signal_num1_keys) - len(trade_signal_num2_keys) == 1 \
                                                and self.brush_past_datetime not in trade_signal_num1_keys \
                                                and current_value > self.brush_dict[trade_signal_num1_keys[-1]]["value"]:
                                            if self.on_trade_signal2:
                                                self.on_trade_signal2("long", bar)
                                            self.point_list.append({
                                                "name": "2买", "color": "#FF3B0A",
                                                "datetime": self.brush_past_datetime, "y": current_value,
                                            })
                                            self.trade_signal_num2[self.brush_past_datetime] = {
                                                "datetime": bar.datetime,
                                                "value": bar.close_price,
                                                "shape": self.brush_past_datetime,
                                            }

                            self.brush_signal = 1
                            self.brush_past_datetime = self.past_bar.datetime
                            self.brush_bars = []
                            self.brush_handle_bars = []
                        else:
                            pass

                if high_price < self.base_low_price:
                    self.is_jump = True
                else:
                    self.is_jump = False

                self.bars = []
                self.handle_bars = []

            # 下降K线
            else:
                pass

            self.past_high_price = self.base_high_price
            self.past_low_price = self.base_low_price
            self.base_high_price = high_price
            self.base_low_price = low_price
            self.brush_signal_special1 = 0

        # 左包含
        elif high_price <= self.base_high_price and low_price >= self.base_low_price:
            if self.base_signal == 1:
                self.base_high_price = max(self.base_high_price, high_price)
                self.base_low_price = max(self.base_low_price, low_price)
            else:
                self.base_high_price = min(self.base_high_price, high_price)
                self.base_low_price = min(self.base_low_price, low_price)

            if self.base_signal == 1 and self.base_low_price > self.past_high_price:
                self.is_jump = True
                self.brush_signal_special1 = 2
            elif self.base_signal == -1 and self.base_high_price < self.past_low_price:
                self.is_jump = True
                self.brush_signal_special1 = 1

            if self.brush_signal_special2 > 0:
                self.brush_signal_special2 = -self.brush_signal_special2

        # 右包含
        elif high_price >= self.base_high_price and low_price <= self.base_low_price:
            if self.base_signal == 1:
                self.base_high_price = max(self.base_high_price, high_price)
                self.base_low_price = max(self.base_low_price, low_price)
            else:
                self.base_high_price = min(self.base_high_price, high_price)
                self.base_low_price = min(self.base_low_price, low_price)

            if self.base_signal == 1 and self.base_low_price > self.past_high_price:
                self.is_jump = True
                self.brush_signal_special1 = 2
            elif self.base_signal == -1 and self.base_high_price < self.past_low_price:
                self.is_jump = True
                self.brush_signal_special1 = 1

            if self.brush_signal_special2 > 0:
                self.brush_signal_special2 = - self.brush_signal_special2

        self.bars.append(copy.deepcopy(bar))
        self.brush_bars.append(copy.deepcopy(bar))

        if self.main_self.trading and self.KLine_chart_dict is not None and self.past_bar is not None:
            self.brush_datetime_list[self.past_bar.datetime] = None

            self.KLine_chart_dict.update_bar(
                self.past_bar,
                signal=None,
                datetime_str=self.past_bar.datetime,
                # signal=signal,
            )

        self.past_bar = copy.deepcopy(bar)

    def judge_center_signal(self):
        if len(self.four_list) == 4:
            shape_0 = self.shape_dict[self.four_list[0]]
            shape_3 = self.shape_dict[self.four_list[3]]
            if shape_0["signal"] == 1 and (self.center_signal_true == 1 or self.center_signal_true is None):
                if shape_3["value"] < shape_0["value"]:
                    self.center_signal = 1
                    self.center_shape_list = copy.deepcopy(self.four_list)

            if shape_0["signal"] == -1 and (self.center_signal_true == -1 or self.center_signal_true is None):
                if shape_0["value"] < shape_3["value"]:
                    self.center_signal = -1
                    self.center_shape_list = copy.deepcopy(self.four_list)

    def get_center_info(self, value_type=1, is_skip_last=False):
        """获取当前中枢关键参数
        is_skip_last : 是否跳过最后一条
        """
        zg = {}
        zd = {}
        gg = {}
        dd = {}

        count = 0
        shape_lenght = len(self.center_shape_list)
        for _datetime in self.center_shape_list:
            count += 1

            if shape_lenght - count <= 1 and is_skip_last:
                continue

            if self.shape_dict[_datetime]["signal"] == 1:
                if not gg or self.shape_dict[_datetime]["value"] > gg["value"]:
                    gg = self.shape_dict[_datetime]
                if count <= 4:
                    if not zg or self.shape_dict[_datetime]["value"] < zg["value"]:
                        zg = self.shape_dict[_datetime]

            else:
                if not dd or self.shape_dict[_datetime]["value"] < dd["value"]:
                    dd = self.shape_dict[_datetime]
                if count <= 4:
                    if not zd or self.shape_dict[_datetime]["value"] > zd["value"]:
                        zd = self.shape_dict[_datetime]

        if value_type == 1:
            return zg.get("value", None), zd.get("value", None), gg.get("value", None), dd.get("value", None)
        else:
            return zg, zd, gg, dd

    @staticmethod
    def list_fixed_length(_list, item, fixed_length=10):
        _list.append(item)

        if len(_list) > fixed_length:
            _list.pop(0)

    def get_diff_datetime(self, datetime, is_get_last=False):
        datetime_str = str(datetime)

        if not is_get_last:
            datetime_count = self.datetime_count.get(datetime_str, 0) + 1
            self.datetime_count[datetime_str] = datetime_count
        else:
            datetime_count = self.datetime_count.get(datetime_str, 1)

        if datetime_count == 1:
            return datetime_str
        else:
            return datetime_str + "_" + str(datetime_count)


class TwineStrategy(CtaTemplate):
    """
    """
    author = "jin"

    fixed_size = 1

    parameters = ["fixed_size"]
    variables = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.twine_signal = TwineSignal(
            main_self=self,
            time_period=30,
            chart=None,
            on_trade_signal1=self.on_trade_signal1,
            on_trade_signal2=self.on_trade_signal2,
            on_trade_signal3=self.on_trade_signal3,
        )
        self.renko = Renko(
            jump_price=3,
            on_bar_callback=self.twine_signal.on_x_min
        )

    def on_init(self):
        self.write_log("策略初始化")
        self.load_bar(1)
        # self.load_tick(1)

    def on_start(self):
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        super().on_tick(tick)
        # tick回测和实盘
        self.twine_signal.bg_min.update_tick(tick)  # 不使用砖图
        # self.renko.update_tick(tick)  # 使用砖图

    def on_bar(self, bar: BarData):
        super().on_bar(bar)
        # 分钟回测
        self.twine_signal.bg_min.update_bar(bar)  # 不使用砖图
        # self.renko.update_bar(bar)  # 使用砖图

    def on_trade_signal1(self, direction, bar: BarData):
        if direction == "long":
            print(f"{bar.datetime}：买1")
        else:
            print(f"{bar.datetime}：卖1")

    def on_trade_signal2(self, direction, bar: BarData):
        if direction == "long":
            print(f"{bar.datetime}：买2")
        else:
            print(f"{bar.datetime}：卖2")

    def on_trade_signal3(self, direction, bar: BarData):
        if direction == "long":
            print(f"{bar.datetime}：买3")
        else:
            print(f"{bar.datetime}：卖3")

    def on_order(self, order: OrderData):
        super().on_order(order)

    def on_trade(self, trade: TradeData):
        super().on_trade(trade)

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
