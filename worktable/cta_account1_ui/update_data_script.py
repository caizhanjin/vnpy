from datetime import datetime

from vnpy.trader.object import HistoryRequest
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.rqdata import rqdata_client
from vnpy.trader.setting import SETTINGS

from vnpy_pro.data.source.tdxdata import tdxdata_client

# 设置配置参数
interval = Interval.MINUTE
symbol = "IF2005"
exchange = Exchange.CFFEX

# 查询数据库中的最新数据
bar = database_manager.get_newest_bar_data(symbol, exchange, interval)
if bar:
    start = bar.datetime
else:
    start = datetime(2017, 1, 1)

if tdxdata_client.init():
    print("RQData登录成功")
else:
    print("RQData登录失败")

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
    print(f"数据更新完成：{data[0].datetime} -- {data[-1].datetime}")
