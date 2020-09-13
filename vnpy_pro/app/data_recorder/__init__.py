from vnpy.app.data_recorder import DataRecorderApp

from .engine import RecorderEnginePro


class DataRecorderAppPro(DataRecorderApp):
    engine_class = RecorderEnginePro

