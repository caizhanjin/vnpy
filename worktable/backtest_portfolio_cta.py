from datetime import datetime
import os

from vnpy.trader.constant import Interval
from vnpy_pro.app.cta_strategy.backtesting import BacktestingEnginePro
from vnpy_pro.config import load_futures

from vnpy_pro.data.tdx.tdx_common import get_future_contracts
from worktable.strategies_storage.num2_final.KFM_strategy_v1 import KFMStrategy

# 组合回测合约填入这里
futures = ["RB", "BU", "AG", "P"]
# futures = ["RB", "BU", "MA", "RU", "AG"]
is_save_result = True
FUTURES = load_futures()
future_contracts = get_future_contracts()
interval = Interval.MINUTE
start = datetime(2017, 8, 1)
end = datetime(2020, 11, 1)
capital = 200_000


def run_backtesting(strategy_class, setting,
                    vt_symbol1, interval1, start1, end1,
                    rate1, slippage1, size1, pricetick1, capital1):
    print(f"开始回测{vt_symbol1}...")
    engine = BacktestingEnginePro()
    engine.set_parameters(
        vt_symbol=vt_symbol1,
        interval=interval1,
        start=start1,
        end=end1,
        rate=rate1,
        slippage=slippage1,
        size=size1,
        pricetick=pricetick1,
        capital=capital1,
        log_path=os.path.dirname(__file__)
    )
    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()
    engine.calculate_statistics()

    if is_save_result:
        # engine.show_chart()
        engine.export_all()
        print("#####################################################")

    return df


df_p = None
for future in futures:
    vt_symbol = future.upper() + "99." + future_contracts[future]["exchange"]
    rate = 0.23 / 10000
    slippage = 0
    size = future_contracts[future]["symbol_size"]
    pricetick = future_contracts[future]["price_tick"]

    df_item = run_backtesting(
        strategy_class=KFMStrategy,
        setting={},
        vt_symbol1=vt_symbol,
        interval1=interval,
        start1=start,
        end1=end,
        rate1=rate,
        slippage1=slippage,
        size1=size,
        pricetick1=pricetick,
        capital1=capital,
    )
    df_p = df_item if df_p is None else (df_p + df_item)

df_p = df_p.dropna()
engine = BacktestingEnginePro()
engine.capital = capital
engine.calculate_statistics(df_p)
engine.show_chart(df_p)
