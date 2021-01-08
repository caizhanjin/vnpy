import os
import sys

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
print(ROOT_PATH)
sys.path.append(ROOT_PATH)
if not os.path.exists(".vntrader"):
    os.mkdir(".vntrader")

from tzlocal import get_localzone
from datetime import datetime

from vnpy.trader.object import BarData
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Interval, Exchange


def csv_load(file_path):
    """
    读取csv文件内容，并写入到数据库中
    """
    for _file in os.listdir(file_path):
        full_path = os.path.join(file_path, _file)

        with open(full_path) as f:
            print(f"开始载入文件：{_file}")
            lines = f.readlines()

            start = None
            count = 0
            buf = []
            for row in lines:
                if count == 0:
                    count += 1
                    continue

                items = row.strip().split("\t")
                _datetime = datetime.fromtimestamp(int(items[1]))
                _datetime = _datetime.replace(tzinfo=get_localzone())

                bar = BarData(
                    gateway_name="DB",
                    symbol=items[0],
                    exchange=Exchange.HUOBI,
                    interval=Interval.MINUTE,
                    datetime=_datetime,
                    open_price=float(items[4]),
                    high_price=float(items[5]),
                    low_price=float(items[6]),
                    close_price=float(items[7]),
                    volume=float(items[8]),
                )

                buf.append(bar)
                count += 1
                if not start:
                    start = bar.datetime

            end = bar.datetime
            database_manager.save_bar_data(buf)

            print("插入数据", start, "-", end, "总数量：", count)


if __name__ == "__main__":

    corpus_path = r"D:\vnpy\vnpy2_pro\history_data\bar-btc"
    csv_load(corpus_path)
    print("同步完毕...")



