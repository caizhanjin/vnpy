from pyecharts.charts import Line, Grid, Bar, Kline
import pyecharts.options as opts
import numpy as np
import pandas as pd
import os
from functools import wraps


def draw_daily_results_chart(daily_df, save_path):
    """绘制资金曲线图"""
    date_list = daily_df.index.values.tolist()
    balance_list = daily_df.balance.values.tolist()
    draw_down_list = daily_df.drawdown.values.tolist()
    net_pnl_list = daily_df.net_pnl.values.tolist()

    line1 = (
        Line()
        .add_xaxis(xaxis_data=date_list)
        .add_yaxis(
            series_name="Balance",
            y_axis=balance_list,
            label_opts=opts.LabelOpts(is_show=False),
            linestyle_opts=opts.LineStyleOpts(width=2),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="回测资金曲线", pos_left="center"),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="cross",
                background_color="rgba(245, 245, 245, 0.8)",
                border_width=1,
                border_color="#ccc",
                textstyle_opts=opts.TextStyleOpts(color="#000"),
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                boundary_gap=False,
                axisline_opts=opts.AxisLineOpts(is_on_zero=True),
            ),
            legend_opts=opts.LegendOpts(pos_left="1%"),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                is_scale=True,
                splitline_opts=opts.SplitLineOpts(is_show=True),
            ),
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
            datazoom_opts=[
                opts.DataZoomOpts(range_start=0, range_end=100),
                opts.DataZoomOpts(type_="inside", range_start=0, range_end=100, xaxis_index=[0, 1, 2]),
            ],
        )
    )

    line2 = (
        Line()
        .set_global_opts(
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                boundary_gap=False,
                axisline_opts=opts.AxisLineOpts(is_on_zero=True),
                position="top",
                axislabel_opts=opts.LabelOpts(is_show=False),
            ),
            legend_opts=opts.LegendOpts(pos_left="9%"),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                is_scale=True,
                splitline_opts=opts.SplitLineOpts(is_show=True),
            ),
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
        )
        .add_xaxis(xaxis_data=date_list)
        .add_yaxis(
            series_name="Draw Down",
            y_axis=draw_down_list,
            label_opts=opts.LabelOpts(is_show=False),
            areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
        )
    )

    bar3 = (
        Bar()
        .set_global_opts(
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                boundary_gap=False,
                axisline_opts=opts.AxisLineOpts(is_on_zero=True),
                axislabel_opts=opts.LabelOpts(is_show=False),
            ),
            legend_opts=opts.LegendOpts(pos_left="19%"),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                is_scale=True,
                splitline_opts=opts.SplitLineOpts(is_show=True),
            ),
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
        )
        .add_xaxis(xaxis_data=date_list)
        .add_yaxis(series_name="Daily Pnl", yaxis_data=net_pnl_list, label_opts=opts.LabelOpts(is_show=False))
    )

    (
        Grid(init_opts=opts.InitOpts(width="100%", height="720px"))
        .add(chart=line1, grid_opts=opts.GridOpts(pos_left=50, pos_right=50, height="35%"))
        .add(
            chart=line2,
            grid_opts=opts.GridOpts(pos_left=50, pos_right=50, pos_top="48%", height="20%"),
        )
        .add(
            chart=bar3,
            grid_opts=opts.GridOpts(pos_left=50, pos_right=50, pos_top="71%", height="20%"),
        )
        .render(os.path.join(save_path, "daily_results.html"))
    )


def chart_data_to_df(func):
    """获取df"""
    @wraps(func)
    def inner(self, *args, **kwargs):
        if self.df.empty:
            columns = ["datetime", "open", "high", "low", "close", "volume"].extend(self.extend_field)
            self.df = pd.DataFrame(self.list_dict, columns=columns)
        return func(self, *args, **kwargs)
    return inner


class KLineChart(object):
    """K线数据可视化"""
    def __init__(self, extend_field=None, is_fixed_size=False, fixed_size: int = 200):
        if extend_field is None:
            extend_field = []

        self.extend_field = extend_field
        self.is_fixed_size = is_fixed_size
        self.df = pd.DataFrame()

        self.trade_list = []
        if self.is_fixed_size:
            self.list_dict = {
                "datetime": ["" for i in range(fixed_size)],
                "open": np.zeros(fixed_size),
                "high": np.zeros(fixed_size),
                "low": np.zeros(fixed_size),
                "close": np.zeros(fixed_size),
                "volume": np.zeros(fixed_size)
            }
            for field in extend_field:
                self.list_dict.setdefault(field, np.zeros(fixed_size))
        else:
            self.list_dict = {
                "datetime": [],
                "open": [],
                "high": [],
                "low": [],
                "close": [],
                "volume": []
            }
            for field in self.extend_field:
                self.list_dict.setdefault(field, [])

    def update_bar(self, bar, **kwargs):
        if self.is_fixed_size:
            self.list_dict["datetime"][:-1] = self.list_dict["datetime"][1:]
            self.list_dict["open"][:-1] = self.list_dict["open"][1:]
            self.list_dict["high"][:-1] = self.list_dict["high"][1:]
            self.list_dict["low"][:-1] = self.list_dict["low"][1:]
            self.list_dict["close"][:-1] = self.list_dict["close"][1:]
            self.list_dict["volume"][:-1] = self.list_dict["volume"][1:]

            self.list_dict["datetime"][-1] = bar.datetime.strftime("%Y-%m-%d %H:%M:%S")
            self.list_dict["open"][-1] = bar.open_price
            self.list_dict["high"][-1] = bar.high_price
            self.list_dict["low"][-1] = bar.low_price
            self.list_dict["close"][-1] = bar.close_price
            self.list_dict["volume"][-1] = bar.volume

            for field in self.extend_field:
                self.list_dict[field][:-1] = self.list_dict[field][1:]
                self.list_dict[field][-1] = kwargs[field]
        else:
            self.list_dict["datetime"].append(bar.datetime.strftime("%Y-%m-%d %H:%M:%S"))
            self.list_dict["open"].append(bar.open_price)
            self.list_dict["high"].append(bar.high_price)
            self.list_dict["low"].append(bar.low_price)
            self.list_dict["close"].append(bar.close_price)
            self.list_dict["volume"].append(bar.volume)

            for field in self.extend_field:
                self.list_dict[field].append(kwargs[field])

    @chart_data_to_df
    def save_csv(self, save_path=""):
        self.df.to_csv(os.path.join(save_path, "KLineChart.csv"), encoding="utf_8_sig")

    def read_csv_to_df(self, path: str):
        self.df = pd.read_csv(path)

    @chart_data_to_df
    def draw_chart(self, save_path="", kline_title="买卖点K线图"):
        datetime_array = self.df.datetime.tolist()
        volume_array = self.df.volume.tolist()
        # open close low high
        kline_data = self.df[["open", "close", "low", "high"]].values.tolist()
        point_list = []

        for trade in self.trade_list:
            # 开多
            trade_datetime = trade.datetime.strftime("%Y-%m-%d %H:%M:%S")
            if trade.direction.value == "多" and trade.offset.value == "开":
                point_list.append(opts.MarkPointItem(
                    name="开多",
                    coord=[trade_datetime, trade.price],
                    value="开多",
                    itemstyle_opts=opts.ItemStyleOpts(color="#ef232a")
                ))
            # 开空
            elif trade.direction.value == "空" and trade.offset.value == "开":
                point_list.append(opts.MarkPointItem(
                    name="开空",
                    coord=[trade_datetime, trade.price],
                    value="开空",
                    itemstyle_opts=opts.ItemStyleOpts(color="#ef232a")
                ))
            # 平多
            elif trade.direction.value == "多" and \
                (trade.offset.value == "平" or trade.offset.value == "平今" or trade.offset.value == "平昨"):
                point_list.append(opts.MarkPointItem(
                    name="平空",
                    coord=[trade_datetime, trade.price],
                    value="平空",
                    itemstyle_opts=opts.ItemStyleOpts(color="#14b143")
                ))
            # 平空
            elif trade.direction.value == "空" and \
                 (trade.offset.value == "平" or trade.offset.value == "平今" or trade.offset.value == "平昨"):
                point_list.append(opts.MarkPointItem(
                    name="平多",
                    coord=[trade_datetime, trade.price],
                    value="平多",
                    itemstyle_opts=opts.ItemStyleOpts(color="#14b143")
                ))

        kline = (
            Kline()
            .add_xaxis(xaxis_data=datetime_array)
            .add_yaxis(
                series_name="Kline",
                y_axis=kline_data,
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#ef232a",
                    color0="#14b143",
                    border_color="#ef232a",
                    border_color0="#14b143",
                ),
                markpoint_opts=opts.MarkPointOpts(
                    data=point_list
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=kline_title, pos_left="2%", pos_top="1%"),
                legend_opts=opts.LegendOpts(
                    is_show=True, pos_top=10, pos_left="center"
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=False,
                        type_="inside",
                        xaxis_index=[0, 1],
                        range_start=0,
                        range_end=100,
                    ),
                    opts.DataZoomOpts(
                        is_show=True,
                        xaxis_index=[0, 1],
                        type_="slider",
                        pos_top="88%",
                        range_start=0,
                        range_end=100,
                    ),
                ],
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitline_opts=opts.SplitLineOpts(is_show=True)
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                    background_color="rgba(245, 245, 245, 0.8)",
                    border_width=1,
                    border_color="#ccc",
                    textstyle_opts=opts.TextStyleOpts(color="#000"),
                ),
                visualmap_opts=opts.VisualMapOpts(
                    is_show=False,
                    dimension=2,
                    series_index=5,
                    is_piecewise=True,
                    pieces=[
                        {"value": 1, "color": "#00da3c"},
                        {"value": -1, "color": "#ec0000"},
                    ],
                ),
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                    label=opts.LabelOpts(background_color="#777"),
                ),
            )
        )

        bar = (
            Bar()
            .add_xaxis(xaxis_data=datetime_array)
            .add_yaxis(
                series_name="Volume",
                yaxis_data=volume_array,
                xaxis_index=1,
                yaxis_index=1,
                label_opts=opts.LabelOpts(is_show=False),
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    is_scale=True,
                    grid_index=1,
                    boundary_gap=False,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                    axislabel_opts=opts.LabelOpts(is_show=False),
                    split_number=20,
                    min_="dataMin",
                    max_="dataMax",
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=1,
                    is_scale=True,
                    split_number=2,
                    axislabel_opts=opts.LabelOpts(is_show=False),
                    axisline_opts=opts.AxisLineOpts(is_show=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )

        if len(self.extend_field) > 0:
            line = (
                Line()
                .add_xaxis(xaxis_data=datetime_array)
                .set_global_opts(
                    xaxis_opts=opts.AxisOpts(type_="category"),
                    legend_opts=opts.LegendOpts(
                       is_show=True
                    ),
                )
            )
            for field in self.extend_field:
                field_value_array = self.df[field].tolist()
                line.add_yaxis(
                    series_name=field,
                    y_axis=field_value_array,
                    is_smooth=True,
                    is_hover_animation=False,
                    linestyle_opts=opts.LineStyleOpts(width=2, opacity=0.8),
                    label_opts=opts.LabelOpts(is_show=False),
                )

            # Kline And Line
            kline = kline.overlap(line)

        # Grid Overlap + Bar
        grid_chart = Grid(
            init_opts=opts.InitOpts(
                width="100%",
                height="760px",
                animation_opts=opts.AnimationOpts(animation=False),
            )
        )
        grid_chart.add(
            kline,
            grid_opts=opts.GridOpts(pos_left="3.5%", pos_right="3.5%", height="60%"),
        )
        grid_chart.add(
            bar,
            grid_opts=opts.GridOpts(
                pos_left="3.5%", pos_right="3.5%", pos_top="70%", height="16%"
            ),
        )

        grid_chart.render(os.path.join(save_path, "KLineChart.html"))


if __name__ == '__main__':
    test_chart = KLineChart()
    test_chart.read_csv_to_df(r"D:\vnpy\vnpy2_pro\worktable\KLineChart.csv")
    test_chart.draw_chart()
    pass
