from datetime import datetime
import os

from vnpy.app.cta_strategy.backtesting import OptimizationSetting
from vnpy.trader.constant import Interval
from vnpy_pro.app.cta_strategy.backtesting import BacktestingEnginePro
from vnpy_pro.config import load_futures
from vnpy_pro.data.tdx.tdx_common import get_future_contracts

from worktable.strategies.try_strategy import TryStrategy
from worktable.strategies.grid_strategy import GridStrategy
# from worktable.strategies.KFM_ma_strategy import KFMMaStrategy
from worktable.strategies.KFM_ma_strategy_v2 import KFMMaStrategy


test_future = "AG"

FUTURES = load_futures()
future_contracts = get_future_contracts()
vt_symbol = test_future.upper() + "99." + future_contracts[test_future]["exchange"]
print(vt_symbol)

engine = BacktestingEnginePro()
engine.set_parameters(
    vt_symbol=vt_symbol,
    interval=Interval.MINUTE,
    start=datetime(2018, 1, 1),
    end=datetime(2020, 11, 1),
    rate=0.1 / 1000,
    slippage=0,
    size=future_contracts[test_future]["symbol_size"],
    pricetick=future_contracts[test_future]["price_tick"],
    capital=50_000,
    log_path=os.path.dirname(__file__)
)
engine.add_strategy(KFMMaStrategy, {})

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

