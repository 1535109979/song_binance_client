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
            # 'api_key': '8kHJ8xMwb8wZkrTy17IVOym4CDo5qS6JFP8suvpsDaWCqjuBuIAn29HFYKuQM1bE',
            # 'secret_key': 'uUH1X2sz5jnMVhL44zxHiphnxhoQ5swPs62gFg4JFLCRayWwFr2MZJm9dJlaM2WK',
            'api_key': 'tw8xvSqYAXfqqTHWBKKuvETUcJ6w9BttMG6QIb7q7CceVrl74RdeChxeg05zfDg2',
            'secret_key': '81b9bXaVU7t0QhRQrFB5NfulRYYO7IFiR2D3rLOdrSlbGA2NYwxBvIy09JQPC1dL',
        }

    strategy_list = [

        # {'instrument': 'LTCUSDT', 'cash': 200,
        #  'windows': 550, 'roll_mean_period': 630, 'interval_period': 60,
        #  'strategy_name': 'breakout', 'open_direction': 'LONG',
        #  'open_volume': 30, 'order_step_muti': 10, 'stop_loss': 0},

        # {'instrument': 'EOSUSDT', 'cash': 200,
        #  'windows': 390, 'roll_mean_period': 100, 'interval_period': 100,
        #  'strategy_name': 'breakout', 'open_direction': 'LONG',
        #  'open_volume': 30, 'order_step_muti': 20, 'stop_loss': 0},

        { 'instrument': 'RLCUSDT', 'cash': 200,
         'windows': 400, 'roll_mean_period': 120, 'interval_period': 860,
         'strategy_name': 'breakout', 'open_direction': 'LONG',
         'open_volume': 30, 'order_step_muti': 20, 'stop_loss': 0 },

        {'instrument': 'ONDOUSDT', 'cash': 200,
         'windows': 430, 'roll_mean_period': 200, 'interval_period': 710,
         'strategy_name': 'breakout', 'open_direction': 'LONG',
         'open_volume': 30, 'order_step_muti': 10, 'stop_loss': 0},

        # {'instrument': 'PORTALUSDT', 'cash': 200,
        #  'windows': 600, 'roll_mean_period': 500, 'interval_period': 600,
        #  'strategy_name': 'breakout', 'open_direction': 'LONG',
        #  'open_volume': 30, 'order_step_muti': 10, 'stop_loss': 0},

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
