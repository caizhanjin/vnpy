# -*- coding:utf-8 -*-
import sqlite3
import time
import pandas as pd

from configs import load_settings

SETTINGS = load_settings()


class DatabaseSqlite(object):
    """
    sqlite 数据库操作类
    调用示例：
    from tools.database import DatabaseSqlite

    queryset = DatabaseSqlite()
    result = queryset.query_future(symbol='rb2001', begin_date='2019-11-11', end_date='2019-11-11')
    """
    database_path = SETTINGS["sqlite_db_path"]
    db_connect = object
    cursor = object

    def __init__(self, database_path=""):
        if database_path:
            self.database_path = database_path
        self.connect()

    def query_future(self, symbol='', interval='1m', begin_date=None,
                     end_date=None, fields=None, used_close=False):
        """
        @param: interval ('1m', 'd')
        """
        if fields is None:
            fields = ['symbol', 'datetime', 'interval', 'volume', 'open_price', 'high_price', 'close_price']
        fields_str = '' if len(fields) == 0 else ', '.join(fields)

        sql_base = f"SELECT {fields_str} FROM dbbardata"
        sql_order = " ORDER BY datetime ASC"
        sql_filter = f" WHERE interval='{interval}'"
        if symbol:
            sql_filter += f" AND symbol='{symbol}'"
        if begin_date:
            sql_filter += f" AND datetime>='{begin_date}'"
        if end_date:
            end_date += ' 23:59:59'
            sql_filter += f" AND datetime<='{end_date}'"

        self.cursor.execute(sql_base + sql_filter + sql_order)
        result = self.cursor.fetchall()

        if used_close:
            self.close()

        return result

    def import_csv_single(self, csv_file_path, symbol, exchange, interval="1m",
                          datetime="datetime", open="open", high="high", low="low", close="close", volume="volume"):
        """通过csv插入/更新数据库数据"""
        data_frame = pd.read_csv(csv_file_path)

        self.update_from_df(
            df=data_frame,
            exchange=exchange,
            symbol=symbol,
            interval=interval,
            datetime=datetime,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume
        )

        self.db_connect.commit()

    def update_from_df(self, df, exchange, symbol, interval,
                       datetime="datetime", time_handler_type="",
                       open="open", high="high", low="low", close="close", volume="volume"):
        """批量更新dataframe格式数据
        datetime格式：2019-5-10 13:00
        @:param time_handler_type：nanometre[纳米数] timestamp[时间戳]
        """
        print(f"开始导入：{symbol}")
        start_time = time.time()

        df.sort_values(by="datetime", ascending=True, inplace=True)

        for index, row in df.iterrows():
            date = row[datetime]
            if time_handler_type == "":
                date = date.replace('/', '-')
                date = date if len(date) <= 19 else date[: 19]
            elif time_handler_type == "nanometre":
                date = time.localtime(date / 1000000000)
                date = time.strftime("%Y-%m-%d %H:%M:%S", date)
            elif time_handler_type == "timestamp":
                date = time.localtime(int(date))
                date = time.strftime("%Y-%m-%d %H:%M:%S", date)

            self.update_one_row(
                exchange=exchange,
                symbol=symbol,
                interval=interval,
                datetime=date,
                open=float(row[open]),
                high=float(row[high]),
                low=float(row[low]),
                close=float(row[close]),
                volume=float(row[volume])
            )

        self.db_connect.commit()
        print(f"{symbol} 导入完成，耗时 {time.time() - start_time} s")

    def update_one_row(self, exchange, symbol, interval, datetime,
                       open, high, low, close, volume):
        """更新/插入1条数据，
        注意：该方法中没有提交数据库"""
        query_sql = """
        SELECT COUNT(*) FROM dbbardata WHERE symbol='%s' AND interval='%s' AND datetime='%s'
        """ % (symbol, interval, datetime)
        self.cursor.execute(query_sql)
        count = self.cursor.fetchone()[0]

        if count > 0:
            update_sql = """
            UPDATE dbbardata 
            SET 
                volume=%s, open_price=%s, high_price=%s, low_price=%s, close_price=%s 
            WHERE 
                symbol='%s' AND interval='%s' AND datetime='%s'
            """ % (volume, open, high, low, close, symbol, interval, datetime)
            self.cursor.execute(update_sql)
        else:
            insert_sql = """
            insert into 
                dbbardata(symbol, exchange, datetime, interval, volume, open_interest, open_price, high_price, low_price, close_price)
            values 
                ('%s', '%s', '%s', '%s', %s, '%s', %s, %s, %s, %s)
            """ % (symbol, exchange, datetime, interval, volume, "", open, high, low, close)
            self.cursor.execute(insert_sql)

    def connect(self):
        self.db_connect = sqlite3.connect(self.database_path)
        self.cursor = self.db_connect.cursor()

    def close(self):
        self.cursor.close()
        self.db_connect.close()


if __name__ == "__main__":
    queryset = DatabaseSqlite()

    # 导入excel到数据库
    # DatabaseSqlite.import_csv_single(
    #     csv_file_path="C:\\self_vnpy\\history_data\\99\\FU99_SHFE.csv",
    #     symbol="FU99",
    #     exchange="SHFE",
    #     interval="1m"
    # )

    # queryset = DatabaseSqlite()
    result = queryset.query_future(symbol='BU99', begin_date='2013-10-1', end_date='2013-10-11')

    print("Finish test!")
