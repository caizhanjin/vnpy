import os
import sys

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_PATH)
if not os.path.exists("../.vntrader"):
    os.mkdir("../.vntrader")

import csv
from datetime import datetime
import time
from pytz import timezone
from tzlocal import get_localzone

from vnpy.trader.constant import Exchange
from vnpy.trader.database import database_manager
from vnpy.trader.object import TickData
import pandas as pd


def csv_load(file: str):
    """
    读取csv文件内容，并写入到数据库中
    """
    with open(file, "r") as f:
        reader = csv.DictReader(f)

        ticks = []
        start = None
        count = 0

        for item in reader:

            # generate datetime
            date = item["交易日"]
            second = item["最后修改时间"]
            millisecond = item["最后修改毫秒"]

            standard_time = date + " " + second + "." + millisecond
            dt = datetime.strptime(standard_time, "%Y%m%d %H:%M:%S.%f")

            # filter
            if time(15, 1) < dt.time() < time(20, 59):
                continue

            tick = TickData(
                symbol="RU88",
                datetime=dt,
                exchange=Exchange.SHFE,
                last_price=float(item["最新价"]),
                volume=float(item["持仓量"]),
                bid_price_1=float(item["申买价一"]),
                bid_volume_1=float(item["申买量一"]),
                ask_price_1=float(item["申卖价一"]),
                ask_volume_1=float(item["申卖量一"]),
                gateway_name="DB",
            )
            ticks.append(tick)

            # do some statistics
            count += 1
            if not start:
                start = tick.datetime

        end = tick.datetime
        database_manager.save_tick_data(ticks)

        print("插入数据", start, "-", end, "总数量：", count)


def run_load_csv():
    """
    遍历同一文件夹内所有csv文件，并且载入到数据库中
    """
    for _file in os.listdir(".."):
        if not _file.endswith(".csv"):
            continue
        print(f"载入文件：{_file}")
        csv_load(_file)


if __name__ == "__main__":
    # run_load_csv()

    corpus_path = r"/history_data/tick-btc2"

    for _file in os.listdir(corpus_path):
        full_path = os.path.join(corpus_path, _file)

        with open(full_path, "r") as f:
            print(f"开始载入文件：{_file}")

            lines = f.readlines()

            ticks = []
            start = None
            count = 0

            for row in lines:
                if count == 0:
                    count += 1
                    continue

                items = row.strip().split("\t")
                datetime = datetime.fromtimestamp(int(items[1]) / 1000)
                datetime = datetime.replace(tzinfo=get_localzone())

                tick = TickData(
                    symbol=items[2],
                    datetime=datetime,
                    exchange=Exchange.HUOBI,
                    last_price=float(items[3]),
                    volume=float(items[4]),
                    bid_price_1=float(items[3]),
                    bid_volume_1=float(items[4]),
                    ask_price_1=float(items[3]),
                    ask_volume_1=float(items[4]),
                    gateway_name="DB",
                )
                ticks.append(tick)

                # do some statistics
                count += 1
                if not start:
                    start = tick.datetime

            end = tick.datetime
            database_manager.save_tick_data(ticks)

            print("插入数据", start, "-", end, "总数量：", count)

