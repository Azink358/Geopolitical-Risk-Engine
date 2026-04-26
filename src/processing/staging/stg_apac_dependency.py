"""
Staging script for APAC Fuel Import Dependency dataset.

Transforms raw import dependency data into a fact table:
    fact_apac_fuel_dependency(date_key, country_key, fuel_type_key, conflict_phase_key, measures...)

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


class APACDependencyStager:
    def __init__(self,
                 raw_path="data/raw/apac_fuel_import_dependency.csv",
                 processed_path="data/processed/fact_apac_dependency.csv",
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
        self.logger.info("Reading raw APAC fuel import dependency data from %s", self.raw_path)
        return pd.read_csv(self.raw_path)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Transforming APAC fuel import dependency data")

        # Rename raw headers → schema-friendly compact names
        df.rename(columns={
            "Date": "date_key",
            "Country": "country_key",
            "Fuel_Type": "fuel_type_key",
            "Conflict_Phase": "conflict_phase_key",
            "Import_Volume_KBPD": "import_volume",
            "ME_Share_Pct": "me_share_pct",
            "Alternative_Source_Pct": "alt_source_pct",
            "Price_Premium_Pct": "price_premium_pct",
            "Disruption_Risk_Score": "disruption_risk_score",
            "SPR_Days_Cover": "spr_days_cover"
        }, inplace=True)

        # Ensure numeric measures are properly typed
        numeric_cols = [
            "import_volume",
            "me_share_pct",
            "alt_source_pct",
            "price_premium_pct",
            "disruption_risk_score",
            "spr_days_cover"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Keep only fact grain + measures
        fact_cols = [
                        "date_key", "country_key", "fuel_type_key", "conflict_phase_key"
                    ] + numeric_cols
        df_fact = df[fact_cols]

        self.logger.info("Transformation complete: %d rows, %d columns", df_fact.shape[0], df_fact.shape[1])
        return df_fact

    def validate(self, df_fact: pd.DataFrame) -> None:
        self.logger.info("Validating fact_apac_fuel_dependency against schema.yaml")
        schema = self.load_schema()
        validator = Validator(schema)
        validator.validate_fact("fact_apac_dependency", df_fact)
        self.logger.info("Validation passed")

    def save(self, df_fact: pd.DataFrame) -> None:
        df_fact.to_csv(self.processed_path, index=False)
        self.logger.info("✅ Processed fact_apac_fuel_dependency saved to %s", self.processed_path)

    def run(self) -> None:
        df = self.read_raw()
        df_fact = self.transform(df)
        self.validate(df_fact)
        self.save(df_fact)


if __name__ == "__main__":
    stager = APACDependencyStager()
    stager.run()
