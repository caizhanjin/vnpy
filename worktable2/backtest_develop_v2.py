from datetime import datetime
import os

from vnpy.app.cta_strategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval

from vnpy_pro.app.cta_strategy.backtesting import BacktestingEnginePro
from vnpy_pro.app.cta_strategy.csv_backtesting import CsvBacktestingEngine

from vnpy_pro.config import load_futures
from vnpy_pro.data.tdx.tdx_common import get_future_contracts

from worktable.strategies_storage.num9_btb.macd_strategy import MACDStrategy
from worktable.strategies_storage.num9_btb.macd_strategy_v2 import MACDStrategy
from worktable.strategies_storage.num4_renko.renko import RenkoStrategy

test_future = "MA"

FUTURES = load_futures()
future_contracts = get_future_contracts()
vt_symbol = test_future.upper() + "99." + future_contracts[test_future]["exchange"]
print(vt_symbol)

engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol=vt_symbol,
    interval=Interval.MINUTE,
    start=datetime(2020, 6, 1),
    end=datetime(2020, 11, 1),
    rate=1 / 10000,
    slippage=0,
    size=future_contracts[test_future]["symbol_size"],
    pricetick=future_contracts[test_future]["price_tick"],
    capital=50_000,
)
engine.add_strategy(MACDStrategy, {})

engine.load_data()
engine.run_backtesting()
engine.calculate_result()
engine.calculate_statistics()

engine.show_chart()


# 参数优化
# setting = OptimizationSetting()
# setting.set_target("sharpe_ratio")
# setting.add_parameter("big_entry", 20, 30, 5)
# setting.add_parameter("big_exit", 5, 15, 5)
#
# result = engine.run_ga_optimization(setting)

