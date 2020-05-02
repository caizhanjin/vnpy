from pathlib import Path

from vnpy.trader.app import BaseApp
from vnpy.trader.constant import Direction
from vnpy.trader.object import TickData, BarData, TradeData, OrderData
from vnpy.trader.utility import BarGenerator, ArrayManager

from vnpy.app.cta_strategy.base import APP_NAME, StopOrder
from vnpy.app.cta_strategy.template import CtaTemplate, CtaSignal, TargetPosTemplate
from vnpy_pro.app.cta_strategy.engine import CtaEngine

from .engine import CtaEnginePro


class CtaStrategyAppPro(BaseApp):
    """"""

    app_name = APP_NAME
    app_module = __module__
    app_path = Path(__file__).parent
    display_name = "CTA策略"
    engine_class = CtaEnginePro
    widget_name = "CtaManager"
    icon_name = "cta.ico"
