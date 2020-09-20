import os
import sys

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(ROOT_PATH)
if not os.path.exists(".vntrader"):
    os.mkdir(".vntrader")

import multiprocessing
from time import sleep
from datetime import datetime, time
from logging import INFO, DEBUG
from vnpy.trader.utility import load_json

from vnpy.event import EventEngine
from vnpy.trader.setting import SETTINGS
from vnpy.trader.engine import MainEngine

from vnpy.gateway.ctp import CtpGateway
from vnpy.app.cta_strategy.base import EVENT_CTA_LOG
from vnpy.app.data_recorder import DataRecorderApp

from vnpy_pro.app.data_recorder import DataRecorderAppPro
from vnpy_pro.app.cta_strategy import CtaStrategyAppPro
from vnpy_pro.tools.widget import get_logger
from vnpy_pro.data.download_data import download_data_from_tdx

SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True

default_logger = get_logger(
    level=SETTINGS["log.level"],
    is_console=SETTINGS["log.console"]
)
ctp_setting = load_json("connect_ctp.json")

trade_data = load_json("trade_data.json")
futures = trade_data["trade_futures"]


def run_child():
    SETTINGS["log.file"] = True

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(CtpGateway)
    cta_engine = main_engine.add_app(CtaStrategyAppPro)

    log_engine = main_engine.get_engine("log")
    event_engine.register(EVENT_CTA_LOG, log_engine.process_log_event)

    main_engine.connect(ctp_setting, "CTP")
    sleep(5)

    # 录制行情和从数据源下载数据
    download_data_from_tdx(futures, back_days=5)
    main_engine.add_app(DataRecorderAppPro)
    main_engine.write_log("启动数据录制")
    sleep(60)

    cta_engine.init_engine()
    cta_engine.init_all_strategies()
    sleep(360)
    main_engine.write_log("CTA策略全部初始化")

    cta_engine.start_all_strategies()
    main_engine.write_log("CTA策略全部启动")

    cta_engine.send_run_report_email("账号1监控报表")  # 完成启动后，发送监控报表

    day_close_time1 = time(15, 2)
    day_close_time2 = time(15, 5)
    day_close_time3 = time(15, 6)
    day_close_time4 = time(15, 10)

    night_close_time1 = time(2, 40)
    night_close_time2 = time(2, 45)

    lock1 = False
    lock2 = False
    lock3 = False
    while True:
        current_time1 = datetime.now().time()
        # 实例交易数据保存；资金曲线&策略评估指标更新
        if ((day_close_time1 <= current_time1 <= day_close_time4) or
            (night_close_time1 <= current_time1 <= night_close_time2)) \
                and not lock1:
            cta_engine.save_all_trade_data()
            main_engine.write_log("实例交易数据保存成功")
            cta_engine.update_all_daily_results()
            main_engine.write_log("实例资金曲线&策略评估指标更新成功")
            lock1 = True

        # 发送实例评估报表
        if (day_close_time2 <= current_time1 <= day_close_time4) and not lock2:
            cta_engine.send_evaluate_report_email("账号1实例评估报表")
            lock2 = True

        # 更新K线图完毕
        if (day_close_time3 <= current_time1 <= day_close_time4) and not lock3:
            cta_engine.update_all_k_line()
            main_engine.write_log("CTA更新K线图完毕")
            lock3 = True

        sleep(1)


def run_parent():
    default_logger.info("[主进程]启动守护父进程")

    DAY_START = time(8, 50)
    DAY_END = time(15, 20)

    NIGHT_START = time(20, 50)
    NIGHT_END = time(2, 45)

    child_process = None

    while True:
        current_time = datetime.now().time()
        week_day = datetime.now().weekday() + 1
        trading = False

        if (
            ((DAY_START <= current_time <= DAY_END)
             or (current_time >= NIGHT_START)
             or (current_time <= NIGHT_END))
            and week_day < 6
        ):
            trading = True
        trading = True

        if trading and child_process is None:
            child_process = multiprocessing.Process(target=run_child)
            child_process.start()
            default_logger.info("[主进程]启动子进程")

        # 非记录时间则退出子进程
        if not trading and child_process is not None:
            child_process.terminate()
            child_process.join()
            child_process = None
            default_logger.info("[主进程]关闭子进程")

        sleep(5)


if __name__ == "__main__":
    run_parent()
