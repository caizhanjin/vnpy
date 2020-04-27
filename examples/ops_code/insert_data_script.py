import csv
from datetime import datetime

from vnpy.trader.object import BarData
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.utility import round_to

# 设置配置参数
interval = Interval.MINUTE
symbol = "IF000"
exchange = Exchange.CFFEX
pricetick = 0.2


# 打开CSV文件
with open("if_data.csv") as f:
    # 用Dict方式读取
    reader = csv.DictReader(f)

    # 从文件读取数据并转换成对象
    buf = []
    for d in reader:
        bar = BarData(
            gateway_name="DB",
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            datetime=datetime.strptime(d["datetime"], "%Y-%m-%d %H:%M:%S")
        )
        bar.open_price = round_to(d["open"], pricetick)
        bar.high_price = round_to(d["high"], pricetick)
        bar.low_price = round_to(d["low"], pricetick)
        bar.close_price = round_to(d["close"], pricetick)
        bar.volume = d["volume"]
        bar.open_interest = d["open_interest"]

        buf.append(bar)

    # 写入数据库
    database_manager.save_bar_data(buf)

print("数据插入完成：", len(buf))
