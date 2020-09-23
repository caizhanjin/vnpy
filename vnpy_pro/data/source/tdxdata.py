from datetime import timedelta, datetime
from typing import List

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, HistoryRequest

from vnpy_pro.data.source.dataapi import SourceDataApi
from vnpy_pro.data.tdx.tdx_future_data import TdxFutureData

INTERVAL_VT2JQ = {
    Interval.MINUTE: "1min",
    Interval.HOUR: "1hour",
    Interval.DAILY: "1day",
}

INTERVAL_ADJUSTMENT_MAP = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
    Interval.DAILY: timedelta()         # no need to adjust for daily bar
}


class TdxdataClient(SourceDataApi):
    """通达信数据源"""

    def __init__(self):
        self.tdx_api = TdxFutureData()
        self.inited = False

    def init(self, username="", password="", is_update_contracts=False):
        """
        is_update_contracts: 需不需要更新contracts
        """
        if self.tdx_api.connection_status:
            result = True
        else:
            result = self.tdx_api.connect()

        if is_update_contracts:
            self.tdx_api.update_mi_contracts()

        self.inited = result
        return result

    def query_history(self, req: HistoryRequest):
        symbol = req.symbol
        exchange = req.exchange
        interval = req.interval
        start = req.start
        end = req.end

        tdx_interval = INTERVAL_VT2JQ.get(interval)
        if not tdx_interval:
            return None

        # For adjust timestamp from bar close point (RQData) to open point (VN Trader)
        adjustment = INTERVAL_ADJUSTMENT_MAP[interval]

        # For querying night trading period data
        end += timedelta(1)

        result, bar_data = self.tdx_api.get_bars(
            symbol=symbol,
            period=tdx_interval,
            start_dt=start,
            end_dt=end
        )

        data: List[BarData] = []

        if bar_data is not None:
            for row in bar_data:
                bar = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    interval=interval,
                    datetime=row.datetime.to_pydatetime() - adjustment,
                    open_price=row.open_price,
                    high_price=row.high_price,
                    low_price=row.low_price,
                    close_price=row.close_price,
                    volume=row.volume,
                    open_interest=row.open_interest,
                    gateway_name=row.gateway_name
                )
                data.append(bar)

        return data


tdxdata_client = TdxdataClient()

if __name__ == "__main__":
    tdxdata_client = TdxdataClient()

    req = HistoryRequest(symbol='SR2009',
                         exchange=Exchange.CZCE,
                         start=datetime(2020, 4, 1, 16, 13, 49, 896628),
                         end=datetime(2020, 4, 11, 16, 13, 49, 896628),
                         interval=Interval.MINUTE)
    test_data = tdxdata_client.query_history(req)

    pass

