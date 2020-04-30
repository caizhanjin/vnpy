from datetime import datetime
import os

from vnpy.trader.constant import Interval
from vnpy_pro.app.cta_strategy.backtesting import BacktestingEnginePro
from vnpy_pro.config import load_futures

# from worktable.backtest.strategies.break_strategy_4 import BreakStrategy
from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import AtrRsiStrategy

FUTURES = load_futures()

test_future = "bu"

# test_future.upper() + "99." + FUTURES[test_future]["exchange_code"]

engine = BacktestingEnginePro()
engine.set_parameters(
    vt_symbol="IF99.CFFEX",
    interval=Interval.MINUTE,
    start=datetime(2019, 1, 1),
    end=datetime(2020, 4, 30),
    rate=0.3/10000,
    slippage=0,
    size=FUTURES[test_future]["multiplier"],
    pricetick=FUTURES[test_future]["minimum_change"],
    capital=10_000,
    log_path=os.path.dirname(__file__)
)
engine.add_strategy(AtrRsiStrategy, {})

engine.load_data()
engine.run_backtesting()
engine.calculate_result()
engine.calculate_statistics()

# engine.show_chart()

engine.export_all()

