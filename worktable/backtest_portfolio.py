from datetime import datetime
from importlib import reload

import vnpy.app.portfolio_strategy
reload(vnpy.app.portfolio_strategy)

from vnpy.app.portfolio_strategy import BacktestingEngine
from vnpy.trader.constant import Interval

import vnpy.app.portfolio_strategy.strategies.pair_trading_strategy as stg
reload(stg)
from worktable.strategies_storage.num6_epiboly.num2_wang.turtle_portfolio_strategy import TurtlePortfolioStrategy

# MA99.CZCE,BU99.SHFE
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbols=["MA99.CZCE", "BU99.SHFE"],
    interval=Interval.MINUTE,
    start=datetime(2020, 6, 1),
    end=datetime(2020, 7, 1),
    rates={
        "MA99.CZCE": 0/10000,
        "BU99.SHFE": 0/10000
    },
    slippages={
        "MA99.CZCE": 0,
        "BU99.SHFE": 0
    },
    sizes={
        "MA99.CZCE": 10,
        "BU99.SHFE": 10
    },
    priceticks={
        "MA99.CZCE": 1,
        "BU99.SHFE": 1
    },
    capital=1_000_000,
)

setting = {}
engine.add_strategy(TurtlePortfolioStrategy, setting)

engine.load_data()
engine.run_backtesting()
engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()

