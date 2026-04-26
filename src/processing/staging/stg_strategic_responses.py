"""
Staging script for Strategic Responses dataset.

Transforms raw strategic response data into a fact table:
    fact_strategic_responses(response_key, date_key, country_key, conflict_phase_key,
                             response_category, institution, urgency_level, implementation_status, measures...)

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


class StrategicResponsesStager:
    def __init__(self,
                 raw_path="data/raw/strategic_response_measures.csv",
                 processed_path="data/processed/fact_strategic_responses.csv",
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
        self.logger.info("Reading raw strategic responses data from %s", self.raw_path)
        return pd.read_csv(self.raw_path)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Transforming strategic response measures data")

        # Rename raw headers → schema-friendly compact names
        df.rename(columns={
            "Response_ID": "response_key",
            "Date": "date_key",
            "Country": "country_key",
            "Conflict_Phase": "conflict_phase_key",
            "Response_Category": "response_category",
            "Implementing_Institution": "institution",
            "Urgency_Level": "urgency_level",
            "Implementation_Status": "implementation_status",
            "Estimated_Cost_MUSD": "estimated_cost_usd",
            "Effectiveness_Score": "effectiveness_score",
            "ME_Dependency_Reduction_Pct": "dependency_reduction_pct"
        }, inplace=True)

        # Ensure numeric measures are properly typed
        numeric_cols = [
            "estimated_cost_usd",
            "effectiveness_score",
            "dependency_reduction_pct"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Keep only fact grain + measures
        fact_cols = [
                        "response_key", "date_key", "country_key", "conflict_phase_key",
                        "response_category", "institution", "urgency_level", "implementation_status"
                    ] + numeric_cols
        df_fact = df[fact_cols]

        self.logger.info("Transformation complete: %d rows, %d columns", df_fact.shape[0], df_fact.shape[1])
        return df_fact

    def validate(self, df_fact: pd.DataFrame) -> None:
        self.logger.info("Validating fact_strategic_responses against schema.yaml")
        schema = self.load_schema()
        validator = Validator(schema)
        validator.validate_fact("fact_strategic_responses", df_fact)
        self.logger.info("Validation passed")

    def save(self, df_fact: pd.DataFrame) -> None:
        df_fact.to_csv(self.processed_path, index=False)
        self.logger.info("✅ Processed fact_strategic_responses saved to %s", self.processed_path)

    def run(self) -> None:
        df = self.read_raw()
        df_fact = self.transform(df)
        self.validate(df_fact)
        self.save(df_fact)


if __name__ == "__main__":
    stager = StrategicResponsesStager()
    stager.run()
