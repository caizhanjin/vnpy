"""外部行情数据接口"""
from abc import ABC, abstractmethod

from vnpy.trader.object import HistoryRequest


class SourceDataApi(ABC):
    """
    抽象数据接口
    """

    @abstractmethod
    def init(self, username="", password=""):
        """
        初始化行情数据接口
        :param username: 用户名
        :param password: 密码
        :return:
        """
        pass

    @abstractmethod
    def query_history(self, req: HistoryRequest):
        """
        查询历史数据接口
        :param req:
        :return:
        """
        pass
