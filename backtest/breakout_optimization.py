import sqlite3

import matplotlib.pyplot as plt
import pandas
import pandas as pd

pandas.set_option("expand_frame_repr", False)
pandas.set_option("display.max_rows", 2000)


def plt_account(n, stop_loss_rate, commision, trade_first, period, roll_mean_period, if_trend ,start_time):
    with sqlite3.connect('binance_quote_data.db') as conn:
        df = pd.read_sql(f'select * from future_{symbol} where start_time >= "{start_time}" order by start_time DESC',
                         conn)

    df = df.sort_values(by='start_time').reset_index(drop=True)
    start_time = df.loc[0].start_time
    end_time = df.loc[len(df) - 1].start_time
    df['close'] = df['close'].astype(float)

    position = None
    account_value = 1
    account_value_list = []
    long_rate = []
    short_rate = []

    time_list = df['start_time'].tolist()
    close_list = df['close'].tolist()
    df['roll_mean'] = df['close'].rolling(roll_mean_period).mean()
    close_roll_mean_list = df['roll_mean'].tolist()

    df_trade = pd.DataFrame(columns=['time', 'offset', 'dir', 'close', 'account_value'])

    for i, close in enumerate(close_list):

        if i < n:
            continue

        time = time_list[i]
        last_n = close_list[int(i - n): i]
        last_n_max = max(last_n)
        last_n_min = min(last_n)

        # if last_n_max / last_n_min - 1 < 0.001:
        #     continue

        if position:
            flag = None
            if position[0] == 'long':
                rate = close / position[1] - 1
                flag = 'long'
                if if_trend:
                    if close > close_roll_mean_list[i - period] > close_roll_mean_list[i - 2 * period]:
                        continue

            elif position[0] == 'short':
                rate = 1 - close / position[1]
                flag = 'short'

                if if_trend:
                    if close < close_roll_mean_list[i - period] < close_roll_mean_list[i - 2 * period]:
                        continue

            if rate < -stop_loss_rate:
                position = None
                account_value += rate - 0.0002

                df_trade.loc[len(df_trade)] = [time, 'stop_close', flag, close, account_value]
                account_value_list.append(account_value)
                continue

        if close < last_n_min:
            if not position:
                position = ('long', close)
                account_value += -commision
                account_value_list.append(account_value)
                df_trade.loc[len(df_trade)] = [time, 'open', 'long', close, account_value]
            else:
                if position[0] == 'short':
                    if trade_first:
                        account_value += 1 - (close + 0.001) / (position[1]) - commision
                    else:
                        account_value += 1 - close / position[1] - commision
                    df_trade.loc[len(df_trade)] = [time, 'close', 'short', close, account_value]

                    short_rate.append(1 - close / position[1])
                    account_value_list.append(account_value)
                    position = ('long', close)
                    df_trade.loc[len(df_trade)] = [time, 'open', 'long', close, account_value]

        elif close > last_n_max:
            if not position:
                position = ('short', close)
                account_value += -commision
                account_value_list.append(account_value)

                df_trade.loc[len(df_trade)] = [time, 'open', 'short', close, account_value]
            else:
                if position[0] == 'long':
                    if trade_first:
                        account_value += (close - 0.001) / (position[1]) - 1 - commision
                    else:
                        account_value += close / position[1] - 1 - commision
                    df_trade.loc[len(df_trade)] = [time, 'close', 'long', close, account_value]

                    long_rate.append(close / position[1] - 1)
                    account_value_list.append(account_value)

                    position = ('short', close)
                    df_trade.loc[len(df_trade)] = [time, 'open', 'short', close, account_value]

    plt.plot(account_value_list)

    title_name = (f'{start_time}-->{end_time}    {len(df)}min\n '
                  f'{symbol}  n={n}   trade times={len(account_value_list)} c={commision} sl={stop_loss_rate} '
                  f'p={period} rp={roll_mean_period}')
    plt.title(title_name)
    plt.show()

    # plt.savefig(f'result/{title_name}.jpg')
    # plt.clf()


if __name__ == '__main__':
    n = 400
    stop_loss_rate = 0.1
    commision = 0.0005
    trade_first = True
    period = 120
    roll_mean_period = 200
    if_trend = True
    if not if_trend:
        period = 0
        roll_mean_period = 0

    symbol = 'eosusdt'
    start_time = '2023-01-01 00:00:00'

    plt_account(n, stop_loss_rate, commision, trade_first, period, roll_mean_period, if_trend, start_time)

    # for period in [120]:
    #     for roll_mean_period in [210, 240, 270]:
    #         plt_account(n, stop_loss_rate, commision, trade_first, period, roll_mean_period, if_trend, start_time)

