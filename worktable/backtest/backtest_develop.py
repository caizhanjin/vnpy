from vnpy.app.cta_strategy.backtesting import BacktestingEngine
# from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import (
#     AtrRsiStrategy,
# )
from datetime import datetime
from worktable.backtest.strategies.trend_strategy import AtrRsiStrategy

from vnpy_pro.config import load_futures

FUTURES = load_futures()

test_future = "RB"

engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol=test_future + "99." + FUTURES[test_future]["exchange_code"],
    interval="1m",
    start=datetime(2019, 1, 1),
    end=datetime(2020, 4, 30),
    rate=0.3/10000,
    slippage=FUTURES[test_future]["minimum_change"],
    size=FUTURES[test_future]["multiplier"],
    pricetick=FUTURES[test_future]["minimum_change"],
    capital=1_000_000,
)
engine.add_strategy(AtrRsiStrategy, {})

engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()

