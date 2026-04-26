import logging
import yaml
from pathlib import Path
import pandas as pd


class Validator:
    def __init__(self, schema_path="schema.yaml"):
        # Configure logging once
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

        # Accept either a path or a dict
        if isinstance(schema_path, (str, Path)):
            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = yaml.safe_load(f)
        elif isinstance(schema_path, dict):
            self.schema = schema_path
        else:
            raise TypeError("schema_path must be a str, Path, or dict")

    def _get_fact_def(self, fact_name: str):
        return next((f for f in self.schema.get("facts", []) if f.get("name") == fact_name), None)

    def _get_dim_def(self, dim_name: str):
        return next((d for d in self.schema.get("dimensions", []) if d.get("name") == dim_name), None)

    def validate_fact(self, fact_name: str, df: pd.DataFrame):
        fact_def = self._get_fact_def(fact_name)
        if not fact_def:
            raise ValueError(f"Fact {fact_name} not found in schema.yaml")

        expected_cols = fact_def.get("grain", []) + fact_def.get("measures", [])
        missing = [c for c in expected_cols if c not in df.columns]
        extra = [c for c in df.columns if c not in expected_cols]

        if missing:
            raise ValueError(f"{fact_name} missing columns: {missing}")
        if extra:
            self.logger.warning("%s has extra columns not in schema: %s", fact_name, extra)

        self.logger.info("✅ %s validated successfully (%d rows)", fact_name, len(df))

    def validate_dimension(self, dim_name: str, df: pd.DataFrame):
        dim_def = self._get_dim_def(dim_name)
        if not dim_def:
            raise ValueError(f"Dimension {dim_name} not found in schema.yaml")

        expected_cols = dim_def.get("attributes", [])
        missing = [c for c in expected_cols if c not in df.columns]
        extra = [c for c in df.columns if c not in expected_cols]

        if missing:
            raise ValueError(f"{dim_name} missing columns: {missing}")
        if extra:
            self.logger.warning("%s has extra columns not in schema: %s", dim_name, extra)

        self.logger.info("✅ %s validated successfully (%d rows)", dim_name, len(df))
