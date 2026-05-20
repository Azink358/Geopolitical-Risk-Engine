import os
import pandas as pd
from src.processing.builders.base_pipeline import BasePipeline

ROUTE_COORDS = {
    "Strait of Hormuz": {"origin_lat":25.2697,"origin_lon":55.3075,"dest_lat":25.2697,"dest_lon":56.8333},
    "Bab el-Mandeb / Red Sea": {"origin_lat":11.6,"origin_lon":43.1,"dest_lat":12.7,"dest_lon":45.0},
    "Suez Canal": {"origin_lat":31.265,"origin_lon":32.301,"dest_lat":29.966,"dest_lon":32.55},
    "Strait of Malacca": {"origin_lat":1.264,"origin_lon":103.822,"dest_lat":2.99,"dest_lon":101.36},
    "Cape of Good Hope (reroute)": {"origin_lat":-33.9,"origin_lon":18.4,"dest_lat":-29.9,"dest_lon":31.0},
    "Persian Gulf – East China Sea": {"origin_lat":25.2697,"origin_lon":55.3075,"dest_lat":31.23,"dest_lon":121.47},
    "Persian Gulf – Bay of Bengal": {"origin_lat":25.2697,"origin_lon":55.3075,"dest_lat":13.0827,"dest_lon":80.2707},
    "Persian Gulf – Sea of Japan": {"origin_lat":25.2697,"origin_lon":55.3075,"dest_lat":35.45,"dest_lon":139.64},
    "Aden Gulf – Indian Ocean": {"origin_lat":12.8,"origin_lon":45.0,"dest_lat":6.93,"dest_lon":79.85},
    "Arabian Sea – South China Sea": {"origin_lat":19.076,"origin_lon":72.877,"dest_lat":22.3,"dest_lon":114.2}
}


class DimensionBuilder(BasePipeline):
    """
    DimensionBuilder constructs conformed dimension tables.

    Responsibilities:
      - Deduplicate raw dimension values
      - Generate surrogate keys (integer IDs)
      - Standardize column names to schema.yaml
      - Save dimension tables for fact builders
    """

    def __init__(self, schema_path="schema.yaml"):
        super().__init__(schema_path)
        self.output_dir = self.schema["output"]["dimensions"]

    def build_dimension(self, df: pd.DataFrame, col: str, key_col: str, name: str) -> pd.DataFrame:
        """
        Generic dimension builder.
        - Deduplicates values
        - Assigns surrogate key
        - Saves to schema.yaml output path
        """
        if col not in df.columns:
            self.log(f"⚠️ Column {col} missing in dataset for {name}. Available: {list(df.columns)}")
            return pd.DataFrame(columns=[key_col, col])

        dim = df[[col]].drop_duplicates(keep="first").reset_index(drop=True)
        dim[key_col] = range(1, len(dim) + 1)

        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, f"{name}.csv")
        dim[[key_col, col]].to_csv(file_path, index=False)

        self.log(f"✅ Built {name} with {len(dim)} rows. Saved to {file_path}")
        return dim[[key_col, col]]

    def build_dim_date(self, df):
        """
        Dimension: Date | Surrogate Key: date_key
        - Uses YYYYMMDD as surrogate key
        - Adds year, month, week attributes
        """
        if "date" not in df.columns:
            self.log("⚠️ date column missing in dataset for dim_date.")
            return pd.DataFrame(columns=["date_key","date","year","month","week"])

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        dim = df[["date"]].drop_duplicates().reset_index(drop=True)
        dim["date_key"] = dim["date"].dt.strftime("%Y%m%d").astype(int)
        dim["year"] = dim["date"].dt.year
        dim["month"] = df["date"].dt.month
        dim["week"] = df["date"].dt.isocalendar().week

        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, "dim_date.csv")
        dim.to_csv(file_path, index=False)

        self.log(f"✅ Built dim_date with {len(dim)} rows. Saved to {file_path}")
        return dim

    # ---------------- DIMENSION BUILDERS ----------------
    def build_dim_country(self, df): return self.build_dimension(df, "country", "country_key", "dim_country")
    def build_dim_sector(self, df): return self.build_dimension(df, "sector", "sector_key", "dim_sector")

    def build_dim_route(self, df):
        dim = df[["route"]].drop_duplicates(keep="first").reset_index(drop=True)
        dim["route_key"] = range(1, len(dim) + 1)

        # Add coordinate columns
        dim["origin_lat"] = None
        dim["origin_lon"] = None
        dim["dest_lat"] = None
        dim["dest_lon"] = None

        for i, row in dim.iterrows():
            route_name = row["route"]
            if route_name in ROUTE_COORDS:
                coords = ROUTE_COORDS[route_name]
                dim.at[i, "origin_lat"] = coords["origin_lat"]
                dim.at[i, "origin_lon"] = coords["origin_lon"]
                dim.at[i, "dest_lat"] = coords["dest_lat"]
                dim.at[i, "dest_lon"] = coords["dest_lon"]

        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, "dim_route.csv")
        dim.to_csv(file_path, index=False)

        self.log(f"✅ Built dim_route with {len(dim)} rows. Saved to {file_path}")
        return dim

    def build_dim_vessel_type(self, shipping_df, disruptions_df):
        """
        Build vessel type dimension from both shipping (vessel_type)
        and disruptions (vessel_type_affected).
        """
        vessel_types = pd.concat([
            shipping_df[["vessel_type"]],
            disruptions_df[["vessel_type_affected"]].rename(columns={"vessel_type_affected": "vessel_type"})
        ], ignore_index=True)

        dim = vessel_types.drop_duplicates().reset_index(drop=True)
        dim["vessel_type_key"] = range(1, len(dim) + 1)

        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, "dim_vessel_type.csv")
        dim.to_csv(file_path, index=False)

        self.log(f"✅ Built dim_vessel_type with {len(dim)} rows. Saved to {file_path}")
        return dim

    def build_dim_flag_state(self, df):
        return self.build_dimension(df, "flag_state", "flag_state_key", "dim_flag_state")

    def build_dim_fuel_type(self, df): return self.build_dimension(df, "fuel_type", "fuel_type_key", "dim_fuel_type")
    def build_dim_incident_type(self, df): return self.build_dimension(df, "incident_type", "incident_type_key", "dim_incident_type")
    def build_dim_severity(self, df): return self.build_dimension(df, "severity", "severity_key", "dim_severity")
    def build_dim_response_category(self, df): return self.build_dimension(df, "response_category", "response_category_key", "dim_response_category")
    def build_dim_conflict_phase(self, df): return self.build_dimension(df, "conflict_phase", "conflict_phase_key", "dim_conflict_phase")

    def run_all(self, dfs: dict) -> dict:
        """
        Run all dimension builders sequentially.
        Expects dfs dict with cleaned dataframes keyed by file name.
        """
        dims = {}
        dims["country"] = self.build_dim_country(dfs["supply_chain"])
        dims["date"] = self.build_dim_date(dfs["price"])
        dims["sector"] = self.build_dim_sector(dfs["supply_chain"])
        dims["route"] = self.build_dim_route(dfs["shipping"])
        dims["vessel_type"] = self.build_dim_vessel_type(dfs["shipping"], dfs["disruptions"])
        dims["flag_state"] = self.build_dim_flag_state(dfs["disruptions"])
        dims["fuel_type"] = self.build_dim_fuel_type(dfs["imports"])
        dims["incident_type"] = self.build_dim_incident_type(dfs["disruptions"])
        dims["severity"] = self.build_dim_severity(dfs["disruptions"])
        dims["response_category"] = self.build_dim_response_category(dfs["response"])
        dims["conflict_phase"] = self.build_dim_conflict_phase(dfs["supply_chain"])
        self.log("✅ All dimension tables built and saved successfully.")
        return dims
