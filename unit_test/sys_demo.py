from a_songbo.binance_client.utils.sys_exception import common_exception


@common_exception(log_flag=True)
def divs():
    return 1 / 0



