import os
import pandas as pd
from src.processing.builders.base_pipeline import BasePipeline
from src.validation.validator import Validator

class FactBuilder(BasePipeline):
    """
    FactBuilder constructs fact tables according to schema.yaml.

    Responsibilities:
      - Map raw columns to surrogate keys from dimensions
      - Enrich with date attributes (year, month, week)
      - Output only grain + metrics defined in schema.yaml
      - Validate grain uniqueness and nulls using Validator
      - Save fact tables to schema.yaml output path
    """

    def __init__(self, schema_path="schema.yaml"):
        super().__init__(schema_path)
        self.output_dir = self.schema["output"]["facts"]
        self.validator = Validator()

    def map_dimension(self, df, dim_df, dim_col, key_col):
        if dim_col not in df.columns or dim_col not in dim_df.columns:
            self.log(f"⚠️ Missing {dim_col}, inserting placeholder {key_col}. Available: {list(df.columns)}")
            df[key_col] = None
            return df
        df[dim_col] = df[dim_col].astype(str)
        dim_df[dim_col] = dim_df[dim_col].astype(str)
        df = df.merge(dim_df[[key_col, dim_col]], on=dim_col, how="left")
        return df.drop(columns=[dim_col])

    def map_date(self, df, dim_date, date_col="date"):
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            dim_date["date"] = pd.to_datetime(dim_date["date"], errors="coerce")
            df = df.merge(dim_date[["date_key","date","year","month","week"]],
                          left_on=date_col, right_on="date", how="left")
            return df.drop(columns=["date"])
        elif "date_key" in df.columns:
            return df.merge(dim_date[["date_key","year","month","week"]],
                            on="date_key", how="left")
        else:
            self.log("⚠️ No date column found, inserting placeholders.")
            df["date_key"] = None; df["year"] = None; df["month"] = None; df["week"] = None
            return df

    def finalize_fact(self, df, grain_cols, metrics, name):
        df = df.drop_duplicates(subset=grain_cols)
        try:
            self.validator.validate_fact(df, grain_cols, metrics)
        except ValueError as e:
            self.log(str(e))
        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, f"{name}.csv")
        df.to_csv(file_path, index=False)
        self.log(f"✅ Built {name} with {len(df)} rows. Saved to {file_path}")
        return df

    # ---------------- FACT BUILDERS ----------------

    def build_fact_supply_chain(self, df, dim_country, dim_date, dim_sector, dim_conflict_phase):
        self.log("Building fact_supply_chain...")
        df = self.map_dimension(df, dim_country, "country", "country_key")
        df = self.map_date(df, dim_date)
        df = self.map_dimension(df, dim_sector, "sector", "sector_key")
        df = self.map_dimension(df, dim_conflict_phase, "conflict_phase", "conflict_phase_key")
        metrics = [
            "supply_chain_disruption_index","estimated_gdp_impact_musd","avg_delivery_delay_days",
            "input_cost_increase_pct","inventory_stress_score","supplier_diversification_score"
        ]
        fact = df[["country_key","date_key","sector_key","conflict_phase_key"] + metrics]
        return self.finalize_fact(fact, ["country_key", "date_key", "sector_key", "conflict_phase_key"], metrics, "fact_supply_chain")

    def build_fact_imports(self, df, dim_country, dim_date, dim_fuel_type, dim_conflict_phase):
        self.log("Building fact_imports...")
        df = self.map_dimension(df, dim_country, "country", "country_key")
        df = self.map_date(df, dim_date)
        df = self.map_dimension(df, dim_fuel_type, "fuel_type", "fuel_type_key")
        df = self.map_dimension(df, dim_conflict_phase, "conflict_phase", "conflict_phase_key")
        metrics = ["import_volume_kbpd","me_share_pct","alternative_source_pct","price_premium_pct",
                   "disruption_risk_score","spr_days_cover"]
        fact = df[["country_key","date_key","fuel_type_key","conflict_phase_key"] + metrics]
        return self.finalize_fact(fact, ["country_key", "date_key", "fuel_type_key", "conflict_phase_key"], metrics, "fact_imports")

    def build_fact_shipping(self, df, dim_date, dim_route, dim_vessel_type, dim_conflict_phase):
        self.log("Building fact_shipping...")
        df = self.map_dimension(df, dim_route, "route", "route_key")

        # Handle vessel type column from shipping dataset
        if "vessel_type" in df.columns:
            df = self.map_dimension(df, dim_vessel_type, "vessel_type", "vessel_type_key")
        elif "vessel_type_affected" in df.columns:
            df = self.map_dimension(df, dim_vessel_type, "vessel_type_affected", "vessel_type_key")
        else:
            self.log("⚠️ No vessel_type column found in shipping dataset.")
            df["vessel_type_key"] = None

        df = self.map_dimension(df, dim_conflict_phase, "conflict_phase", "conflict_phase_key")

        if "week_starting" in df.columns:
            df["week_starting"] = pd.to_datetime(df["week_starting"], errors="coerce")
            dim_date["date"] = pd.to_datetime(dim_date["date"], errors="coerce")
            df = df.merge(dim_date[["date_key", "date", "week"]],
                          left_on="week_starting", right_on="date", how="left")
            df = df.drop(columns=["date"])
            grain = ["route_key", "week", "vessel_type_key", "conflict_phase_key"]
        else:
            grain = ["route_key", "vessel_type_key", "conflict_phase_key"]

        metrics = [
            "freight_rate_usd_day", "war_risk_premium_pct", "hull_insurance_pct_value",
            "bunker_cost_usd_mt", "transit_time_days", "rerouting_extra_days"
        ]
        fact = df[grain + metrics]
        return self.finalize_fact(fact, grain, metrics, "fact_shipping")

    def build_fact_disruption(self, df, dim_date, dim_route, dim_vessel_type,
                              dim_incident_type, dim_severity, dim_conflict_phase,dim_flag_state):
        self.log("Building fact_disruption...")
        df = self.map_date(df, dim_date)
        df = self.map_dimension(df, dim_route, "route", "route_key")

        # Normalize vessel_type_affected → vessel_type for mapping
        if "vessel_type_affected" in df.columns:
            df = df.rename(columns={"vessel_type_affected": "vessel_type"})
        # Now map consistently
        df = self.map_dimension(df, dim_vessel_type, "vessel_type", "vessel_type_key")
        df = self.map_dimension(df, dim_flag_state, "flag_state", "flag_state_key")

        df = self.map_dimension(df, dim_incident_type, "incident_type", "incident_type_key")
        df = self.map_dimension(df, dim_severity, "severity", "severity_key")
        df = self.map_dimension(df, dim_conflict_phase, "conflict_phase", "conflict_phase_key")

        metrics = ["estimated_delay_hours", "cargo_volume_impacted_kt", "lat", "lon","reroute_required"]

        fact = df[["event_id", "date_key", "conflict_phase_key", "incident_type_key", "vessel_type_key","flag_state_key"] + metrics]

        return self.finalize_fact(
            fact,
            ["event_id", "date_key", "conflict_phase_key", "incident_type_key", "vessel_type_key","flag_state_key"],
            metrics,
            "fact_disruption"
        )

    def build_fact_response(self, df, dim_country, dim_date, dim_response_category, dim_conflict_phase):
        self.log("Building fact_response...")
        df = self.map_dimension(df, dim_country, "country", "country_key")
        df = self.map_date(df, dim_date)
        df = self.map_dimension(df, dim_response_category, "response_category", "response_category_key")
        df = self.map_dimension(df, dim_conflict_phase, "conflict_phase", "conflict_phase_key")
        metrics = ["estimated_cost_musd","effectiveness_score","me_dependency_reduction_pct"]
        fact = df[["response_id","country_key","date_key","conflict_phase_key","response_category_key"] + metrics]
        return self.finalize_fact(fact, ["response_id", "country_key", "date_key", "conflict_phase_key", "response_category_key"], metrics, "fact_response")

    def build_fact_price(self, df, dim_date, dim_conflict_phase):
        self.log("Building fact_price...")
        # Map date and conflict phase dimensions
        df = self.map_date(df, dim_date)
        df = self.map_dimension(df, dim_conflict_phase, "conflict_phase", "conflict_phase_key")

        # Define metrics
        metrics = [
            "brent_crude_usd_bbl",
            "wti_crude_usd_bbl",
            "dubai_oman_crude_usd_bbl",
            "henry_hub_ng_usd_mmbtu",
            "jkm_lng_usd_mmbtu",
            "singapore_gasoil_usd_bbl",
            "jet_fuel_usd_bbl",
            "coal_newcastle_usd_ton",
            "brent_wti_spread",
            "asian_premium_pct",
            "volatility_index"
        ]

        # Build fact table
        fact = df[["date_key", "conflict_phase_key"] + metrics]

        # Finalize and save
        return self.finalize_fact(
            fact,
            ["date_key", "conflict_phase_key"],
            metrics,
            "fact_price"
        )

    def run_all(self, dfs: dict, dims: dict) -> dict:
        """
        Run all fact builders sequentially.
        Expects dfs dict with raw dataframes keyed by file name (supply_chain, imports, etc.)
        and dims dict with dimension DataFrames keyed by logical dimension name.
        """
        facts = {}
        facts["supply_chain"] = self.build_fact_supply_chain(
            dfs["supply_chain"], dims["country"], dims["date"], dims["sector"], dims["conflict_phase"]
        )
        facts["imports"] = self.build_fact_imports(
            dfs["imports"], dims["country"], dims["date"], dims["fuel_type"], dims["conflict_phase"]
        )
        facts["shipping"] = self.build_fact_shipping(
            dfs["shipping"], dims["date"], dims["route"], dims["vessel_type"], dims["conflict_phase"]
        )
        facts["disruption"] = self.build_fact_disruption(
            dfs["disruptions"], dims["date"], dims["route"], dims["vessel_type"],
            dims["incident_type"], dims["severity"], dims["conflict_phase"],dims["flag_state"]
        )
        facts["response"] = self.build_fact_response(
            dfs["response"], dims["country"], dims["date"], dims["response_category"], dims["conflict_phase"]
        )
        facts["price"] = self.build_fact_price(
            dfs["price"], dims["date"], dims["conflict_phase"]
        )
        self.log("✅ All fact tables built and saved successfully.")
        return facts


