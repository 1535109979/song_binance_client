import sqlite3

import matplotlib.pyplot as plt
import pandas
import pandas as pd

pandas.set_option("expand_frame_repr", False)

# 当前价格 低于 前n小时最小值，做多
# 当前价格 高于 前n小时最大值，做空
n = 10
stop_loss_rate = 0.01
commision = 0.00035
symbol = 'eosusdt'
direction = 'LONG'
direction_rever = 'SHORT'
start_time = '2024-05-20 00:00:00'

with sqlite3.connect('binance_quote_data.db') as conn:
    df = pd.read_sql(f'select * from future_{symbol} where start_time >= "{start_time}" order by start_time DESC', conn)

df = df.sort_values(by='start_time').reset_index(drop=True)
start_time = df.loc[0].start_time
end_time = df.loc[len(df)-1].start_time

df['close'] = df['close'].astype(float)

position = None
account_value = 1
account_value_list = []
long_rate = []
short_rate = []

close_list = df['close'].tolist()
for i, close in enumerate(close_list):

    if i < n:
        continue

    last_n = close_list[int(i - n): i]
    last_n_max = max(last_n)
    last_n_min = min(last_n)

    if position:
        if position[0] == 'long':
            rate = close / position[1] - 1
        elif position[0] == 'short':
            rate = 1 - close / position[1]

        if rate < -stop_loss_rate:
            position = None
            account_value += rate - 0.0002
            account_value_list.append(account_value)
            continue

        # if i - position[2] > 20:
        #     position = None
        #     account_value += rate - 0.0002
        #     account_value_list.append(account_value)
        #     continue

    # if last_n[-1] < last_n[-2] < last_n[-3]:
    #     if not position:
    #         position = ('short', close, i)
    #         continue
    #     if position[0] == 'long':
    #         account_value += close / position[1] - 1 - commision
    #         long_rate.append(close / position[1] - 1)
    #         account_value_list.append(account_value)
    #         position = ('short', close, i)
    #         continue
    #
    # if last_n[-1] > last_n[-2] > last_n[-3]:
    #     if not position:
    #         position = ('long', close, i)
    #         continue
    #     if position[0] == 'short':
    #         account_value += 1 - close / position[1] - commision
    #         short_rate.append(1 - close / position[1])
    #         account_value_list.append(account_value)
    #         position = ('long', close, i)

    if close < last_n_min:
        if not position:
            position = ('long', close, i)
            account_value -= commision
        else:
            if position[0] == 'short':
                account_value += 1 - close / position[1] - commision
                short_rate.append(1 - close / position[1])
                account_value_list.append(account_value)
                position = ('long', close, i)

    elif close > last_n_max:
        if not position:
            position = ('short', close, i)
            account_value -= commision
        else:
            if position[0] == 'long':
                account_value += close / position[1] - 1 - commision
                long_rate.append(close / position[1] - 1)
                account_value_list.append(account_value)
                position = ('short', close, i)

# plt.scatter(range(len(short_rate)), short_rate)
# plt.show()
#
# plt.subplot(2,1,1)
# plt.plot(df['close'])
# plt.subplot(2,1,2)
plt.plot(account_value_list)

plt.title(f'{start_time}-->{end_time}    {len(df)}min\n '
          f'{symbol}    n={n}   trade times={len(account_value_list)} commision={commision}')
plt.show()

