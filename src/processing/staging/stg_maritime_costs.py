"""
Staging script for Maritime Costs dataset.

Transforms raw maritime cost data into a fact table:
    fact_maritime_costs(date_key, route_key, vessel_type_key, conflict_phase_key, measures...)

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


class MaritimeCostsStager:
    def __init__(self,
                 raw_path="data/raw/maritime_insurance_freight.csv",
                 processed_path="data/processed/fact_maritime_costs.csv",
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
        self.logger.info("Reading raw maritime costs data from %s", self.raw_path)
        return pd.read_csv(self.raw_path)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Transforming maritime insurance & freight data")

        # Rename raw headers → schema-friendly compact names
        df.rename(columns={
            "Week_Starting": "date_key",
            "Route": "route_key",
            "Vessel_Type": "vessel_type_key",
            "Conflict_Phase": "conflict_phase_key",
            "Freight_Rate_USD_Day": "freight_rate_usd",
            "War_Risk_Premium_Pct": "war_risk_premium_pct",
            "Hull_Insurance_Pct_Value": "hull_insurance_pct",
            "Bunker_Cost_USD_MT": "bunker_cost_usd",
            "Transit_Time_Days": "transit_days",
            "Rerouting_Extra_Days": "reroute_days"
        }, inplace=True)

        # Ensure numeric measures are properly typed
        numeric_cols = [
            "freight_rate_usd",
            "war_risk_premium_pct",
            "hull_insurance_pct",
            "bunker_cost_usd",
            "transit_days",
            "reroute_days"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Keep only fact grain + measures
        fact_cols = [
                        "date_key", "route_key", "vessel_type_key", "conflict_phase_key"
                    ] + numeric_cols
        df_fact = df[fact_cols]

        self.logger.info("Transformation complete: %d rows, %d columns", df_fact.shape[0], df_fact.shape[1])
        return df_fact

    def validate(self, df_fact: pd.DataFrame) -> None:
        self.logger.info("Validating fact_maritime_costs against schema.yaml")
        schema = self.load_schema()
        validator = Validator(schema)
        validator.validate_fact("fact_maritime_costs", df_fact)
        self.logger.info("Validation passed")

    def save(self, df_fact: pd.DataFrame) -> None:
        df_fact.to_csv(self.processed_path, index=False)
        self.logger.info("✅ Processed fact_maritime_costs saved to %s", self.processed_path)

    def run(self) -> None:
        df = self.read_raw()
        df_fact = self.transform(df)
        self.validate(df_fact)
        self.save(df_fact)


if __name__ == "__main__":
    stager = MaritimeCostsStager()
    stager.run()
