from datetime import datetime

from vnpy.app.portfolio_strategy import BacktestingEngine
from vnpy.app.portfolio_strategy.strategies.trend_following_strategy import TrendFollowingStrategy
from vnpy.trader.constant import Interval

from vnpy_pro.config import load_futures

FUTURES = load_futures()

test_future = "bu"
symbol = "BU99.SHFE"
# test_future.upper() + "99." + FUTURES[test_future]["exchange_code"]

engine = BacktestingEngine()
engine.set_parameters(
    vt_symbols=[symbol],
    interval=Interval.MINUTE,
    start=datetime(2010, 2, 1),
    end=datetime(2020, 4, 30),
    rates={symbol: 0.3/10000},
    slippages={symbol: 0.2},
    sizes={symbol: 300},
    priceticks={symbol: 0.2},
    capital=1_000_000,
)
engine.add_strategy(TrendFollowingStrategy, {})

engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()



