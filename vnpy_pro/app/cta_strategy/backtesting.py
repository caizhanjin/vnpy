from datetime import datetime
import pandas as pd
import os
from functools import wraps
import logging

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

        return func(self)
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
        self.export_daily_results(self)
        self.export_trades(self)
        self.export_orders(self)
        self.save_output(self)

    @add_log_path_wrapper
    def export_daily_results(self):
        # 导出daily_results到csv
        self.daily_df.to_csv(os.path.join(self.backtest_log_path, "daily_results.csv"))

    @add_log_path_wrapper
    def export_trades(self):
        # 导出trades到csv
        trades_results = self.get_all_trades()
        trades_results = [
            [
                i.datetime,
                i.direction,
                i.exchange,
                i.gateway_name,
                i.offset,
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

        trades_results_df.to_csv(os.path.join(self.backtest_log_path, "trades.csv"))

    @add_log_path_wrapper
    def export_orders(self):
        # 导出orders到csv
        trades_orders = self.get_all_orders()
        trades_orders = [
            [
                i.datetime,
                i.direction,
                i.exchange,
                i.gateway_name,
                i.offset,
                i.orderid,
                i.price,
                i.status,
                i.symbol,
                i.time,
                i.traded,
                i.type,
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

        trades_orders_df.to_csv(os.path.join(self.backtest_log_path, "orders.csv"))

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

