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
    test = [3.0, 4.0, 6.0, 7.0, 39.0, 11.0, 3.0, 4.0, 6.0, 7.0, 3.09, 1.01]
    test = np.array(test)
    test1 = talib.STDDEV(test, 5)

    std_list = calculate_std(test, 5)
    std_list2 = calculate_std(test, 5, 1)

    print(test1[-5:])
    print(std_list[-5:])
    print(std_list2[-5:])

    pass


if __name__ == "__main__":
    main()
