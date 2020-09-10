from datetime import datetime
import os

from vnpy.trader.constant import Interval

from vnpy_pro.app.cta_strategy.backtesting import BacktestingEnginePro
from vnpy_pro.app.cta_strategy.csv_backtesting import CsvBacktestingEngine

from vnpy_pro.config import load_futures
from vnpy_pro.data.tdx.tdx_common import get_future_contracts

from worktable.strategies.KFM_strategy import KFMStrategy
from worktable.strategies.break_strategy import BreakStrategy
from worktable.strategies_storage.num1_breaker.break_strategy_1 import BreakStrategy
from worktable.strategies_storage.num1_breaker.break_strategy_long import BreakStrategy
from worktable.strategies_storage.num7_bbi_turtle.machine_strategy import MachineStrategy
from worktable.strategies_storage.num8_toos.tradedays import TradeDaysStrategy
from worktable.strategies_storage.num9_macd.macd_strategy import MACDStrategy


test_future = "MA"

FUTURES = load_futures()
future_contracts = get_future_contracts()
vt_symbol = test_future.upper() + "99." + future_contracts[test_future]["exchange"]
print(vt_symbol)

engine = BacktestingEnginePro()
engine.set_parameters(
    vt_symbol=vt_symbol,
    interval=Interval.MINUTE,
    start=datetime(2019, 1, 1),
    end=datetime(2020, 11, 1),
    rate=1 / 10000,
    slippage=0,
    size=future_contracts[test_future]["symbol_size"],
    pricetick=future_contracts[test_future]["price_tick"],
    capital=50_000,
    log_path=os.path.dirname(__file__)
)
engine.add_strategy(MACDStrategy, {})

engine.load_data()
engine.run_backtesting()
engine.calculate_result()
engine.calculate_statistics()

# 保存结果
# engine.show_chart()
engine.export_all()


# 参数优化
# setting = OptimizationSetting()
# setting.set_target("sharpe_ratio")
# setting.add_parameter("big_entry", 20, 30, 5)
# setting.add_parameter("big_exit", 5, 15, 5)
#
# result = engine.run_ga_optimization(setting)

