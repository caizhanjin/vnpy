from datetime import datetime
import os

from vnpy.app.cta_strategy.engine import CtaEngine
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.event import Event, EventEngine
from vnpy.trader.utility import get_folder_path, load_json, TEMP_DIR


class CtaEnginePro(CtaEngine):

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__(main_engine, event_engine)

    def send_run_report_email(self, subject="监控报表"):
        """策略运行/监控报表"""
        subject = subject + datetime.now().strftime("%Y-%m-%d %H:%M")

        log_content = ""
        log_path = os.path.join(
            get_folder_path("log"),
            f"vt_{datetime.now().strftime('%Y%m%d')}.log"
        )
        if os.path.exists(log_path):
            with open(log_path, mode="r", encoding="utf8") as f:
                for log_line in f.readlines():
                    _log_line = log_line.rstrip("\n")
                    log_content += f"<div>{_log_line}</div>"

        strategy_content = ""
        for key, value in self.strategy_setting.items():
            strategy_title = key + "_" + value["class_name"] + "_" + value["vt_symbol"].split(".")[0]
            param_header = ""
            param_body = ""
            variate_header = ""
            variate_body = ""
            for param_name, param_value in value["setting"].items():
                if param_name == "class_name":
                    continue
                param_header += f"<th>{param_name}</th>"
                param_body += f"<td>{param_value}</td>"
            for variate_name, variate_value in self.strategy_data[key].items():
                variate_header += f"<th>{variate_name}</th>"
                variate_body += f"<td>{range(variate_value, 2)}</td>"
            strategy_content += f"""
            <div style="margin-top: 10px;">
                {strategy_title}:
                <table border="1px">
                    <tr>{param_header}</tr>
                    <tr>{param_body}</tr>
                </table>
                <table border="1px">
                    <tr>{variate_header}</tr>
                    <tr>{variate_body}</tr>
                </table>
            </div>
            """

        content = f"""
        <div>
            <strong>账号详情：</strong>
            <table border="1px">
                <tr>
                  <th>余额</th>
                  <th>冻结</th>
                  <th>可用</th>
                </tr>
                <tr>
                  <td>100000</td>
                  <td>100000</td>
                  <td>100000</td>
                </tr>
            </table>
            <table border="1px">
                <tr>
                  <th>合约</th>
                  <th>方向</th>
                  <th>数量</th>
                  <th>盈亏</th>
                </tr>
                <tr>
                  <td>100000</td>
                  <td>100000</td>
                  <td>100000</td>
                  <td>100000</td>
                </tr>
                <tr>
                  <td>100000</td>
                  <td>100000</td>
                  <td>100000</td>
                  <td>100000</td>
                </tr>
            </table>
        </div>
        <br>
        <div>
            <strong>策略实例：</strong>
            {strategy_content}
        </div>
        <br>
        <div>
            <strong>运行log：</strong>
            <div>{log_content}</div>
        </div>
        """ + "<style>td {text-align:center;}</style>"

        self.main_engine.send_email_html(
            subject=subject,
            content=content
        )

    def send_evaluate_report_email(self, subject="实例评估报表"):
        """发送策略评估报表"""
        subject = subject + datetime.now().strftime("%Y-%m-%d %H:%M")

        statistics_list = [
            {"key": "start_date", "name": "首个交易日", "html": "<th>首个交易日</th>"},
            {"key": "end_date", "name": "最后交易日", "html": "<th>最后交易日</th>"},

            {"key": "total_days", "name": "总交易日", "html": "<th>总交易日</th>"},
            {"key": "profit_days", "name": "盈利交易日", "html": "<th>盈利交易日</th>"},
            {"key": "loss_days", "name": "亏损交易日", "html": "<th>亏损交易日</th>"},

            {"key": "capital", "name": "起始资金", "html": "<th>起始资金</th>"},
            {"key": "end_balance", "name": "结束资金", "html": "<th>结束资金</th>"},

            {"key": "total_return", "name": "总收益率", "html": "<th>总收益率</th>"},
            {"key": "annual_return", "name": "年化收益", "html": "<th>年化收益</th>"},
            {"key": "max_drawdown", "name": "最大回撤", "html": "<th>最大回撤</th>"},
            {"key": "max_ddpercent", "name": "百分比最大回撤", "html": "<th>百分比最大回撤</th>"},
            {"key": "max_drawdown_duration", "name": "最长回撤天数", "html": "<th>最长回撤天数</th>"},

            {"key": "total_net_pnl", "name": "总盈亏", "html": "<th>总盈亏</th>"},
            {"key": "total_commission", "name": "总手续费", "html": "<th>总手续费</th>"},
            {"key": "total_slippage", "name": "总滑点", "html": "<th>总滑点</th>"},
            {"key": "total_turnover", "name": "总成交金额", "html": "<th>总成交金额</th>"},
            {"key": "total_trade_count", "name": "总成交笔数", "html": "<th>总成交笔数</th>"},

            {"key": "daily_net_pnl", "name": "日均盈亏", "html": "<th>日均盈亏</th>"},
            {"key": "daily_commission", "name": "日均手续费", "html": "<th>日均手续费</th>"},
            {"key": "daily_slippage", "name": "日均滑点", "html": "<th>日均滑点</th>"},
            {"key": "daily_turnover", "name": "日均成交金额", "html": "<th>日均成交金额</th>"},
            {"key": "daily_trade_count", "name": "日均成交笔数", "html": "<th>日均成交笔数</th>"},

            {"key": "daily_return", "name": "日均收益率", "html": "<th>日均收益率</th>"},
            {"key": "return_std", "name": "收益标准差", "html": "<th>收益标准差</th>"},
            {"key": "sharpe_ratio", "name": "Sharpe Ratio", "html": "<th>Sharpe Ratio</th>"},
            {"key": "return_drawdown_ratio", "name": "收益回撤比", "html": "<th>收益回撤比</th>"},
        ]
        table_header_html = "<th>实例</th>"
        for key, value in self.strategy_setting.items():
            strategy_name = key + "_" + value["class_name"] + "_" + value["vt_symbol"].split(".")[0]
            table_header_html += "<td>" + strategy_name + "</td>"
            statistics_file = os.path.join(
                TEMP_DIR,
                "trade_data",
                strategy_name,
                "statistics.json"
            )
            if not os.path.exists(statistics_file):
                statistics_dict = {}
            else:
                statistics_dict = load_json(statistics_file)
            for item in statistics_list:
                if item["key"] in ["total_days", "profit_days", "loss_days", "max_drawdown_duration"]:
                    item["html"] += "<td>" + str(int(statistics_dict.get(item["key"], 0))) + "</td>"
                else:
                    item["html"] += "<td>" + str(statistics_dict.get(item["key"], 0)) + "</td>"

        statistics_html = ""
        for item in statistics_list:
            statistics_html += "<tr>" + item["html"] + "</tr>"
        # <strong>实例指标：</strong>
        statistics_html = f"""
        <div>
            <table border="1px" cellpadding="3.8">
                <tr>{table_header_html}</tr>
                {statistics_html}
            </table>
        </div>
        """ + "<style>td {text-align:center;}</style>"

        self.main_engine.send_email_html(
            subject=subject,
            content=statistics_html
        )

    def save_all_trade_data(self):
        for strategy_name in self.strategies.keys():
            try:
                self.save_trade_data(strategy_name)
            except Exception as error:
                self.write_log(f"{strategy_name}策略交易数据保存失败，error：{error}")

    def save_trade_data(self, strategy_name):
        """保存实例交易数据"""
        strategy = self.strategies[strategy_name]
        strategy.save_trade_data()

    def update_all_daily_results(self):
        for strategy_name in self.strategies.keys():
            try:
                self.save_trade_data(strategy_name)
            except Exception as error:
                self.write_log(f"{strategy_name}策略交易数据保存失败，error：{error}")

    def update_daily_results(self, strategy_name):
        strategy = self.strategies[strategy_name]
        strategy.calculate_and_chart_daily_results()
