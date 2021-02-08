from datetime import datetime
from tzlocal import get_localzone

from vnpy.trader.object import HistoryRequest
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Interval, Exchange

from vnpy_pro.data.source.tdxdata import tdxdata_client
from vnpy_pro.data.tdx.tdx_common import get_future_contracts

# 下载合约
futures = ["rb2105.SHFE"]
# futures = ["AG", "AP", "AU", "BU", "CF", "CU", "JD",
#            "MA", "NI", "OI", "P", "RB", "RU", "SR", "TA"]

if tdxdata_client.init():
    print("数据服务器登录成功")
else:
    print("数据服务器登录失败")
    import sys
    sys.exit(0)

for future in futures:
    _future = future.split(".")
    symbol = _future[0]
    exchange = Exchange.__dict__[_future[1]]
    interval = Interval.MINUTE

    # 查询数据库中的最新数据
    # start = datetime(2010, 6, 1)
    # 增量更新数据
    bar = database_manager.get_newest_bar_data(symbol, exchange, interval)
    if bar:
        start = bar.datetime
    else:
        start = datetime(2020, 11, 1)

    # 下载数据
    req = HistoryRequest(
        symbol,
        exchange,
        start,
        datetime.now(),
        interval=interval
    )
    data = tdxdata_client.query_history(req)

    # 写入数据库
    if data:
        database_manager.save_bar_data(data)
        print(f"{symbol}更新完成：{data[0].datetime} -- {data[-1].datetime}，总计 {len(data)} 条...")

print("数据更新完毕")
# 更新contracts字典
# tdxdata_client.tdx_api.update_mi_contracts()
