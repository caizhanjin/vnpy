import json
import os

from .log_config import initialize_logging

BASE_PATH = os.path.dirname(__file__)
ROOT_PATH = os.path.dirname(BASE_PATH)
JSON_PATH = os.path.join(BASE_PATH, "json")

if not os.path.exists(JSON_PATH):
    os.makedirs(JSON_PATH)


def load_settings():
    SETTINGS_PATH = os.path.join(JSON_PATH, "settings.json")
    with open(SETTINGS_PATH, "r", encoding="utf8") as f:
        SETTINGS = json.load(f)

    if not os.path.exists(SETTINGS["tq_99_save"]):
        os.makedirs(SETTINGS["tq_99_save"])
    if not os.path.exists(SETTINGS["tq_99"]):
        os.makedirs(SETTINGS["tq_99"])

    return SETTINGS


def load_futures():
    FUTURES_PATH = os.path.join(JSON_PATH, "futures.json")
    with open(FUTURES_PATH, "r", encoding="utf8") as f:
        FUTURES = json.load(f)
    return FUTURES


def init_logging():
    """初始化log配置"""
    initialize_logging(ROOT_PATH)
