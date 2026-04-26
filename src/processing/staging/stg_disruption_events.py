"""
Staging script for Disruption Events dataset.

Transforms raw disruption event data into a fact table:
    fact_disruption_events(event_key, date_key, route_key, conflict_phase_key, incident_type, severity_level,
                           vessel_type_key, flag_state, reroute_required, measures...)

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


class DisruptionEventsStager:
    def __init__(self,
                 raw_path="data/raw/shipping_route_disruptions.csv",
                 processed_path="data/processed/fact_shipping_disruptions.csv",
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
        self.logger.info("Reading raw disruption events data from %s", self.raw_path)
        return pd.read_csv(self.raw_path)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Transforming shipping route disruptions data")

        # Rename raw headers → schema-friendly compact names
        df.rename(columns={
            "Event_ID": "event_key",
            "Date": "date_key",
            "Route": "route_key",
            "Conflict_Phase": "conflict_phase_key",
            "Incident_Type": "incident_type",
            "Severity": "severity_level",
            "Vessel_Type_Affected": "vessel_type_key",
            "Flag_State": "flag_state",
            "Estimated_Delay_Hours": "delay_hours",
            "Cargo_Volume_Impacted_KT": "cargo_volume",
            "Lat": "latitude",
            "Lon": "longitude",
            "Reroute_Required": "reroute_required"
        }, inplace=True)

        # Ensure numeric measures are properly typed
        numeric_cols = [
            "delay_hours",
            "cargo_volume",
            "latitude",
            "longitude"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Keep only fact grain + measures
        fact_cols = [
            "event_key", "date_key", "route_key", "conflict_phase_key",
            "incident_type", "severity_level", "vessel_type_key", "flag_state",
            "reroute_required", "delay_hours", "cargo_volume", "latitude", "longitude"
        ]
        df_fact = df[fact_cols]

        self.logger.info("Transformation complete: %d rows, %d columns", df_fact.shape[0], df_fact.shape[1])
        return df_fact

    def validate(self, df_fact: pd.DataFrame) -> None:
        self.logger.info("Validating fact_disruption_events against schema.yaml")
        schema = self.load_schema()
        validator = Validator(schema)
        validator.validate_fact("fact_shipping_disruptions", df_fact)
        self.logger.info("Validation passed")

    def save(self, df_fact: pd.DataFrame) -> None:
        df_fact.to_csv(self.processed_path, index=False)
        self.logger.info("✅ Processed fact_disruption_events saved to %s", self.processed_path)

    def run(self) -> None:
        df = self.read_raw()
        df_fact = self.transform(df)
        self.validate(df_fact)
        self.save(df_fact)


if __name__ == "__main__":
    stager = DisruptionEventsStager()
    stager.run()
