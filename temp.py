import pandas as pd
df = pd.read_csv("excel/q6_by_station.csv")
print(df.shape)
print(df.columns.tolist())
print(df.iloc[:, 0].nunique())
print(df.groupby(df.columns[0]).size().value_counts())