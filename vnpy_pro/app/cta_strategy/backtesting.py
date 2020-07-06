from datetime import date, datetime, timedelta
import pandas as pd
from pandas import DataFrame
import os
from functools import wraps
import logging
import pyecharts.options as opts
from pyecharts.charts import Line, Grid, Bar

from vnpy.app.cta_strategy.backtesting import BacktestingEngine, DailyResult
from vnpy.trader.constant import (Direction, Offset, Exchange,
                                  Interval, Status)
from vnpy.app.cta_strategy.base import BacktestingMode
from vnpy.trader.utility import get_file_logger

from vnpy_pro.tools.chart import draw_daily_results_chart


class DailyResultPro(DailyResult):
    def __init__(self, date: date, close_price: float):
        super().__init__(date, close_price)

    def calculate_pnl2(
        self,
        pre_close: float,
        start_pos: float,
        size: int,
        rate: float,
        slippage: float,
        inverse: bool
    ):
        """给从csv读取的数据使用"""
        # If no pre_close provided on the first day,
        # use value 1 to avoid zero division error
        if pre_close:
            self.pre_close = pre_close
        else:
            self.pre_close = 1

        # Holding pnl is the pnl from holding position at day start
        self.start_pos = start_pos
        self.end_pos = start_pos

        if not inverse:     # For normal contract
            self.holding_pnl = self.start_pos * \
                (self.close_price - self.pre_close) * size
        else:               # For crypto currency inverse contract
            self.holding_pnl = self.start_pos * \
                (1 / self.pre_close - 1 / self.close_price) * size

        # Trading pnl is the pnl from new trade during the day
        self.trade_count = len(self.trades)

        for trade in self.trades:
            if trade["direction"] == Direction.LONG.value:
                pos_change = trade["volume"]
            else:
                pos_change = -trade["volume"]

            self.end_pos += pos_change

            # For normal contract
            if not inverse:
                turnover = trade["volume"] * size * trade["price"]
                self.trading_pnl += pos_change * \
                    (self.close_price - trade["price"]) * size
                self.slippage += trade["volume"] * size * slippage
            # For crypto currency inverse contract
            else:
                turnover = trade["volume"] * size / trade["price"]
                self.trading_pnl += pos_change * \
                    (1 / trade["price"] - 1 / self.close_price) * size
                self.slippage += trade["volume"] * size * slippage / (trade["price"] ** 2)

            self.turnover += turnover
            self.commission += turnover * rate

        # Net pnl takes account of commission and slippage cost
        self.total_pnl = self.trading_pnl + self.holding_pnl
        self.net_pnl = self.total_pnl - self.commission - self.slippage


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

    def get_trades_list(self):
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
                # i.time,
                i.tradeid,
                i.volume,
                i.vt_orderid,
                i.vt_symbol,
                i.vt_tradeid,
            ]
            for i in trades_results
        ]
        return trades_results

    @add_log_path_wrapper
    def export_trades(self):
        # 导出trades到csv
        trades_results = self.get_trades_list()
        trades_results_df = pd.DataFrame(
            trades_results,
            columns=["datetime", "direction", "exchange", "gateway_name", "offset", "orderid", "price",
                     "symbol", "tradeid", "volume", "vt_orderid", "vt_symbol", "vt_tradeid"]
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
                # i.time,
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
                     "status", "symbol", "traded", "type", "volume", "vt_orderid", "vt_symbol"]
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
        draw_daily_results_chart(self.daily_df, self.backtest_log_path)

    @add_log_path_wrapper
    def save_k_line_chart(self):
        if len(self.strategy.KLine_chart_dict.list_dict) == 0:
            return
        trades_results = self.get_trades_list()
        self.strategy.KLine_chart_dict.draw_chart_backtest(
            save_path=self.backtest_log_path,
            trade_list=trades_results,
            kline_title=self.strategy.strategy_name + "_" + self.symbol,
        )
