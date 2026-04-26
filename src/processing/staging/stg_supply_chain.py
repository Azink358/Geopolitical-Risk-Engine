"""
Staging script for Supply Chain Impact dataset.

Transforms raw supply chain impact data into a fact table:
    fact_supply_chain_impact(date_key, country_key, sector_key, conflict_phase_key, measures...)

Steps:
    - Rename raw columns to schema-friendly snake_case names
    - Coerce numeric measures
    - Validate against schema.yaml
"""

import pandas as pd
import yaml
import logging
from pathlib import Path
from src.validation.validator import Validator


class SupplyChainImpactStager:
    def __init__(self,
                 raw_path="data/raw/supply_chain_impact_by_country.csv",
                 processed_path="data/processed/fact_supply_chain_impact.csv",
                 schema_path="schema.yaml"):
        self.raw_path = Path(raw_path)
        self.processed_path = Path(processed_path)
        self.schema_path = Path(schema_path)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

    def load_schema(self):
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def read_raw(self):
        self.logger.info("Reading raw supply chain impact data from %s", self.raw_path)
        return pd.read_csv(self.raw_path)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Transforming supply chain impact data")

        # Rename raw headers → schema-friendly compact names
        df.rename(columns={
            "Date": "date_key",
            "Country": "country_key",
            "Sector": "sector_key",
            "Conflict_Phase": "conflict_phase_key",
            "Supply_Chain_Disruption_Index": "disruption_index",
            "Estimated_GDP_Impact_MUSD": "gdp_impact_usd",
            "Avg_Delivery_Delay_Days": "delivery_delay_days",
            "Input_Cost_Increase_Pct": "input_cost_increase_pct",
            "Inventory_Stress_Score": "inventory_stress_score",
            "Supplier_Diversification_Score": "supplier_diversification_score"
        }, inplace=True)

        # Ensure numeric measures are properly typed
        numeric_cols = [
            "disruption_index",
            "gdp_impact_usd",
            "delivery_delay_days",
            "input_cost_increase_pct",
            "inventory_stress_score",
            "supplier_diversification_score"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Keep only fact grain + measures
        fact_cols = [
                        "date_key", "country_key", "sector_key", "conflict_phase_key"
                    ] + numeric_cols
        df_fact = df[fact_cols]

        self.logger.info("Transformation complete: %d rows, %d columns", df_fact.shape[0], df_fact.shape[1])
        return df_fact

    def validate(self, df_fact: pd.DataFrame) -> None:
        self.logger.info("Validating fact_supply_chain_impact against schema.yaml")
        schema = self.load_schema()
        validator = Validator(schema)
        validator.validate_fact("fact_supply_chain_impact", df_fact)
        self.logger.info("Validation passed")

    def save(self, df_fact: pd.DataFrame) -> None:
        df_fact.to_csv(self.processed_path, index=False)
        self.logger.info("✅ Processed fact_supply_chain_impact saved to %s", self.processed_path)

    def run(self) -> None:
        df = self.read_raw()
        df_fact = self.transform(df)
        self.validate(df_fact)
        self.save(df_fact)


if __name__ == "__main__":
    stager = SupplyChainImpactStager()
    stager.run()
