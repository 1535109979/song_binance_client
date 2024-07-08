

class Configs:
    root_fp = '/Users/edy/byt_pub/'

    strategy_list = [
        {'instrument': 'EOSUSDT',
         'breakout': {'open_direction': 'LONG', 'windows': 400, 'open_volume': 20,
                    'interval_period': 120, 'roll_mean_period': 200},
         'stop_loss': {'stop_loss_rate': 0.1}
         },
        # {'instrument': 'LTCUSDT',
        #  'params': {'open_direction': 'LONG', 'windows': 30, 'open_volume': 30,
        #             'interval_period': 120, 'roll_mean_period': 200}
        #  }
    ]

