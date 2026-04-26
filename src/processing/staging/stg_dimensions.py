import os
import pandas as pd

REFERENCE_DIR = "data/reference"
PROCESSED_DIR = "data/processed"

def normalize_keys(df):
    """Ensure we always have a DataFrame with *_key columns as strings."""
    if df is None:
        return pd.DataFrame()
    if isinstance(df, pd.io.parsers.TextFileReader):
        df = pd.concat(df, ignore_index=True)
    for col in df.columns:
        if col.endswith("_key"):
            df[col] = df[col].astype(str)
    return df

def ensure_reference_csvs():
    os.makedirs(REFERENCE_DIR, exist_ok=True)
    # keep your reference creation logic here

# ------------------------
# Dimension Builders
# ------------------------

def build_dim_country(df, fact_supply_chain_impact):
    df = normalize_keys(df)
    fact_supply_chain_impact = normalize_keys(fact_supply_chain_impact)

    ref_path = os.path.join(REFERENCE_DIR, "countries.csv")
    ref = pd.read_csv(ref_path)
    ref = normalize_keys(ref)

    dim = df[["country_key"]].drop_duplicates().reset_index(drop=True)
    dim = dim.merge(ref, on="country_key", how="left")
    dim = dim.merge(fact_supply_chain_impact[["country_key"]].drop_duplicates(), on="country_key", how="left")

    ref_updated = dim[["country_key","country_name","region"]].drop_duplicates()
    ref_updated.to_csv(ref_path, index=False)
    return dim

def build_dim_sector(df, fact_supply_chain_impact):
    df = normalize_keys(df)
    fact_supply_chain_impact = normalize_keys(fact_supply_chain_impact)

    ref_path = os.path.join(REFERENCE_DIR, "sectors.csv")
    ref = pd.read_csv(ref_path)
    ref = normalize_keys(ref)

    dim = df[["sector_key"]].drop_duplicates().reset_index(drop=True)
    dim = dim.merge(ref, on="sector_key", how="left")
    dim = dim.merge(fact_supply_chain_impact[["sector_key"]].drop_duplicates(), on="sector_key", how="left")

    ref_updated = dim[["sector_key","sector_name"]].drop_duplicates()
    ref_updated.to_csv(ref_path, index=False)
    return dim

def build_dim_fuel_type(df, fact_apac_dependency):
    df = normalize_keys(df)
    fact_apac_dependency = normalize_keys(fact_apac_dependency)

    ref_path = os.path.join(REFERENCE_DIR, "fuel_types.csv")
    ref = pd.read_csv(ref_path)
    ref = normalize_keys(ref)

    dim = df[["fuel_type_key"]].drop_duplicates().reset_index(drop=True)
    dim = dim.merge(ref, on="fuel_type_key", how="left")
    dim = dim.merge(fact_apac_dependency[["fuel_type_key"]].drop_duplicates(), on="fuel_type_key", how="left")

    ref_updated = dim[["fuel_type_key","fuel_type_name"]].drop_duplicates()
    ref_updated.to_csv(ref_path, index=False)
    return dim

def build_dim_conflict_phase(df, fact_energy_volatility):
    df = normalize_keys(df)
    fact_energy_volatility = normalize_keys(fact_energy_volatility)

    ref_path = os.path.join(REFERENCE_DIR, "conflict_phases.csv")
    ref = pd.read_csv(ref_path)
    ref = normalize_keys(ref)

    dim = df[["conflict_phase_key"]].drop_duplicates().reset_index(drop=True)
    dim = dim.merge(ref, on="conflict_phase_key", how="left")
    dim = dim.merge(fact_energy_volatility[["conflict_phase_key"]].drop_duplicates(), on="conflict_phase_key", how="left")

    ref_updated = dim[["conflict_phase_key","phase_name","description"]].drop_duplicates()
    ref_updated.to_csv(ref_path, index=False)
    return dim

def build_dim_response(df, fact_strategic_responses):
    df = normalize_keys(df)
    fact_strategic_responses = normalize_keys(fact_strategic_responses)

    ref_path = os.path.join(REFERENCE_DIR, "responses.csv")
    ref = pd.read_csv(ref_path)
    ref = normalize_keys(ref)

    dim = df[["response_key"]].drop_duplicates().reset_index(drop=True)
    dim = dim.merge(ref, on="response_key", how="left")
    dim = dim.merge(fact_strategic_responses[["response_key","response_category","institution"]].drop_duplicates(),
                    on="response_key", how="left", suffixes=("", "_fact"))

    for col in ["response_category","institution"]:
        dim[col] = dim[col].fillna(dim[f"{col}_fact"])
        dim.drop(columns=[f"{col}_fact"], inplace=True)

    ref_updated = dim[["response_key","response_category","institution"]].drop_duplicates()
    ref_updated.to_csv(ref_path, index=False)
    return dim

def build_dim_event(df, fact_shipping_disruptions):
    df = normalize_keys(df)
    fact_shipping_disruptions = normalize_keys(fact_shipping_disruptions)

    ref_path = os.path.join(REFERENCE_DIR, "events.csv")
    ref = pd.read_csv(ref_path)
    ref = normalize_keys(ref)

    dim = df[["event_key"]].drop_duplicates().reset_index(drop=True)
    dim = dim.merge(ref, on="event_key", how="left")
    dim = dim.merge(fact_shipping_disruptions[["event_key","incident_type","severity_level","route_key"]].drop_duplicates(),
                    on="event_key", how="left", suffixes=("", "_fact"))

    for col in ["incident_type","severity_level","route_key"]:
        dim[col] = dim[col].fillna(dim[f"{col}_fact"])
        dim.drop(columns=[f"{col}_fact"], inplace=True)

    ref_updated = dim[["event_key","incident_type","severity_level","route_key"]].drop_duplicates()
    ref_updated.to_csv(ref_path, index=False)
    return dim

# ------------------------
# Dimension Stager
# ------------------------

class DimensionStager:
    def __init__(self, dim_name, df_source, facts):
        self.dim_name = dim_name
        self.df_source = df_source
        self.facts = facts

    def transform(self):
        if self.dim_name == "dim_country":
            return build_dim_country(self.df_source, self.facts["fact_supply_chain_impact"])
        if self.dim_name == "dim_sector":
            return build_dim_sector(self.df_source, self.facts["fact_supply_chain_impact"])
        if self.dim_name == "dim_fuel_type":
            return build_dim_fuel_type(self.df_source, self.facts["fact_apac_dependency"])
        if self.dim_name == "dim_conflict_phase":
            return build_dim_conflict_phase(self.df_source, self.facts["fact_energy_volatility"])
        if self.dim_name == "dim_response":
            return build_dim_response(self.df_source, self.facts["fact_strategic_responses"])
        if self.dim_name == "dim_event":
            return build_dim_event(self.df_source, self.facts["fact_shipping_disruptions"])
        raise ValueError(f"No builder defined for {self.dim_name}")

    def run(self):
        df_dim = self.transform()
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        output_path = os.path.join(PROCESSED_DIR, f"{self.dim_name}.csv")
        df_dim.to_csv(output_path, index=False)
        print(f"[{self.dim_name}] staged with {len(df_dim)} rows → saved to {output_path}")
        return df_dim

# ------------------------
# Run All
# ------------------------

def run_all(dim_sources: dict, facts: dict) -> dict:
    ensure_reference_csvs()
    staged_dims = {}
    for dim_name, df_source in dim_sources.items():
        stager = DimensionStager(dim_name, df_source, facts)
        staged_dims[dim_name] = stager.run()
    return staged_dims
