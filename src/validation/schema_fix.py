"""
Schema Fix Utility

Runs validation across all staged fact and dimension CSVs
to ensure they match schema.yaml definitions.
Auto-corrects column names when they are close variants.
"""

import pandas as pd
from pathlib import Path
from validator import Validator


def auto_fix_columns(df: pd.DataFrame, expected_cols: list) -> pd.DataFrame:
    """
    Attempt to auto-fix column names by stripping suffixes/prefixes
    and matching to expected schema names.
    """
    rename_map = {}
    for col in df.columns:
        if col in expected_cols:
            continue
        # Simple heuristics: strip common suffixes/prefixes
        normalized = (
            col.lower()
            .replace("_day", "")
            .replace("_mt", "")
            .replace("_value", "")
            .replace("_time", "")
            .replace("_extra", "")
        )
        for exp in expected_cols:
            if normalized == exp.lower():
                rename_map[col] = exp
                break

    if rename_map:
        df.rename(columns=rename_map, inplace=True)
    return df


def run_schema_fix(schema_path="schema.yaml", processed_dir="data/processed"):
    validator = Validator(schema_path)

    # Validate facts
    for fact in validator.schema.get("facts", []):
        table_name = fact["name"]
        csv_path = Path(processed_dir) / f"{table_name}.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            expected_cols = fact["grain"] + fact["measures"]
            df = auto_fix_columns(df, expected_cols)
            validator.validate_fact(table_name, df)
        else:
            validator.logger.warning("Fact file not found: %s", csv_path)

    # Validate dimensions
    for dim in validator.schema.get("dimensions", []):
        table_name = dim["name"]
        csv_path = Path(processed_dir) / f"{table_name}.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            expected_cols = dim["attributes"]
            df = auto_fix_columns(df, expected_cols)
            validator.validate_dimension(table_name, df)
        else:
            validator.logger.warning("Dimension file not found: %s", csv_path)


if __name__ == "__main__":
    run_schema_fix()
