import pandas as pd

df_industry = pd.read_parquet(r".\OpenPermID-bulk-industry.ntriples\industry.parquet")

print("How many different types of entities are present in the graph?")
print("Different types of entities: ", df_industry['type'].nunique())
print()

print("How many industries are mentioned in the graph?")
print(df_industry['label'][df_industry['type'] == 'BusinessClassification'].nunique())
print()

print("How many business sectors are mentioned in the graph?")
print(df_industry['label'][df_industry['type'] == 'EconomicSector'].nunique())
print()

print("Under which broader does the most industries fall under?")
df_clean_broader = df_industry.drop_duplicates(subset=['label', 'broader_label'])
print(df_clean_broader.groupby('broader_label')['label'].count().sort_values(ascending=False))
