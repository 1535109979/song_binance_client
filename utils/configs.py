import platform

system = platform.system()


class Configs:
    if system == 'Darwin':
        root_fp = '/Users/edy/byt_pub/'

        api_config = {
                'recvWindow': '5000',
                'stream_url': 'wss://fstream.binance.com',
                'base_url': 'https://fapi.binance.com',
                'api_key': '8kHJ8xMwb8wZkrTy17IVOym4CDo5qS6JFP8suvpsDaWCqjuBuIAn29HFYKuQM1bE',
                'secret_key': 'uUH1X2sz5jnMVhL44zxHiphnxhoQ5swPs62gFg4JFLCRayWwFr2MZJm9dJlaM2WK',
                # 'api_key': 'lfFQPMO2aNVuq6RI8h4PzPObfLQjWsvPcJ8zpfbYb0TJZV3zFmuxTTN7z0aj7lnc',
                # 'secret_key': '9x0h75LjgFw7QwAa7yYFOvDOpN4VKPx4i6iRiicTadZpTLMrTqW4uetm1GSg8srk',
                }

    elif system == 'Linux':
        root_fp = '/logs/a_songbo/'
        api_config = {
            'recvWindow': '5000',
            'stream_url': 'wss://fstream.binance.com',
            'base_url': 'https://fapi.binance.com',
            # 'api_key': '8kHJ8xMwb8wZkrTy17IVOym4CDo5qS6JFP8suvpsDaWCqjuBuIAn29HFYKuQM1bE',
            # 'secret_key': 'uUH1X2sz5jnMVhL44zxHiphnxhoQ5swPs62gFg4JFLCRayWwFr2MZJm9dJlaM2WK',
            'api_key': 'lfFQPMO2aNVuq6RI8h4PzPObfLQjWsvPcJ8zpfbYb0TJZV3zFmuxTTN7z0aj7lnc',
            'secret_key': '9x0h75LjgFw7QwAa7yYFOvDOpN4VKPx4i6iRiicTadZpTLMrTqW4uetm1GSg8srk',
        }

    strategy_list = [
        {'instrument': 'EOSUSDT',
         'strategy_name': 'breakout',
         'cash': 10,
         'open_direction': 'LONG',
         'windows': 400,
         'open_volume': 30,
         'interval_period': 120,
         'roll_mean_period': 200,
         'stop_loss': 0
         },

        # {'instrument': 'LTCUSDT',
        #  'strategy_name': 'breakout',
        #  'cash': 10,
        #  'open_direction': 'LONG',
        #  'windows': 400,
        #  'open_volume': 30,
        #  'interval_period': 120,
        #  'roll_mean_period': 200,
        #  'stop_loss': 0
        #  },

    ]


