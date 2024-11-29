import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('account_value.csv')


print(df)

plt.plot(df['balance'])
plt.show()
