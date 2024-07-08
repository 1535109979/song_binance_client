import sqlite3

import pandas as pd


# sta_time = '2024-05-23 00:00:00'
#
# with sqlite3.connect('bian_f_data.db') as conn:
#     df = pd.read_sql(f'select * from rtn_trade where update_time > "{sta_time}"', conn)
#     print(df)
#
# df.to_csv('trade.csv')

with sqlite3.connect('bian_f_data.db') as conn:
    df = pd.read_sql('select * from account_value', conn)
    print(df)

