import os
import pandas as pd
from src.processing.builders.base_pipeline import BasePipeline

class FeatureBuilder(BasePipeline):
    """
    FeatureBuilder constructs the final feature table by aggregating fact tables.
    Outputs:
      - final_feature_table.csv (country/date/conflict_phase level)
      - shipping_features.csv (route/week/vessel level)
      - disruption_features.csv (route/date/vessel level)
      - response_features.csv (country/date/category level)
    """

    def __init__(self, schema_path="schema.yaml"):
        super().__init__(schema_path)
        self.output_dir = self.schema["output"]["features"]

    @staticmethod
    def enforce_keys(df, keys):
        """Force keys to nullable integer type."""
        for k in keys:
            if k in df.columns:
                df[k] = df[k].astype("Int64")
        return df

    def safe_groupby(self, df, keys, agg="sum"):
        """Group by only existing keys and aggregate numeric columns."""
        if df.empty:
            return pd.DataFrame()

        df = self.enforce_keys(df, keys)
        existing = [k for k in keys if k in df.columns]
        if not existing:
            self.log(f"⚠️ Skipped aggregation: none of {keys} found in DataFrame")
            return pd.DataFrame()

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        agg_cols = [c for c in numeric_cols if c not in existing]

        if not agg_cols:
            return df[existing].drop_duplicates()

        return df.groupby(existing)[agg_cols].agg(agg).reset_index()

    def build_feature_table(self, fact_supply_chain, fact_imports, fact_shipping,
                            fact_disruption, fact_response, fact_price):
        self.log("Building final_feature_table...")

        # === Aggregate each fact table to country/date/conflict_phase grain ===
        supply_chain_agg = self.safe_groupby(
            fact_supply_chain, ["country_key","date_key","conflict_phase_key"], agg="sum"
        ).drop(columns=[c for c in ["sector_key"] if c in fact_supply_chain.columns])

        imports_agg = self.safe_groupby(
            fact_imports, ["country_key","date_key","conflict_phase_key"], agg="sum"
        ).drop(columns=[c for c in ["fuel_type_key"] if c in fact_imports.columns])

        response_agg = self.safe_groupby(
            fact_response, ["country_key","date_key","conflict_phase_key"], agg="mean"
        ).drop(columns=[c for c in ["response_category_key"] if c in fact_response.columns])

        price_agg = self.safe_groupby(
            fact_price, ["date_key","conflict_phase_key"], agg="mean"
        )

        # === Drill-down features (keep sector/fuel/response_category granularity separately) ===
        if not fact_shipping.empty:
            shipping_agg = self.safe_groupby(
                fact_shipping, ["route_key","week","vessel_type_key","conflict_phase_key"], agg="mean"
            )
            shipping_agg.to_csv(os.path.join(self.output_dir, "shipping_features.csv"), index=False)
            self.log("✅ Shipping features saved")

        if not fact_disruption.empty:
            disruption_agg = self.safe_groupby(
                fact_disruption, ["route_key","date_key","vessel_type_key","conflict_phase_key"], agg="sum"
            )
            disruption_agg.to_csv(os.path.join(self.output_dir, "disruption_features.csv"), index=False)
            self.log("✅ Disruption features saved")

        if not fact_response.empty:
            response_detail = self.safe_groupby(
                fact_response, ["country_key","date_key","response_category_key","conflict_phase_key"], agg="mean"
            )
            response_detail.to_csv(os.path.join(self.output_dir, "response_features.csv"), index=False)
            self.log("✅ Response features saved")

        # === Merge into final feature table ===
        final_features = supply_chain_agg
        if not imports_agg.empty:
            final_features = final_features.merge(imports_agg, on=["country_key","date_key","conflict_phase_key"], how="outer")
        if not response_agg.empty:
            final_features = final_features.merge(response_agg, on=["country_key","date_key","conflict_phase_key"], how="outer")
        if not price_agg.empty:
            # Merge price only on date_key + conflict_phase_key (no country_key)
            final_features = final_features.merge(price_agg, on=["date_key","conflict_phase_key"], how="left")

        # === Save final feature table ===
        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, "final_feature_table.csv")
        final_features.to_csv(file_path, index=False)
        self.log(f"✅ Final feature table built with {len(final_features)} rows. Saved to {file_path}")

        return final_features
