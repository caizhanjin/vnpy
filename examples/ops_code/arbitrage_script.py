from time import sleep
from vnpy.app.script_trader import ScriptEngine
from vnpy.trader.constant import Direction


def run(engine: ScriptEngine):
    """
    """
    # 设置参数
    leg1_symbol = "TF2006.CFFEX"
    leg2_symbol = "T2006.CFFEX"
    entry_level = 5         # 入场位置
    tick_add = 1            # 买卖超价Tick
    trading_size = 100000   # 交易数量

    vt_symbols = [leg1_symbol, leg2_symbol]

    # 订阅行情
    engine.subscribe(vt_symbols)

    # 初始化变量
    pos_data = {}
    target_data = {}

    for vt_symbol in vt_symbols:
        pos_data[vt_symbol] = 0
        target_data[vt_symbol] = 0

    # 持续运行，使用strategy_active来判断是否要退出程序
    while engine.strategy_active:
        # 获取行情
        leg1_tick = engine.get_tick(leg1_symbol)
        leg2_tick = engine.get_tick(leg2_symbol)

        # 计算交易目标
        # 开仓
        if not target_data[leg1_symbol]:
            if leg1_tick.bid_price_1 >= leg2_tick.ask_price_1 + entry_level:
                print(f"满足开仓条件，卖{leg1_symbol}，买{leg2_symbol}")
                target_data[leg1_symbol] = -trading_size
                target_data[leg2_symbol] = trading_size
            elif leg1_tick.ask_price_1 <= leg2_tick.bid_price_1 - entry_level:
                print(f"满足开仓条件，买{leg1_symbol}，卖{leg2_symbol}")
                target_data[leg1_symbol] = trading_size
                target_data[leg2_symbol] = -trading_size
        # 平仓
        else:
            if target_data[leg1_symbol] > 0:
                if leg1_tick.ask_price_1 <= leg2_tick.bid_price_1:
                    print("满足平仓条件")
                    target_data[leg1_symbol] = 0
                    target_data[leg2_symbol] = 0
            else:
                if leg1_tick.bid_price_1 >= leg2_tick.ask_price_1:
                    print("满足平仓条件")
                    target_data[leg1_symbol] = 0
                    target_data[leg2_symbol] = 0

        # 检查委托情况
        active_orders = engine.get_all_active_orders()
        if active_orders:
            print("当前存在活动委托，执行撤单")
            for order in active_orders:
                engine.cancel_order(order.vt_orderid)

            continue

        # 执行交易
        for vt_symbol in vt_symbols:
            pos = pos_data[vt_symbol]
            target = target_data[vt_symbol]
            diff = target - pos

            contract = engine.get_contract(vt_symbol)
            price_add = tick_add * contract.pricetick

            tick = engine.get_tick(vt_symbol)

            # 持仓和目标一致，无需交易
            if not diff:
                continue
            # 大于则买入
            elif diff > 0:
                # 有空头持仓，买入平仓
                if pos < 0:
                    engine.cover(
                        vt_symbol, tick.ask_price_1 + price_add, abs(diff)
                    )
                    print(f"cover {vt_symbol}")
                # 否则买入开仓
                else:
                    engine.buy(
                        vt_symbol, tick.ask_price_1 + price_add, abs(diff)
                    )
                    print(f"buy {vt_symbol}")
            # 小于则卖出
            elif diff < 0:
                # 有多头持仓，卖出平仓
                if pos > 0:
                    engine.sell(
                        vt_symbol, tick.bid_price_1 - price_add, abs(diff)
                    )
                    print(f"sell {vt_symbol}")
                # 否则卖出开仓
                else:
                    engine.short(
                        vt_symbol, tick.bid_price_1 - price_add, abs(diff)
                    )
                    print(f"short {vt_symbol}")

        # 等待进入下一轮
        sleep(10)


# 定义持仓查询函数
def get_net_pos(engine, vt_symbol):
    net_pos = 0

    long_position = engine.get_position(vt_symbol + "." + Direction.LONG.value)
    if long_position:
        net_pos += long_position.volume

    short_position = engine.get_position(vt_symbol + "." + Direction.SHORT.value)
    if short_position:
        net_pos -= short_position.volume

    return net_pos
