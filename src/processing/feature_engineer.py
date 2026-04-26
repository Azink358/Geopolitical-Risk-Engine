"""
Feature Engineer module.

Adds derived features to processed fact tables for downstream analytics.
Examples:
    - Lagged values
    - Rolling averages
    - Normalized scores
    - Ratios and efficiency metrics
"""

import pandas as pd
import logging
from pathlib import Path


class FeatureEngineer:
    def __init__(self, processed_dir="data/processed", features_dir="data/features"):
        self.processed_dir = Path(processed_dir)
        self.features_dir = Path(features_dir)
        self.features_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging once
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger("feature_engineer")

    def add_energy_features(self):
        df = pd.read_csv(self.processed_dir / "fact_energy_volatility.csv")

        # 7-day rolling average of price_value
        df["price_value_7d_avg"] = df.groupby("commodity_key")["price_value"].transform(
            lambda x: x.rolling(7, min_periods=1).mean()
        )

        # Volatility proxy (rolling std)
        df["price_value_7d_std"] = df.groupby("commodity_key")["price_value"].transform(
            lambda x: x.rolling(7, min_periods=1).std()
        )

        out_path = self.features_dir / "feat_energy_volatility.csv"
        df.to_csv(out_path, index=False)
        self.logger.info("✅ Energy features engineered and saved to %s", out_path)

    def add_maritime_cost_features(self):
        df = pd.read_csv(self.processed_dir / "fact_maritime_costs.csv")

        # Normalize freight rate
        df["freight_rate_norm"] = (
            df["freight_rate_usd"] - df["freight_rate_usd"].mean()
        ) / df["freight_rate_usd"].std()

        # War risk premium relative to freight
        df["war_risk_vs_freight"] = df["war_risk_premium_pct"] * df["freight_rate_usd"]

        # Hull insurance relative to freight
        df["hull_insurance_vs_freight"] = df["hull_insurance_pct"] * df["freight_rate_usd"]

        # Bunker cost ratio vs freight
        df["bunker_vs_freight"] = df["bunker_cost_usd"] / df["freight_rate_usd"].replace(0, pd.NA)

        # Transit efficiency: freight per transit day
        df["freight_per_day"] = df["freight_rate_usd"] / df["transit_days"].replace(0, pd.NA)

        # Reroute penalty: freight per reroute day
        df["reroute_penalty"] = df["freight_rate_usd"] / (df["reroute_days"].replace(0, pd.NA) + 1)

        out_path = self.features_dir / "feat_maritime_costs.csv"
        df.to_csv(out_path, index=False)
        self.logger.info("✅ Maritime cost features engineered and saved to %s", out_path)

    def add_shipping_disruption_features(self):
        df = pd.read_csv(self.processed_dir / "fact_shipping_disruptions.csv")

        # Map severity_level (categorical) to numeric codes
        severity_map = {
            "Low": 1,
            "Moderate": 2,
            "High": 3,
            "Critical": 4
        }
        df["severity_numeric"] = df["severity_level"].map(severity_map)

        # Normalize severity score
        df["severity_norm"] = (
                                      df["severity_numeric"] - df["severity_numeric"].mean()
                              ) / df["severity_numeric"].std()

        # Delay per cargo volume
        df["delay_per_volume"] = df["delay_hours"] / df["cargo_volume"].replace(0, pd.NA)

        out_path = self.features_dir / "feat_shipping_disruptions.csv"
        df.to_csv(out_path, index=False)
        self.logger.info("✅ Shipping disruption features engineered and saved to %s", out_path)

    def add_strategic_response_features(self):
        df = pd.read_csv(self.processed_dir / "fact_strategic_responses.csv")

        # Effectiveness normalized
        df["effectiveness_norm"] = (
            df["effectiveness_score"] - df["effectiveness_score"].mean()
        ) / df["effectiveness_score"].std()

        # Cost efficiency ratio
        df["cost_efficiency"] = df["estimated_cost_usd"] / df["effectiveness_score"].replace(0, pd.NA)

        # Dependency reduction effectiveness
        df["dependency_reduction_efficiency"] = df["dependency_reduction_pct"] / df["estimated_cost_usd"].replace(0, pd.NA)

        out_path = self.features_dir / "feat_strategic_responses.csv"
        df.to_csv(out_path, index=False)
        self.logger.info("✅ Strategic response features engineered and saved to %s", out_path)

    def add_supply_chain_features(self):
        df = pd.read_csv(self.processed_dir / "fact_supply_chain_impact.csv")

        # Normalize disruption index
        df["disruption_index_norm"] = (
            df["disruption_index"] - df["disruption_index"].mean()
        ) / df["disruption_index"].std()

        # GDP impact per day of delay
        df["gdpimpact_per_delay"] = df["gdp_impact_usd"] / df["delivery_delay_days"].replace(0, pd.NA)

        # Ratio of input cost increase vs inventory stress
        df["cost_increase_vs_inventory"] = df["input_cost_increase_pct"] / df["inventory_stress_score"].replace(0, pd.NA)

        # Supplier diversification efficiency
        df["supplier_diversification_efficiency"] = df["supplier_diversification_score"] / df["disruption_index"].replace(0, pd.NA)

        out_path = self.features_dir / "feat_supply_chain_impact.csv"
        df.to_csv(out_path, index=False)
        self.logger.info("✅ Supply chain features engineered and saved to %s", out_path)

    def add_apac_dependency_features(self):
        df = pd.read_csv(self.processed_dir / "fact_apac_dependency.csv")

        # Risk-adjusted import volume
        df["risk_adjusted_import"] = df["import_volume"] * (df["disruption_risk_score"] / 100)

        # Price premium vs SPR cover
        df["premium_vs_spr"] = df["price_premium_pct"] / df["spr_days_cover"].replace(0, pd.NA)

        # Alternative source effectiveness
        df["alt_source_efficiency"] = df["alt_source_pct"] / df["disruption_risk_score"].replace(0, pd.NA)

        out_path = self.features_dir / "feat_apac_dependency.csv"
        df.to_csv(out_path, index=False)
        self.logger.info("✅ APAC dependency features engineered and saved to %s", out_path)

    def run_all(self):
        self.logger.info("⚙️ Running feature engineering for all fact tables...")
        self.add_energy_features()
        self.add_maritime_cost_features()
        self.add_shipping_disruption_features()
        self.add_strategic_response_features()
        self.add_supply_chain_features()
        self.add_apac_dependency_features()
        self.logger.info("✅ All feature engineering completed")
