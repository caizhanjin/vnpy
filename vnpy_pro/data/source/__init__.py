from vnpy.trader.setting import SETTINGS
from vnpy_pro.data.source.dataapi import SourceDataApi


if SETTINGS["data.source"] == "tdxdata":
    from vnpy_pro.data.source.tdxdata import tdxdata_client
    data_client: SourceDataApi = tdxdata_client
elif SETTINGS["data.source"] == "jqdata":
    from vnpy_pro.data.source.jqdata import jqdata_client
    data_client: SourceDataApi = jqdata_client
else:
    from vnpy.trader.rqdata import rqdata_client
    data_client: SourceDataApi = rqdata_client
