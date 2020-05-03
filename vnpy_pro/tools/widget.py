import logging
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


if __name__ == '__main__':
    default_logger = get_logger()
    default_logger2 = get_logger()
    default_logger.info("hello world.")
    pass
