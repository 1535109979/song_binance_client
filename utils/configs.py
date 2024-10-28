import logging
import platform

system = platform.system()


class Configs:
    dr = 0.003
    signal_reserve_time = 600

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
        root_fp = '/a_songbo/'
        api_config = {
            'recvWindow': '5000',
            'stream_url': 'wss://fstream.binance.com',
            'base_url': 'https://fapi.binance.com',
            'api_key': '8kHJ8xMwb8wZkrTy17IVOym4CDo5qS6JFP8suvpsDaWCqjuBuIAn29HFYKuQM1bE',
            'secret_key': 'uUH1X2sz5jnMVhL44zxHiphnxhoQ5swPs62gFg4JFLCRayWwFr2MZJm9dJlaM2WK',
            # 'api_key': 'lfFQPMO2aNVuq6RI8h4PzPObfLQjWsvPcJ8zpfbYb0TJZV3zFmuxTTN7z0aj7lnc',
            # 'secret_key': '9x0h75LjgFw7QwAa7yYFOvDOpN4VKPx4i6iRiicTadZpTLMrTqW4uetm1GSg8srk',
        }

    strategy_list = [
        # {'instrument': 'EOSUSDT',
        #  'strategy_name': 'breakout',
        #  'cash': 50,
        #  'open_direction': 'LONG',
        #  'windows': 400,
        #  'open_volume': 30,
        #  'roll_mean_period': 200,
        #  'interval_period': 120,
        #  'stop_loss': 0,
        #  },

        {'instrument': 'LTCUSDT',
         'strategy_name': 'breakout',
         'cash': 50,
         'open_direction': 'LONG',
         'windows': 550,
         'open_volume': 30,
         'roll_mean_period': 630,
         'interval_period': 60,
         'order_step_muti': 10,
         'stop_loss': 0
         },

        {'instrument': 'RLCUSDT',
         'strategy_name': 'breakout',
         'cash': 50,
         'open_direction': 'LONG',
         'windows': 400,
         'open_volume': 30,
         'roll_mean_period': 120,
         'interval_period': 860,
         'order_step_muti': 20,
         'stop_loss': 0
         },

    ]


from logging.handlers import TimedRotatingFileHandler
logger = logging.getLogger('binance_api')
logger.setLevel(logging.WARNING)
log_fp = Configs.root_fp + 'song_binance_client/logs/binance_api.log'
handler = TimedRotatingFileHandler(log_fp, when="midnight", interval=1, backupCount=7)
handler.suffix = "%Y-%m-%d.log"  # 设置滚动后文件的后缀
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
