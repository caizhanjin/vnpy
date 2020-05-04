from datetime import datetime
import os

from vnpy.trader.constant import Interval
from vnpy_pro.app.cta_strategy.backtesting import BacktestingEnginePro
from vnpy_pro.config import load_futures

# from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import AtrRsiStrategy
from worktable.strategies_example.atr_rsi_strategy import AtrRsiStrategy

FUTURES = load_futures()

test_future = "RB"

# test_future.upper() + "99." + FUTURES[test_future]["exchange_code"]

engine = BacktestingEnginePro()
engine.set_parameters(
    vt_symbol="RB99.SHFE",
    interval=Interval.MINUTE,
    start=datetime(2020, 1, 1),
    end=datetime(2020, 4, 30),
    rate=0.3/10000,
    slippage=0,
    size=FUTURES[test_future]["symbol_size"] * FUTURES[test_future]["margin_rate"],
    pricetick=FUTURES[test_future]["price_tick"],
    capital=10_000,
    log_path=os.path.dirname(__file__)
)
engine.add_strategy(AtrRsiStrategy, {})

engine.load_data()
engine.run_backtesting()
engine.calculate_result()
engine.calculate_statistics()

# engine.show_chart()
# engine.export_all()

