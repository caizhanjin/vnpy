import datetime

from vnpy.trader.object import HistoryRequest
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Interval, Exchange

from vnpy_pro.data.source.tdxdata import tdxdata_client
from vnpy.trader.utility import load_json


def download_data_from_tdx(download_futures, from_date=None, back_days=None):
    """
    :param download_futures: ["rb2009.SHFE"]
    :param from_date: 2020-7-8
    :param back_days:
    """
    if tdxdata_client.init():
        print("数据服务器登录成功")
    else:
        print("数据服务器登录失败")
        return

    for future in download_futures:
        _future = future.split(".")
        symbol = _future[0]
        exchange = Exchange.__dict__[_future[1]]
        interval = Interval.MINUTE

        if from_date:
            start = datetime.datetime.strptime(from_date, "%Y-%m-%d")
        else:
            bar = database_manager.get_newest_bar_data(symbol, exchange, interval)
            if bar:
                start = bar.datetime
            else:
                start = datetime.datetime(2012, 1, 1)
            if back_days:
                start = start.replace(tzinfo=None)
                _start = datetime.datetime.now() - datetime.timedelta(days=3)
                start = _start if start > _start else start

        # 下载数据
        req = HistoryRequest(
            symbol,
            exchange,
            start,
            datetime.datetime.now(),
            interval=interval
        )
        data = tdxdata_client.query_history(req)

        # 写入数据库
        if data:
            database_manager.save_bar_data(data)
            print(f"{symbol}更新完成：{data[0].datetime} -- {data[-1].datetime}")

# 更新contracts字典
# tdxdata_client.tdx_api.update_mi_contracts()


if __name__ == "__main__":
    # trade_data = load_json("trade_data.json")
    # futures = trade_data["trade_futures"]
    futures = ["rb2009.SHFE", "bu2009.SHFE"]
    download_data_from_tdx(futures, back_days=5)

