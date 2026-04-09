import pandas as pd

df_currency = pd.read_parquet(r".\OpenPermID-bulk-currency.ntriples\currency.parquet")
curr_country_df_updated = pd.read_parquet(r".\OpenPermID-bulk-currency.ntriples\country.parquet")

print("Currencies Analysis:")
print("How many types of currency nodes are represented in the graph?")
print(df_currency.groupby("type")['prefLabel'].count())

print()
print("What are the main edges between the currency entities?")
# Subunits of currencies
result_df_copy1 = df_currency.copy()
mapper = result_df_copy1.set_index('subject')['prefLabel']

result_df_copy1['subunitOF'] = result_df_copy1['isCurrencySubunitOf'].map(mapper)
subunit_mask = result_df_copy1['isCurrencySubunitOf'].notna()
print(result_df_copy1[['subject', 'prefLabel', 'subunitOF']][subunit_mask].head(10))

# Countries currencies used in
result_df_copy2 = df_currency.copy()
lookup_map = result_df_copy2.assign(subject=result_df_copy2['subject'].astype(str).str.strip()) \
                      .drop_duplicates('subject') \
                      .set_index('subject')['prefLabel']
curr_country_df_updated['currencyUsed'] = curr_country_df_updated['subject'].astype(str).str.strip().map(lookup_map)
print()
print(curr_country_df_updated.groupby(['currencyUsed', 'predicate'])['country'].count().sort_values(ascending=False).head(10))

print()
print("What are the  outliers for subunit factors? (Most currencies divide by 100.)")
subunitOutliers = result_df_copy1[(result_df_copy1['subunitFactor'] != 100) & (result_df_copy1['subunitFactor'].notna())]
print("Number of outlier subunits: ", subunitOutliers.shape[0])
print(subunitOutliers[['type', 'prefLabel', 'subunitFactor', 'subunitOF']].head(19))


print()
print("What is the ratio of active to dead currencies globally?")
print(df_currency['isISOHistorical'].value_counts())
print("Ratio: ", float(df_currency['isISOHistorical'].value_counts().iloc[0]) / df_currency['isISOHistorical'].value_counts().iloc[1])