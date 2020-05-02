from datetime import datetime
import os

from vnpy.app.cta_strategy.engine import CtaEngine
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.event import Event, EventEngine
from vnpy.trader.utility import get_folder_path


class CtaEnginePro(CtaEngine):

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__(main_engine, event_engine)

    def send_report_email(self, subject="账号报表"):
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
            strategy_title = key + "_" + value["class_name"] + "_" + value["vt_symbol"]
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
                variate_body += f"<td>{variate_value}</td>"
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



