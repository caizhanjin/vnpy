import csv
import os
import re
from collections import defaultdict
from typing import Any, Callable
from datetime import date, datetime, timedelta
import logging
from pandas import DataFrame
import pandas as pd
import numpy as np

from vnpy.app.cta_strategy import CtaTemplate
from vnpy.trader.object import BarData, TickData, TradeData, OrderData
from vnpy.trader.utility import get_folder_path, TEMP_DIR, get_file_logger, load_json, save_json

from vnpy_pro.tools.widget import csv_add_rows
from vnpy_pro.data.tdx.tdx_common import get_future_contracts
from vnpy_pro.app.cta_strategy.backtesting import DailyResultPro


class CtaTemplatePro(CtaTemplate):

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.order_list = []
        self.trade_list = []
        self.daily_close_dict = {}  # 用于计算daily_result和策略监控指标
        self.output_list = []
        self.last_datetime = None

    def on_bar(self, bar: BarData):
        self.last_datetime = bar.datetime
        self.update_daily_close(bar.close_price)

    def on_tick(self, tick: TickData):
        self.last_datetime = tick.datetime
        self.update_daily_close(tick.last_price)

    def on_trade(self, trade: TradeData):
        self.trade_list.append([
            self.last_datetime,
            trade.direction.value,
            trade.exchange.value,
            trade.gateway_name,
            trade.offset.value,
            trade.orderid,
            trade.price,
            trade.symbol,
            trade.time,
            trade.tradeid,
            trade.volume,
            trade.vt_orderid,
            trade.vt_symbol,
            trade.vt_tradeid,
        ])

    def on_order(self, order: OrderData):
        self.order_list.append([
            self.last_datetime,
            order.direction.value,
            order.exchange.value,
            order.gateway_name,
            order.offset.value,
            order.orderid,
            order.price,
            order.status.value,
            order.symbol,
            order.time,
            order.traded,
            order.type.value,
            order.volume,
            order.vt_orderid,
            order.vt_symbol,
        ])

    def write_log(self, msg: str):
        super().write_log(msg)
        self.output_list.append(msg)

    def update_daily_close(self, last_price):
        self.daily_close_dict[self.last_datetime.strftime("%Y-%m-%d")] = last_price

    def save_trade_data(self, instance_name):
        """保存策略实盘数据
        tips: 实盘时调用"""
        save_path = os.path.join(
            TEMP_DIR,
            "trade_data",
            instance_name + "_" + self.strategy_name + "_" + self.vt_symbol.split(".")[0]
        )
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        if len(self.order_list) != 0:
            csv_add_rows(
                data_list=self.order_list,
                header=["datetime", "direction", "exchange", "gateway_name", "offset", "orderid", "price",
                        "status", "symbol", "time", "traded", "type", "volume", "vt_orderid", "vt_symbol"],
                csv_path=os.path.join(save_path, "orders.csv")
            )
            self.order_list = []

        if len(self.trade_list) != 0:
            csv_add_rows(
                data_list=self.trade_list,
                header=["datetime", "direction", "exchange", "gateway_name", "offset", "orderid", "price",
                        "symbol", "time", "tradeid", "volume", "vt_orderid", "vt_symbol", "vt_tradeid"],
                csv_path=os.path.join(save_path, "trades.csv")
            )
            self.trade_list = []

        if len(self.output_list) != 0:
            logger = get_file_logger(os.path.join(save_path, "output.log"))
            logger.setLevel(logging.INFO)
            for output in self.output_list:
                logger.info(output)
            self.output_list = []

        if len(self.daily_close_dict) != 0:
            daily_close_file = os.path.join(save_path, "daily_close.json")
            pre_close_dict = load_json(daily_close_file)
            pre_close_dict.update(self.daily_close_dict)
            save_json(daily_close_file, pre_close_dict)

        self.update_daily_results(instance_name)

    def update_daily_results(self, instance_name, capital=10_000):
        save_path = os.path.join(
            TEMP_DIR,
            "trade_data",
            instance_name + "_" + self.strategy_name + "_" + self.vt_symbol.split(".")[0]
        )
        daily_results_file = os.path.join(save_path, "daily_results.csv")
        trades_df = pd.read_csv(os.path.join(save_path, "trades.csv"))
        trades_dict = trades_df.to_dict(orient="records")
        close_dict = load_json(os.path.join(save_path, "daily_close.json"))

        daily_results = {}
        for daily_date, daily_close in close_dict.items():
            daily_results[daily_date] = DailyResultPro(daily_date, daily_close)
        for trade in trades_dict:
            d = trade["datetime"][:10]
            # 防止对应的不存在收盘价，不存收盘以交易价为准
            daily_result = daily_results.get(d, DailyResultPro(d, trade["price"]))
            daily_result.add_trade(trade)

        daily_results_values = daily_results.values()
        if len(daily_results_values) != 0:
            future_contracts = get_future_contracts()
            symbol_letter = ''.join(re.split(r'[^A-Za-z]', self.vt_symbol.split(".")[0]))
            symbol_info = future_contracts.get(symbol_letter, {})

            pre_close = 0
            start_pos = 0

            for daily_result in daily_results_values:
                # 手续费、滑点设置为0
                daily_result.calculate_pnl2(
                    pre_close,
                    start_pos,
                    symbol_info.get("symbol_size", 1) * symbol_info.get("margin_rate", 1),
                    0,
                    0,
                    False
                )
                pre_close = daily_result.close_price
                start_pos = daily_result.end_pos

            results = defaultdict(list)
            for daily_result in daily_results_values:
                for key, value in daily_result.__dict__.items():
                    results[key].append(value)

            daily_df = DataFrame.from_dict(results).set_index("date")
            self.calculate_statistics_and_save(daily_df, save_path, capital)
            daily_df.to_csv(daily_results_file, encoding="utf_8_sig")

    @staticmethod
    def calculate_statistics_and_save(df, save_path, capital):
        """计算策略监控参数"""
        df["balance"] = df["net_pnl"].cumsum() + capital
        df["return"] = np.log(df["balance"] / df["balance"].shift(1)).fillna(0)
        df["highlevel"] = (
            df["balance"].rolling(
                min_periods=1, window=len(df), center=False).max()
        )
        df["drawdown"] = df["balance"] - df["highlevel"]
        df["ddpercent"] = df["drawdown"] / df["highlevel"] * 100

        start_date = df.index[0]
        end_date = df.index[-1]

        total_days = len(df)
        profit_days = len(df[df["net_pnl"] > 0])
        loss_days = len(df[df["net_pnl"] < 0])

        end_balance = df["balance"].iloc[-1]
        max_drawdown = df["drawdown"].min()
        max_ddpercent = df["ddpercent"].min()
        max_drawdown_end = df["drawdown"].idxmin()

        if isinstance(max_drawdown_end, date):
            max_drawdown_start = df["balance"][:max_drawdown_end].idxmax()
            max_drawdown_duration = (max_drawdown_end - max_drawdown_start).days
        else:
            max_drawdown_duration = 0

        total_net_pnl = df["net_pnl"].sum()
        daily_net_pnl = total_net_pnl / total_days

        total_commission = df["commission"].sum()
        daily_commission = total_commission / total_days

        total_slippage = df["slippage"].sum()
        daily_slippage = total_slippage / total_days

        total_turnover = df["turnover"].sum()
        daily_turnover = total_turnover / total_days

        total_trade_count = df["trade_count"].sum()
        daily_trade_count = total_trade_count / total_days

        total_return = (end_balance / capital - 1) * 100
        annual_return = total_return / total_days * 240
        daily_return = df["return"].mean() * 100
        return_std = df["return"].std() * 100

        if return_std:
            sharpe_ratio = daily_return / return_std * np.sqrt(240)
        else:
            sharpe_ratio = 0

        return_drawdown_ratio = -total_return / max_ddpercent

        statistics = {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "profit_days": profit_days,
            "loss_days": loss_days,
            "capital": capital,
            "end_balance": end_balance,
            "max_drawdown": max_drawdown,
            "max_ddpercent": max_ddpercent,
            "max_drawdown_duration": max_drawdown_duration,
            "total_net_pnl": total_net_pnl,
            "daily_net_pnl": daily_net_pnl,
            "total_commission": total_commission,
            "daily_commission": daily_commission,
            "total_slippage": total_slippage,
            "daily_slippage": daily_slippage,
            "total_turnover": total_turnover,
            "daily_turnover": daily_turnover,
            "total_trade_count": total_trade_count,
            "daily_trade_count": daily_trade_count,
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_return": daily_return,
            "return_std": return_std,
            "sharpe_ratio": sharpe_ratio,
            "return_drawdown_ratio": return_drawdown_ratio,
        }

        for key, value in statistics.items():
            print(type(value))
            if type(value) is int or type(value) is np.int64:
                statistics[key] = float(value)
            elif type(value) is np.float64:
                statistics[key] = float('%.2f' % value)

        save_json(os.path.join(save_path, "statistics.json"), statistics)
        return statistics
