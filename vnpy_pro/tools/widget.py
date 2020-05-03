import csv
import logging
import os
from datetime import datetime
from logging import INFO, DEBUG
from typing import Dict

from vnpy.trader.event import EVENT_LOG
from vnpy.trader.setting import SETTINGS
from vnpy.trader.utility import get_folder_path


file_handlers: Dict[str, logging.FileHandler] = {}


def get_logger(logger_name="default_logger", file_path=None,
               level=INFO,
               format_s="%(asctime)s  %(levelname)s: %(message)s",
               is_console=True, is_file=True):
    current_logger = logging.getLogger(logger_name)
    current_logger.setLevel(level)
    formatter = logging.Formatter(format_s)
    if is_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        current_logger.addHandler(console_handler)
    if is_file:
        if not file_path:
            today_date = datetime.now().strftime("%Y%m%d")
            filename = f"vt_{today_date}.log"
            log_path = get_folder_path("log")
            file_path = log_path.joinpath(filename)

        file_handler = file_handlers.get(file_path, None)
        if file_handler is None:
            file_handler = logging.FileHandler(
                file_path, mode="a", encoding="utf8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
        current_logger.addHandler(file_handler)

    return current_logger


def csv_add_rows(data_list, header, csv_path):
    """csv末尾追加形式内容"""
    is_exist = os.path.exists(csv_path)

    with open(file=csv_path, mode="a+", newline="", encoding="utf8") as f:
        csv_file = csv.writer(f)
        if not is_exist:
            csv_file.writerow(header)
        csv_file.writerows(data_list)


if __name__ == '__main__':
    dict_list2 = [
        {"test": 55, "test3": 5533},
        {"test": 55, "test3": 5533},
    ]
    csv_add_rows(dict_list2, ["test3", "test"], "tests.csv")

    pass
