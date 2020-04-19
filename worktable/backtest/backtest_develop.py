from vnpy.app.cta_strategy.backtesting import BacktestingEngine
# from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import (
#     AtrRsiStrategy,
# )
from datetime import datetime
from worktable.backtest.strategies.trend_strategy import TrendStrategy
from worktable.backtest.strategies.break_strategy_4 import BreakStrategy

from vnpy_pro.config import load_futures

FUTURES = load_futures()

test_future = "bu"

# test_future.upper() + "99." + FUTURES[test_future]["exchange_code"]

engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="BU99.SHFE",
    interval="1m",
    start=datetime(2016, 1, 1),
    end=datetime(2020, 4, 30),
    rate=0.3/10000,
    slippage=0,
    size=FUTURES[test_future]["multiplier"],
    pricetick=FUTURES[test_future]["minimum_change"],
    capital=10_000,
)
engine.add_strategy(BreakStrategy, {})

engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()

