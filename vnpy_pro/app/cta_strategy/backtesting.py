from datetime import datetime
import pandas as pd
import os

from vnpy.app.cta_strategy.backtesting import BacktestingEngine
from vnpy.trader.constant import (Direction, Offset, Exchange,
                                  Interval, Status)
from vnpy.app.cta_strategy.base import BacktestingMode


class BacktestingEnginePro(BacktestingEngine):

    def __init__(self):
        super().__init__()

        self.root_log_path = ""
        self.strategy_log_path = ""
        self.backtest_log_path = ""

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

    def add_strategy(self, strategy_class: type, setting: dict):
        """"""
        super().add_strategy(strategy_class, setting)

        self.strategy_log_path = os.path.join(self.root_log_path, self.strategy.strategy_name)
        backtest_log_name = str(datetime.now().strftime("%Y%m%d%H%M%S")) + "_" + \
                            self.symbol + "_" + \
                            self.interval.value + "_" + \
                            self.start.strftime("%Y%m%d") + "_" + \
                            self.end.strftime("%Y%m%d")
        self.backtest_log_path = os.path.join(self.strategy_log_path, backtest_log_name)
        if not os.path.exists(self.strategy_log_path):
            os.mkdir(self.strategy_log_path)
        if not os.path.exists(self.backtest_log_path):
            os.mkdir(self.backtest_log_path)

    def export_all(self):
        self.export_daily_results()
        self.export_trades()
        self.export_orders()

    def export_daily_results(self):
        # 导出daily_results到csv
        self.daily_df.to_csv(os.path.join(self.backtest_log_path, "daily_results.csv"))

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
