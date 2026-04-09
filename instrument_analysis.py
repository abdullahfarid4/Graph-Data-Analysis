import polars as pl

df_instrument = pl.read_parquet(r".\OpenPermID-bulk-instrument.ntriples\instruments.parquet")
df_quote = pl.read_parquet(r".\OpenPermID-bulk-quote.ntriples\quote.parquet")
df_asset = pl.read_parquet(r".\OpenPermID-bulk-assetClass.ntriples\assets.parquet")

# Combine assets and instruments
lookup_pl_asset = df_asset.select(['subject', 'label'])
df_instrument = df_instrument.join(
    lookup_pl_asset, 
    left_on="hasAssetClass", 
    right_on="subject", 
    how="left"
).rename({"label": "assetClass_Name"})


lookup_pl_quoate = df_quote.select(['s', 'hasName'])
df_instrument = df_instrument.join(
    lookup_pl_quoate, 
    left_on="hasPrimaryQuote", 
    right_on="s", 
    how="left"
).rename({"hasName_right": "quoteName"})

print("What is ratio of active to inactive instrument status?")
df_inst_unq = df_instrument.unique(subset='s')
active = df_inst_unq.filter((pl.col('hasInstrumentStatus') == "instrumentStatusActive")).shape[0]
inactive = df_inst_unq.filter((pl.col('hasInstrumentStatus') == "instrumentStatusInActive")).shape[0]
print("Ratio: ", active / inactive)
print()

# Top 10 most common quote currencies
top_quotes = (
    df_instrument.filter(pl.col("quoteName").is_not_null())
    .group_by("quoteName")
    .len()
    .sort("len", descending=True)
    .head(10)
)
print(top_quotes)
print()

print("Base assets with the most quote pairings: ")
most_pairs = (
    df_instrument.filter(pl.col("assetClass_Name").is_not_null())
    .group_by("assetClass_Name")
    .len()
    .sort("len", descending=True)
    .head(10)
)
print(most_pairs)
print()
