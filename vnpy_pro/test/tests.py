# -*- coding:utf-8 -*-
import pandas as pd
import pyecharts.options as opts
from pyecharts.charts import Line, Grid, Bar
from datetime import datetime
import os
import talib
from vnpy.trader.utility import get_folder_path, load_json
import numpy as np


def calculate_std(numpy_array, window_len, ddof=0):
    arr_len = numpy_array.size
    std_list = np.zeros(arr_len)
    for i in range(arr_len):
        if i >= window_len-1:
            item = numpy_array[i-4:i+1] if i != arr_len - 1 else numpy_array[i-4:]
            std_list[i] = item.std(ddof=ddof)

    return std_list


def main():
    test1 = np.array([9, 2, 4])
    test2 = np.array([3, 4, 1])
    test3 = test1 - test2
    test4 = np.abs(test3)
    test5 = sum(test4)
    pass


if __name__ == "__main__":
    main()
