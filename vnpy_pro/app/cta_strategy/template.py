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
from vnpy.app.cta_strategy.base import EngineType
from vnpy.trader.object import BarData, TickData, TradeData, OrderData
from vnpy.trader.utility import (
    get_folder_path, TEMP_DIR, get_file_logger, load_json, save_json, BarGenerator,
    ArrayManager
)
from vnpy.trader.utility import virtual

from vnpy_pro.tools.widget import csv_add_rows
from vnpy_pro.data.tdx.tdx_common import get_future_contracts, get_cache_json
from vnpy_pro.app.cta_strategy.backtesting import DailyResultPro
from vnpy_pro.tools.chart import draw_daily_results_chart
from vnpy_pro.tools.chart import KLineChart


class CtaTemplatePro(CtaTemplate):

    fixed_size = 1
    trade_amount = 0
    lever = 0

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        # 回测不保存数据
        # strategy_name = "TEST1"
        if strategy_name == self.__class__.__name__:
            self.instance_name = None
        else:
            self.instance_name = strategy_name + "_" + self.__class__.__name__ + "_" + self.vt_symbol.split(".")[0]
            self.save_path = os.path.join(
                TEMP_DIR,
                "trade_data",
                self.instance_name
            )
        self.order_list = []
        self.trade_list = []
        self.daily_close_dict = {}  # 用于计算daily_result和策略监控指标
        self.output_list = []
        self.last_datetime = None
        self.KLine_chart_dict = KLineChart()

        # 固定资金计算交易手数
        if self.trade_amount:
            future_contracts = get_cache_json('self_maintain_contracts.json')
            contracts = future_contracts[''.join(re.findall(r'[A-Za-z]', vt_symbol[:3].upper()))]
            self.lever = contracts["margin_rate"] * contracts["symbol_size"]

    def on_bar(self, bar: BarData):
        # 固定资金计算交易手数
        if self.lever:
            self.fixed_size = self.trade_amount // (bar.close_price * self.lever)

        self.last_datetime = bar.datetime
        if self.instance_name is None:
            return
        self.update_daily_close(bar.close_price)

    def on_tick(self, tick: TickData):
        self.last_datetime = tick.datetime
        if self.instance_name is None:
            return
        self.update_daily_close(tick.last_price)

    def on_trade(self, trade: TradeData):
        if self.instance_name is None:
            return
        self.append_trade_list(trade)

    def append_trade_list(self, trade: TradeData):
        self.trade_list.append([
            self.last_datetime,
            trade.direction.value,
            trade.exchange.value,
            trade.gateway_name,
            trade.offset.value,
            trade.orderid,
            trade.price,
            trade.symbol,
            # trade.time,
            trade.tradeid,
            trade.volume,
            trade.vt_orderid,
            trade.vt_symbol,
            trade.vt_tradeid,
        ])

    def on_order(self, order: OrderData):
        if self.instance_name is None:
            return
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
            # order.time,
            order.traded,
            order.type.value,
            order.volume,
            order.vt_orderid,
            order.vt_symbol,
        ])

    def write_log(self, msg: str):
        super().write_log(msg)
        if self.instance_name is None:
            return
        self.output_list.append(msg)

    def update_daily_close(self, last_price):
        if self.trading:
            self.daily_close_dict[self.last_datetime.strftime("%Y-%m-%d")] = last_price

    def save_trade_data(self):
        """保存策略实盘数据
        tips: 实盘时调用"""
        if self.instance_name is None:
            return
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

        if len(self.order_list) != 0:
            csv_add_rows(
                data_list=self.order_list,
                header=["datetime", "direction", "exchange", "gateway_name", "offset", "orderid", "price",
                        "status", "symbol", "traded", "type", "volume", "vt_orderid", "vt_symbol"],
                csv_path=os.path.join(self.save_path, "orders.csv")
            )
            self.order_list = []

        if len(self.trade_list) != 0:
            csv_add_rows(
                data_list=self.trade_list,
                header=["datetime", "direction", "exchange", "gateway_name", "offset", "orderid", "price",
                        "symbol", "tradeid", "volume", "vt_orderid", "vt_symbol", "vt_tradeid"],
                csv_path=os.path.join(self.save_path, "trades.csv")
            )
            self.trade_list = []

        if len(self.output_list) != 0:
            logger = get_file_logger(os.path.join(self.save_path, "output.log"))
            logger.setLevel(logging.INFO)
            for output in self.output_list:
                logger.info(output)
            self.output_list = []

        if len(self.daily_close_dict) != 0:
            daily_close_file = os.path.join(self.save_path, "daily_close.json")
            pre_close_dict = load_json(daily_close_file)
            pre_close_dict.update(self.daily_close_dict)
            save_json(daily_close_file, pre_close_dict)

        list_dict = self.KLine_chart_dict.list_dict
        if len(list_dict["datetime"]) != 0:
            KLine_list = []
            for i in range(len(list_dict["datetime"])):
                row = []
                for field in self.KLine_chart_dict.all_field:
                    row.append(list_dict[field][i])
                KLine_list.append(row)
            csv_add_rows(
                data_list=KLine_list,
                header=self.KLine_chart_dict.all_field,
                csv_path=os.path.join(self.save_path, "KLineChart.csv")
            )
            # self.draw_k_line()
            # self.calculate_and_chart_daily_results()

    def calculate_and_chart_daily_results(self, capital=None):
        """update daily_results，并绘制资金曲线图"""
        if not capital and self.trade_amount:
            capital = self.trade_amount
        elif not capital and not self.trade_amount:
            capital = 10000
        if self.instance_name is None:
            return
        if not os.path.exists(self.save_path):
            self.write_log(f"实例{self.instance_name} 不存在交易数据，无法update daily_results，并绘制资金曲线图")
            return
        daily_results_file = os.path.join(self.save_path, "daily_results.csv")
        close_dict = load_json(os.path.join(self.save_path, "daily_close.json"))
        trades_file = os.path.join(self.save_path, "trades.csv")
        if not os.path.exists(trades_file):
            return
        trades_df = pd.read_csv(trades_file)
        trades_dict = trades_df.to_dict(orient="records")

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
                    symbol_info.get("symbol_size", 1),
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
            statistics = self.calculate_statistics_and_save(daily_df, self.save_path, capital)
            daily_df.to_csv(daily_results_file, encoding="utf_8_sig")
            draw_daily_results_chart(daily_df=daily_df, save_path=self.save_path)
            # self.write_log(f"实例{self.instance_name} update daily_results，并绘制资金曲线图成功")
            return statistics

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

        if max_ddpercent:
            return_drawdown_ratio = -total_return / max_ddpercent
        else:
            return_drawdown_ratio = 0

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
            if type(value) is int or type(value) is np.int64:
                statistics[key] = float(value)
            elif type(value) is np.float64:
                statistics[key] = float('%.2f' % value)

        save_json(os.path.join(save_path, "statistics.json"), statistics)
        return statistics

    def draw_k_line(self):
        """绘制K线图"""
        self.KLine_chart_dict.draw_chart_from_csv(
            save_path=self.save_path,
            kline_title=self.instance_name
        )


class TargetPosTemplatePro(CtaTemplatePro):
    """"""
    tick_add = 1

    last_tick = None
    last_bar = None
    target_pos = 0

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.active_orderids = []
        self.cancel_orderids = []

        self.variables.append("target_pos")

    @virtual
    def on_tick(self, tick: TickData):
        super().on_tick(tick)
        self.last_tick = tick

        if self.trading:
            self.trade()

    @virtual
    def on_bar(self, bar: BarData):
        super().on_bar(bar)
        self.last_bar = bar

    @virtual
    def on_order(self, order: OrderData):
        super().on_order(order)
        vt_orderid = order.vt_orderid

        if not order.is_active():
            if vt_orderid in self.active_orderids:
                self.active_orderids.remove(vt_orderid)

            if vt_orderid in self.cancel_orderids:
                self.cancel_orderids.remove(vt_orderid)

    def check_order_finished(self):
        """"""
        if self.active_orderids:
            return False
        else:
            return True

    def set_target_pos(self, target_pos):
        """"""
        self.target_pos = target_pos
        self.trade()

    def trade(self):
        """"""
        if not self.check_order_finished():
            self.cancel_old_order()
        else:
            self.send_new_order()

    def cancel_old_order(self):
        """"""
        for vt_orderid in self.active_orderids:
            if vt_orderid not in self.cancel_orderids:
                self.cancel_order(vt_orderid)
                self.cancel_orderids.append(vt_orderid)

    def send_new_order(self):
        """"""
        pos_change = self.target_pos - self.pos
        if not pos_change:
            return

        long_price = 0
        short_price = 0

        if self.last_tick:
            if pos_change > 0:
                long_price = self.last_tick.ask_price_1 + self.tick_add
                if self.last_tick.limit_up:
                    long_price = min(long_price, self.last_tick.limit_up)
            else:
                short_price = self.last_tick.bid_price_1 - self.tick_add
                if self.last_tick.limit_down:
                    short_price = max(short_price, self.last_tick.limit_down)

        else:
            if pos_change > 0:
                long_price = self.last_bar.close_price + self.tick_add
            else:
                short_price = self.last_bar.close_price - self.tick_add

        if self.get_engine_type() == EngineType.BACKTESTING:
            if pos_change > 0:
                vt_orderids = self.buy(long_price, abs(pos_change))
            else:
                vt_orderids = self.short(short_price, abs(pos_change))
            self.active_orderids.extend(vt_orderids)

        else:
            if self.active_orderids:
                return

            if pos_change > 0:
                if self.pos < 0:
                    if pos_change < abs(self.pos):
                        vt_orderids = self.cover(long_price, pos_change)
                    else:
                        vt_orderids = self.cover(long_price, abs(self.pos))
                else:
                    vt_orderids = self.buy(long_price, abs(pos_change))
            else:
                if self.pos > 0:
                    if abs(pos_change) < self.pos:
                        vt_orderids = self.sell(short_price, abs(pos_change))
                    else:
                        vt_orderids = self.sell(short_price, abs(self.pos))
                else:
                    vt_orderids = self.short(short_price, abs(pos_change))
            self.active_orderids.extend(vt_orderids)


class StopManage(object):

    long_stop = 0
    short_stop = 0
    move_diff = 0

    signal = 0

    def __init__(self, am, atr_count, fixed_pre, move_pre):
        self.am = am

        self.atr_count = atr_count
        self.fixed_pre = fixed_pre
        self.move_pre = move_pre

    def open_long(self, trade):
        atr = self.am.atr(self.atr_count)
        self.long_stop = trade.price - atr * self.fixed_pre
        self.move_diff = atr * self.move_pre
        self.signal = 1

    def open_short(self, trade):
        atr = self.am.atr(self.atr_count)
        self.short_stop = trade.price + atr * self.fixed_pre
        self.move_diff = atr * self.move_pre
        self.signal = -1

    def on_bar(self, bar, pos):
        if pos > 0:
            self.long_stop = max(self.long_stop, bar.high_price - self.move_diff)
            if bar.low_price <= self.long_stop:
                self.signal = 0

        elif pos < 0:
            self.short_stop = min(self.short_stop, bar.low_price + self.move_diff)
            if bar.high_price >= self.short_stop:
                self.signal = 0
