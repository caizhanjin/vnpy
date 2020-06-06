from datetime import datetime
import os

from vnpy.app.cta_strategy.backtesting import OptimizationSetting
from vnpy.trader.constant import Interval
from vnpy_pro.app.cta_strategy.backtesting import BacktestingEnginePro
from vnpy_pro.config import load_futures

# from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import AtrRsiStrategy
from worktable.strategies_example.atr_rsi_strategy import AtrRsiStrategy
from worktable.strategies_storage.num6_option.bbi_strategy_vnpy import BStrategy
from worktable.strategies_storage.num1_breaker.break_strategy_4 import BreakStrategy
from worktable.strategies_storage.num3_single_trend.try_strategy import TryStrategy
from worktable.strategies.try_strategy import TryStrategy

FUTURES = load_futures()

test_future = "MA"

vt_symbol = test_future.upper() + "99." + FUTURES[test_future]["exchange_code"]
# FUTURES[test_future]["symbol_size"] * FUTURES[test_future]["margin_rate"]

engine = BacktestingEnginePro()
engine.set_parameters(
    vt_symbol=vt_symbol,
    interval=Interval.MINUTE,
    start=datetime(2019, 1, 1),
    end=datetime(2020, 1, 1),
    rate=0.1 / 1000,
    slippage=0,
    size=10,
    pricetick=FUTURES[test_future]["price_tick"],
    capital=50_000,
    log_path=os.path.dirname(__file__)
)
engine.add_strategy(TryStrategy, {})

# engine.load_data()
# engine.run_backtesting()
# engine.calculate_result()
# engine.calculate_statistics()

# 保存结果
# engine.show_chart()
# engine.export_all()


# 参数优化
setting = OptimizationSetting()
setting.set_target("sharpe_ratio")
setting.add_parameter("big_entry", 20, 30, 5)
setting.add_parameter("big_exit", 5, 15, 5)

result = engine.run_ga_optimization(setting)

pass
