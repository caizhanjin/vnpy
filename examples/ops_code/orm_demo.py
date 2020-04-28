import json

from peewee import (
    AutoField,
    CharField,
    Database,
    FloatField,
    Model,
    SqliteDatabase
)

# 使用vn.py运行时目录的SQLite数据库
from vnpy.trader.utility import get_file_path
from vnpy.trader.setting import SETTINGS
path = get_file_path(SETTINGS["database.database"])

# 或者可以手动指定数据库位置
# path = "C:\\users\\administrator\\.vntrader\\database.db"   

# 创建数据库对象
db = SqliteDatabase(path)

# 创建数据ORM的类
class DbStrategyData(Model):
    """对应表为dbstrategydata"""

    id = AutoField()
    name = CharField()                          # 策略名
    pos = FloatField()                          # 净持仓
    variables = CharField(max_length=9999)      # 运行变量，JSON数据格式保存，最长9999字符
    
    class Meta:
        database = db
        indexes = ((("name",), True),)

# 连接数据库，并创建数据表
db.connect()
db.create_tables([DbStrategyData])

# 定义函数用于写入和读取
def save_strategy_data(name: str, variables: dict):
    """"""
    # 移除无需保存的字段
    variables.pop("inited")
    variables.pop("trading")

    # pos单独保存
    pos = variables.pop("pos")

    # 写入数据库
    d = {
        "name": name,
        "pos": pos,
        "variables": json.dumps(variables)
    }
    DbStrategyData.insert(d).on_conflict_replace().execute()

def load_strategy_data(name: str) -> dict:
    """"""
    # 数据库读取
    try:
        data = DbStrategyData.select().where(
            DbStrategyData.name == name
        ).get()
    # 找不到则返回空字典
    except DbStrategyData.DoesNotExist:
        return {}
        
    # 把pos放入字典
    variables = json.loads(data.variables)
    variables["pos"] = data.pos
    return variables