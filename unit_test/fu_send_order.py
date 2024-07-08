#!/usr/bin/env python
import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError

config_logging(logging, logging.DEBUG)

key = "8kHJ8xMwb8wZkrTy17IVOym4CDo5qS6JFP8suvpsDaWCqjuBuIAn29HFYKuQM1bE"
secret = "uUH1X2sz5jnMVhL44zxHiphnxhoQ5swPs62gFg4JFLCRayWwFr2MZJm9dJlaM2WK"
# key = "lfFQPMO2aNVuq6RI8h4PzPObfLQjWsvPcJ8zpfbYb0TJZV3zFmuxTTN7z0aj7lnc"
# secret = "9x0h75LjgFw7QwAa7yYFOvDOpN4VKPx4i6iRiicTadZpTLMrTqW4uetm1GSg8srk"

um_futures_client = UMFutures(key=key, secret=secret)


response = um_futures_client.new_order(
    symbol="EOSUSDT",
    side="BUY",
    positionSide='LONG',
    type="LIMIT",
    quantity=20,
    timeInForce="GTC",
    price=0.77,
    newOrderRespType='RESULT',
)

# response = um_futures_client.account(recvWindow=5000)
print(response)


