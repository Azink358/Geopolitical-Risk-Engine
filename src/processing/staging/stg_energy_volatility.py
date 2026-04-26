"""
Staging script for Energy Price Volatility dataset.

Transforms raw benchmark price data into a normalized fact table:
    fact_energy_volatility(date_key, conflict_phase_key, commodity_key, price_value)

Steps:
    - Melt wide benchmark columns into (commodity_key, price_value)
    - Coerce numeric measures
    - Validate against schema.yaml
"""

import pandas as pd
import yaml
import logging
from pathlib import Path
from src.validation.validator import Validator


class EnergyVolatilityStager:
    def __init__(self,
                 raw_path="data/raw/energy_price_volatility.csv",
                 processed_path="data/processed/fact_energy_volatility.csv",
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
        self.logger.info("Reading raw energy price volatility data from %s", self.raw_path)
        return pd.read_csv(self.raw_path)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Transforming energy price volatility data")

        # Melt benchmark columns into commodity_key + price_value
        id_vars = ["Date", "Conflict_Phase"]
        value_vars = [c for c in df.columns if c not in id_vars]

        df_long = df.melt(
            id_vars=id_vars,
            value_vars=value_vars,
            var_name="commodity_key",
            value_name="price_value"
        )

        # Rename to schema-friendly compact names
        df_long.rename(columns={
            "Date": "date_key",
            "Conflict_Phase": "conflict_phase_key"
        }, inplace=True)

        # Ensure numeric measure is properly typed
        df_long["price_value"] = pd.to_numeric(df_long["price_value"], errors="coerce")

        # Keep only fact grain + measures
        fact_cols = ["date_key", "conflict_phase_key", "commodity_key", "price_value"]
        df_fact = df_long[fact_cols]

        self.logger.info("Transformation complete: %d rows, %d columns", df_fact.shape[0], df_fact.shape[1])
        return df_fact

    def validate(self, df_fact: pd.DataFrame) -> None:
        self.logger.info("Validating fact_energy_volatility against schema.yaml")
        schema = self.load_schema()
        validator = Validator(schema)
        validator.validate_fact("fact_energy_volatility", df_fact)
        self.logger.info("Validation passed")

    def save(self, df_fact: pd.DataFrame) -> None:
        df_fact.to_csv(self.processed_path, index=False)
        self.logger.info("✅ Processed fact_energy_volatility saved to %s", self.processed_path)

    def run(self) -> None:
        df = self.read_raw()
        df_fact = self.transform(df)
        self.validate(df_fact)
        self.save(df_fact)


if __name__ == "__main__":
    stager = EnergyVolatilityStager()
    stager.run()
