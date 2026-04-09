import pandas as pd

df_assets = pd.read_parquet(r".\OpenPermID-bulk-assetClass.ntriples\assets.parquet")

print("Assets Analysis:")
print("How many asset classes are represented in the graph?")
print(df_assets['type'].count())
print()

print("What is the total count of assets by asset class?")
print(df_assets.groupby('broader_label')['label'].count().sort_values(ascending=False))
print()

print("What are some root asset classes?")
print(df_assets["label"][df_assets["broader_label"].isna()])
print()

print("What are some root asset classes?")
print(df_assets["label"][~df_assets["label"].isin(list(df_assets['broader_label']))])
print()

print("Which asset classes have the most complex definitions??")
longest_comments = df_assets['comment'].str.len().sort_values(ascending=False).head(10).index.to_list()
print(df_assets['label'].loc[longest_comments])
print()

print("Which asset classes have the least complex definitions??")
shortest_comments = df_assets['comment'].str.len().sort_values(ascending=False).tail(10).index.to_list()
print(df_assets['label'].loc[shortest_comments])
