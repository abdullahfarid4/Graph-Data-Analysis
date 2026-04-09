from rdflib import Graph
import pandas as pd
import requests
import polars as pl
import polars.selectors as cs

def simple_pandas_loader(path: str):
    # Create a Graph object
    g = Graph()

    # Parse the N-Triples file
    g.parse(fr"{path}", format="nt")

    # Convert triples to a list of tuples, then to a DataFrame
    df = pd.DataFrame(list(g), columns=["subject", "predicate", "object"])

    # Getting column names from Predicate URIs
    df['predicate'] = df['predicate'].str.extract(r'[/#]([^/#]+)$')

    # Pivot the graph
    df_clean = df.drop_duplicates(subset=['subject', 'predicate'], keep="last")
    df_pivoted = df_clean.pivot(index='subject', columns='predicate', values='object').reset_index()

    # Clean the shared "subject" column
    df_pivoted['subject'] = df_pivoted['subject'].str.extract(r'[/#]([^/#]+)$')

    return df_pivoted

def efficient_polars_loader(path: str, columnsToExplode: list[str]):
    # Define the Regex Pattern to handle ntriples
    pattern = r'^<(?P<s>[^>]+)>\s+<(?P<p>[^>]+)>\s+(?:"(?P<o_lit>(?:[^"\\]|\\.)*)"(?:\^\^<[^>]+>|@[a-zA-Z0-9\-]+)?|<(?P<o_uri>[^>]+)>)\s*\.\s*$'

    # Scan and Parse
    lazy_df = (
        pl.scan_csv(fr"{path}", has_header=False, separator="\n", new_columns=["raw_line"])
        .select(pl.col("raw_line").str.extract_groups(pattern))
        .unnest("raw_line")
        .with_columns(pl.coalesce(["o_lit", "o_uri"]).alias("o"))
        .drop(["o_lit", "o_uri"])
        # Clean the Predicate names 
        .with_columns(pl.col("p").str.replace_all(r'.*[/#]', ""))
    )

    # Remove duplicates
    lazy_df = lazy_df.unique(subset=["s", "p", "o"])

    # Handle Multi-valued Predicates. Group by subject and predicate to create lists first
    grouped_df = lazy_df.group_by(["s", "p"]).agg(pl.col("o")).collect()

    # Pivot the already-aggregated lists
    df_pol_pivoted = grouped_df.pivot(index="s", on="p", values="o")

    # Expand multivalue columns
    for col in columnsToExplode:
        df_pol_pivoted = df_pol_pivoted.explode(col)

    # Clean URIs
    clean_expression = r"^.*[/#]"
    df_final = df_pol_pivoted.with_columns([
        pl.col(col).str.replace(clean_expression, "") 
        for col in df_pol_pivoted.columns if col in cs.expand_selector(df_pol_pivoted, cs.string())
    ])

    df_final = df_final.with_columns(pl.col("hasName").list.join(separator=", "))

    return df_final



# 1) currency
print("Loading Currencies...")
df_currency = simple_pandas_loader(".\OpenPermID-bulk-currency.ntriples\OpenPermID-bulk-currency.ntriples")

# Drop country column (Used in currency/country names file)
df_currency = df_currency.drop(columns = ['isPrimaryCurrencyOf', 'isCurrencyOf']).reset_index()

# Currency/Country Names Dataframe
curr_country_df_updated = pd.read_csv(r".\OpenPermID-bulk-currency.ntriples\curr_country_with_names.csv")

# Clean
curr_country_df_updated.drop(columns=["Unnamed: 0"], inplace=True)

# Convert Datatype
df_currency['subunitFactor'] = pd.to_numeric(df_currency['subunitFactor'], errors='coerce').astype('Int64')

# Clean Columns
df_currency['isCurrencySubunitOf'] = df_currency['isCurrencySubunitOf'].str.extract(r'[/#]([^/#]+)$')
df_currency['type'] = df_currency['type'].str.extract(r'[/#]([^/#]+)$')

# Export to parquet
df_currency.to_parquet(r".\OpenPermID-bulk-currency.ntriples\currency.parquet", index=False)
curr_country_df_updated.to_parquet(r".\OpenPermID-bulk-currency.ntriples\country.parquet", index=False)


# 2) assetClass
print("Loading Assets...")
df_assets = simple_pandas_loader(".\OpenPermID-bulk-assetClass.ntriples\OpenPermID-bulk-assetClass.ntriples")
# Clean the columns
df_assets['broader'] = df_assets['broader'].str.extract(r'[/#]([^/#]+)$')
df_assets['type'] = df_assets['type'].str.extract(r'[/#]([^/#]+)$')

# Get broader label
asset_mapper = df_assets.set_index('subject')['label']
df_assets['broader_label'] = df_assets['broader'].map(asset_mapper)

# Export to parquet
df_assets.to_parquet(r".\OpenPermID-bulk-assetClass.ntriples\assets.parquet", index=False)


# 3) industry
print("Loading Industries...")
df_industry = simple_pandas_loader(".\OpenPermID-bulk-industry.ntriples\OpenPermID-bulk-industry.ntriples")
# Clean the columns
df_industry['broader'] = df_industry['broader'].str.extract(r'[/#]([^/#]+)$')
df_industry['type'] = df_industry['type'].str.extract(r'[/#]([^/#]+)$')

# Get broader label
industry_mapper = df_industry.set_index('subject')['label']
df_industry['broader_label'] = df_industry['broader'].map(industry_mapper)

# Export to parquet
df_industry.to_parquet(r".\OpenPermID-bulk-industry.ntriples\industry.parquet", index=False)



# 4) instruments
print("Loading Instruments...")
df_instruments = efficient_polars_loader(".\OpenPermID-bulk-instrument.ntriples\OpenPermID-bulk-instrument.ntriples", 
                                         ['hasAssetClass', 'isIssuedBy', 'hasPrimaryQuote', 'hasInstrumentStatus'])

# Export to parquet
df_instruments.write_parquet(r".\OpenPermID-bulk-instrument.ntriples\instruments.parquet")




# 5) quote
print("Loading Quotes...")
df_quote = efficient_polars_loader(".\OpenPermID-bulk-quote.ntriples\OpenPermID-bulk-quote.ntriples", 
                                         ['isQuotedIn', 'isQuoteOf', 'type'])

# Export to parquet
df_quote.write_parquet(r".\OpenPermID-bulk-quote.ntriples\quote.parquet")
print("Done")