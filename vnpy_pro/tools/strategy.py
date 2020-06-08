

class DonAnData(object):
    """唐奇安通道 data"""
    entry_up: float = 0
    entry_down: float = 0

    exit_up: float = 0
    exit_down: float = 0

    # 趋势 1上升 0震荡 -1下降
    trend_status: int = 0

    def __init__(self, entry_length, exit_length):
        self.entry_length = entry_length
        self.exit_length = exit_length

    def update_bar_data(self, am_bars):
        self.entry_up, self.entry_down = am_bars.donchian(self.entry_length)
        self.exit_up, self.exit_down = am_bars.donchian(self.exit_length)

    def update_close_price(self, close_price):
        if close_price > self.entry_up:
            self.trend_status = 1
        elif close_price < self.entry_down:
            self.trend_status = -1

        if (self.trend_status == 1 and close_price < self.exit_down) or \
                (self.trend_status == -1 and close_price > self.exit_up):
            self.trend_status = 0
