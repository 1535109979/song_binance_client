from a_songbo.binance_client.strategy_server.strategys.breakout import BreakoutStrategy
from a_songbo.binance_client.strategy_server.strategys.stop_cover import StopLoss


class StrategyProcess:

    def __init__(self, gateway, strategy_config):
        self.gateway = gateway
        self.td_gateway = gateway.td_gateway
        self.logger = self.gateway.logger
        self.strategy_config = strategy_config

        self.stop_loss_flag = False
        self.strategy_list = []

        self.load_strategy()

    def load_strategy(self):
        if self.strategy_config.get('stop_loss'):
            self.strategy_list.append(StopLoss(self, self.strategy_config['stop_loss']))
        if self.strategy_config.get('breakout'):
            self.strategy_list.append(BreakoutStrategy(self, self.strategy_config['breakout']))

    def on_quote(self, quote):
        for strategy in self.strategy_list:
            strategy.cal_indicator(quote)

        for strategy in self.strategy_list:
            strategy.cal_singal(quote)



