from datetime import datetime
import pandas as pd
from pandas import DataFrame
import os
from functools import wraps
import logging
import pyecharts.options as opts
from pyecharts.charts import Line, Grid, Bar

from vnpy.app.cta_strategy.backtesting import BacktestingEngine
from vnpy.trader.constant import (Direction, Offset, Exchange,
                                  Interval, Status)
from vnpy.app.cta_strategy.base import BacktestingMode
from vnpy.trader.utility import get_file_logger


def add_log_path_wrapper(func):
    """
    回测结果路径获取装饰器
    """
    @wraps(func)
    def inner(self, *args, **kwargs):
        if not os.path.exists(self.root_log_path):
            os.mkdir(self.root_log_path)
        if not self.strategy_log_path:
            self.strategy_log_path = os.path.join(self.root_log_path, self.strategy.strategy_name)
            if not os.path.exists(self.strategy_log_path):
                os.mkdir(self.strategy_log_path)
        if not self.backtest_log_path:
            backtest_log_name = str(datetime.now().strftime("%Y%m%d%H%M%S")) + "_" + \
                                self.symbol + "_" + \
                                self.interval.value + "_" + \
                                self.start.strftime("%Y%m%d") + "_" + \
                                self.end.strftime("%Y%m%d")
            self.backtest_log_path = os.path.join(self.strategy_log_path, backtest_log_name)

            if not os.path.exists(self.backtest_log_path):
                os.mkdir(self.backtest_log_path)

        return func(self, *args, **kwargs)
    return inner


class BacktestingEnginePro(BacktestingEngine):

    def __init__(self):
        super().__init__()

        self.root_log_path = ""
        self.strategy_log_path = ""
        self.backtest_log_path = ""
        self.output_list = []

    def set_parameters(
        self,
        vt_symbol: str,
        interval: Interval,
        start: datetime,
        rate: float,
        slippage: float,
        size: float,
        pricetick: float,
        capital: int = 0,
        end: datetime = None,
        mode: BacktestingMode = BacktestingMode.BAR,
        inverse: bool = False,
        log_path: str = None
    ):
        """"""
        super().set_parameters(
            vt_symbol,
            interval,
            start,
            rate,
            slippage,
            size,
            pricetick,
            capital,
            end,
            mode,
            inverse
        )
        self.root_log_path = os.path.join(log_path, "backtest_result")

    def export_all(self):
        self.export_daily_results()
        self.export_trades()
        self.export_orders()
        self.save_output()
        self.save_daily_chart()
        self.save_k_line_chart()

    @add_log_path_wrapper
    def export_daily_results(self):
        # 导出daily_results到csv
        if self.daily_df is None:
            return
        self.daily_df.to_csv(os.path.join(self.backtest_log_path, "daily_results.csv"), encoding="utf_8_sig")

    @add_log_path_wrapper
    def export_trades(self):
        # 导出trades到csv
        trades_results = self.get_all_trades()
        trades_results = [
            [
                i.datetime,
                i.direction.value,
                i.exchange.value,
                i.gateway_name,
                i.offset.value,
                i.orderid,
                i.price,
                i.symbol,
                i.time,
                i.tradeid,
                i.volume,
                i.vt_orderid,
                i.vt_symbol,
                i.vt_tradeid,
            ]
            for i in trades_results
        ]
        trades_results_df = pd.DataFrame(
            trades_results,
            columns=["datetime", "direction", "exchange", "gateway_name", "offset", "orderid", "price",
                     "symbol", "time", "tradeid", "volume", "vt_orderid", "vt_symbol", "vt_tradeid"]
        ).set_index("datetime")

        trades_results_df.to_csv(os.path.join(self.backtest_log_path, "trades.csv"), encoding="utf_8_sig")

    @add_log_path_wrapper
    def export_orders(self):
        # 导出orders到csv
        trades_orders = self.get_all_orders()
        trades_orders = [
            [
                i.datetime,
                i.direction.value,
                i.exchange.value,
                i.gateway_name,
                i.offset.value,
                i.orderid,
                i.price,
                i.status.value,
                i.symbol,
                i.time,
                i.traded,
                i.type.value,
                i.volume,
                i.vt_orderid,
                i.vt_symbol,
            ]
            for i in trades_orders
        ]
        trades_orders_df = pd.DataFrame(
            trades_orders,
            columns=["datetime", "direction", "exchange", "gateway_name", "offset", "orderid", "price",
                     "status", "symbol", "time", "traded", "type", "volume", "vt_orderid", "vt_symbol"]
        ).set_index("datetime")

        trades_orders_df.to_csv(os.path.join(self.backtest_log_path, "orders.csv"), encoding="utf_8_sig")

    @add_log_path_wrapper
    def save_output(self):
        """保存输出日志"""
        logger = get_file_logger(os.path.join(self.backtest_log_path, "output.log"))
        logger.setLevel(logging.INFO)
        for i in self.output_list:
            logger.info(i)

    def output(self, msg):
        super().output(msg)

        self.output_list.append(msg)

    @add_log_path_wrapper
    def save_daily_chart(self):
        if self.daily_df is None:
            return

        date_list = self.daily_df.index.values.tolist()
        balance_list = self.daily_df.balance.values.tolist()
        draw_down_list = self.daily_df.drawdown.values.tolist()
        net_pnl_list = self.daily_df.net_pnl.values.tolist()

        line1 = (
            Line()
            .add_xaxis(xaxis_data=date_list)
            .add_yaxis(
                series_name="Balance",
                y_axis=balance_list,
                label_opts=opts.LabelOpts(is_show=False),
                linestyle_opts=opts.LineStyleOpts(width=2),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="回测资金曲线", pos_left="center"),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                    background_color="rgba(245, 245, 245, 0.8)",
                    border_width=1,
                    border_color="#ccc",
                    textstyle_opts=opts.TextStyleOpts(color="#000"),
                ),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    boundary_gap=False,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=True),
                ),
                legend_opts=opts.LegendOpts(pos_left="1%"),
                yaxis_opts=opts.AxisOpts(
                    type_="value",
                    is_scale=True,
                    splitline_opts=opts.SplitLineOpts(is_show=True),
                ),
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                    label=opts.LabelOpts(background_color="#777"),
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(range_start=0, range_end=100),
                    opts.DataZoomOpts(type_="inside", range_start=0, range_end=100, xaxis_index=[0, 1, 2]),
                ],
            )
        )

        line2 = (
            Line()
            .set_global_opts(
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    boundary_gap=False,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=True),
                    position="top",
                    axislabel_opts=opts.LabelOpts(is_show=False),
                ),
                legend_opts=opts.LegendOpts(pos_left="9%"),
                yaxis_opts=opts.AxisOpts(
                    type_="value",
                    is_scale=True,
                    splitline_opts=opts.SplitLineOpts(is_show=True),
                ),
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                    label=opts.LabelOpts(background_color="#777"),
                ),
            )
            .add_xaxis(xaxis_data=date_list)
            .add_yaxis(
                series_name="Draw Down",
                y_axis=draw_down_list,
                label_opts=opts.LabelOpts(is_show=False),
                areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
            )
        )

        bar3 = (
            Bar()
            .set_global_opts(
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    boundary_gap=False,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=True),
                    axislabel_opts=opts.LabelOpts(is_show=False),
                ),
                legend_opts=opts.LegendOpts(pos_left="19%"),
                yaxis_opts=opts.AxisOpts(
                    type_="value",
                    is_scale=True,
                    splitline_opts=opts.SplitLineOpts(is_show=True),
                ),
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                    label=opts.LabelOpts(background_color="#777"),
                ),
            )
            .add_xaxis(xaxis_data=date_list)
            .add_yaxis(series_name="Daily Pnl", yaxis_data=net_pnl_list, label_opts=opts.LabelOpts(is_show=False))
        )

        (
            Grid(init_opts=opts.InitOpts(width="100%", height="720px"))
            .add(chart=line1, grid_opts=opts.GridOpts(pos_left=50, pos_right=50, height="35%"))
            .add(
                chart=line2,
                grid_opts=opts.GridOpts(pos_left=50, pos_right=50, pos_top="48%", height="20%"),
            )
            .add(
                chart=bar3,
                grid_opts=opts.GridOpts(pos_left=50, pos_right=50, pos_top="71%", height="20%"),
            )
            .render(os.path.join(self.backtest_log_path, "daily_results.html"))
        )

    @add_log_path_wrapper
    def save_k_line_chart(self):
        if self.strategy.chart_dict is None:
            return
        self.strategy.chart_dict.draw_chart(
            save_path=self.backtest_log_path,
            kline_title=self.strategy.strategy_name + "_" + self.symbol
        )
