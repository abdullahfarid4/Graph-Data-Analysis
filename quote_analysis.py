import polars as pl

df_quote = pl.read_parquet(r".\OpenPermID-bulk-quote.ntriples\quote.parquet")
df_currency = pl.read_parquet(r".\OpenPermID-bulk-currency.ntriples\currency.parquet")

# Get isQuoteIn label
lookup_pl = df_currency.select(['subject', 'prefLabel'])

# Perform a left join (to get currency)
df_quote = df_quote.join(
    lookup_pl, 
    left_on="isQuotedIn", 
    right_on="subject", 
    how="left"
).rename({"prefLabel": "isQuotedIn_currency"})


# Distribution of quotes by currency
print("What are the most common currencies these instruments are quoted in?")
print(df_quote['isQuotedIn_currency'].value_counts(sort=True).head(10))

# Number of unique markets
df_unq_s = df_quote.unique(subset=['s'])
print("How many distinct global markets (MICs) does this data cover?")
print(df_unq_s.select(pl.col('hasMic').n_unique()).item())
print()

# Top exchanges by number of quotes
print("Which trading venues (exchanges) host the highest volume of quotes?")
print(df_unq_s['hasExchangeCode'].value_counts().sort('count', descending=True).head(10))
print()

# Percentage of instruments that have a RIC
ric_coverage = df_unq_s.select((pl.col("hasRic").is_not_null().mean() * 100).alias("ric_pct")).item()

# Percentage of instruments that have an Exchange Ticker
ticker_coverage = df_unq_s.select((pl.col("hasExchangeTicker").is_not_null().mean() * 100).alias("ticker_pct")).item()

print(f"RIC Coverage: {ric_coverage:.2f}%")
print(f"Ticker Coverage: {ticker_coverage:.2f}%")
print()


print("Quotes with multiple exchange codes, ric, mic, and tickers:")
list_cols = ['hasRic', 'hasExchangeCode', 'hasExchangeTicker', 'hasMic']
count_cols = [f"{col}_count" for col in list_cols]

df_quote_multi = df_unq_s.with_columns([
    pl.col(col).list.len().fill_null(0).alias(f"{col}_count") 
    for col in list_cols
])

# df_quote_multi = df_quote_multi.sort(count_cols, descending=[True] * len(count_cols))

# total number of identifiers across all 4 columns
df_quote_multi = df_quote_multi.with_columns(
    total_complexity = pl.sum_horizontal(count_cols)).sort("total_complexity", descending=True)

df_multi = df_quote_multi.select([
    "hasName",
    "total_complexity",
    *count_cols
])

print(df_multi.head(10))