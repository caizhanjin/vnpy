import json
from datetime import datetime, time

from peewee import (
    AutoField,
    CharField,
    Database,
    FloatField,
    DateTimeField,
    Model,
    SqliteDatabase
)

from vnpy.trader.constant import Interval, Exchange

# 使用vn.py运行时目录的SQLite数据库
from vnpy.trader.utility import get_file_path
from vnpy.trader.setting import SETTINGS
path = get_file_path(SETTINGS["database.database"])

# 或者可以手动指定数据库位置
# path = "C:\\users\\administrator\\.vntrader\\database.db"   

# 创建数据库对象
db = SqliteDatabase(path)

# 创建数据ORM的类
class DbBarData(Model):
    """
    Candlestick bar data for database storage.

    Index is defined unique with datetime, interval, symbol
    """

    id = AutoField()
    symbol: str = CharField()
    exchange: str = CharField()
    datetime: datetime = DateTimeField()
    interval: str = CharField()

    volume: float = FloatField()
    open_interest: float = FloatField()
    open_price: float = FloatField()
    high_price: float = FloatField()
    low_price: float = FloatField()
    close_price: float = FloatField()

    class Meta:
        database = db
        indexes = ((("symbol", "exchange", "interval", "datetime"), True),)


# 连接数据库，并创建数据表
db.connect()
db.create_tables([DbBarData])

# 设置清洗参数
interval = Interval.MINUTE
symbol = "IF000"
exchange = Exchange.CFFEX
start = datetime(2010, 4, 20)
end = datetime.now()

# 读取数据
s = (
    DbBarData.select()
        .where(
        (DbBarData.symbol == symbol)
        & (DbBarData.exchange == exchange.value)
        & (DbBarData.interval == interval.value)
        & (DbBarData.datetime >= start)
        & (DbBarData.datetime <= end)
    )
    .order_by(DbBarData.datetime)
)

# 遍历检查
market_open = time(9, 30)
market_close = time(15, 0)

for db_bar in s:
    delete = False

    # 检查最低价是否为0
    if db_bar.low_price == 0:
        delete = True

    # 检查最高价是否过高（超过100万）
    if db_bar.high_price > 1000000:
        delete = True

    # 检查时间
    bar_time = db_bar.datetime.time()
    if bar_time < market_open:
        delete = True

    if bar_time > market_close:
        delete = True

    # 删除异常数据
    if delete:
        print(f"发现异常数据{db_bar.datetime} {db_bar.open_price} {db_bar.high_price} {db_bar.low_price} {db_bar.close_price}，已经删除")
        db_bar.delete_instance()

print("数据清洗完成")
