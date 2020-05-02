# -*- coding:utf-8 -*-
import pandas as pd
import pyecharts.options as opts
from pyecharts.charts import Line, Grid, Bar
from datetime import datetime

from vnpy.trader.utility import get_folder_path
import os


def main():
    log_path = os.path.join(
        get_folder_path("log"),
        f"vt_{datetime.now().strftime('%Y%m%d')}.log"
    )

    if os.path.exists(log_path):
        with open(log_path, mode="r", encoding="utf8") as f:
            content = f.read()
            print(content)
    else:
        content = ""

    pass


if __name__ == "__main__":
    main()
