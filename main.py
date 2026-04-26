# main.py

import argparse
import yaml
from pathlib import Path
from src.processing.data_engine import DataEngine
from src.processing.staging.stg_dimensions import run_all

def align_columns(df, schema_map):
    """Rename columns based on schema mapping dictionary."""
    return df.rename(columns={k: v for k, v in schema_map.items() if k in df.columns})

def main():
    parser = argparse.ArgumentParser(description="Macro-Sentry Geopolitical Risk Engine")
    parser.add_argument("--all", action="store_true", help="Run full pipeline: facts + dimensions")
    parser.add_argument("--facts", action="store_true", help="Run only fact stagers")
    parser.add_argument("--dims", action="store_true", help="Run only dimension staging")
    args = parser.parse_args()

    # Load schema mapping
    schema_path = Path("schema_mappings.yaml")
    with open(schema_path, "r") as f:
        schema_map = yaml.safe_load(f)["mappings"]

    # Initialize DataEngine
    engine = DataEngine(schema_path="schema.yaml")

    if args.all:
        # Run fact stagers first
        engine.run_all()

        # After facts are rebuilt, load them into memory
        import pandas as pd
        facts = {
            "fact_energy_volatility": pd.read_csv("data/processed/fact_energy_volatility.csv"),
            "fact_apac_dependency": pd.read_csv("data/processed/fact_apac_dependency.csv"),
            "fact_supply_chain_impact": pd.read_csv("data/processed/fact_supply_chain_impact.csv"),
            "fact_shipping_disruptions": pd.read_csv("data/processed/fact_shipping_disruptions.csv"),
            "fact_strategic_responses": pd.read_csv("data/processed/fact_strategic_responses.csv"),
        }

        # Align columns
        facts = {name: align_columns(df, schema_map) for name, df in facts.items()}

        # Dimension sources
        dim_sources = {
            "dim_country": facts["fact_supply_chain_impact"],
            "dim_sector": facts["fact_supply_chain_impact"],
            "dim_fuel_type": facts["fact_apac_dependency"],
            "dim_conflict_phase": facts["fact_energy_volatility"],
            "dim_response": facts["fact_strategic_responses"],
            "dim_event": facts["fact_shipping_disruptions"],
        }

        # Run dimension staging
        run_all(dim_sources, facts)
        print("✅ Full pipeline completed successfully")

    elif args.facts:
        engine.run_all()
        print("✅ Fact stagers completed successfully")

    elif args.dims:
        # Load existing facts from processed folder
        import pandas as pd
        facts = {
            "fact_energy_volatility": pd.read_csv("data/processed/fact_energy_volatility.csv"),
            "fact_apac_dependency": pd.read_csv("data/processed/fact_apac_dependency.csv"),
            "fact_supply_chain_impact": pd.read_csv("data/processed/fact_supply_chain_impact.csv"),
            "fact_shipping_disruptions": pd.read_csv("data/processed/fact_shipping_disruptions.csv"),
            "fact_strategic_responses": pd.read_csv("data/processed/fact_strategic_responses.csv"),
        }

        facts = {name: align_columns(df, schema_map) for name, df in facts.items()}

        dim_sources = {
            "dim_country": facts["fact_supply_chain_impact"],
            "dim_sector": facts["fact_supply_chain_impact"],
            "dim_fuel_type": facts["fact_apac_dependency"],
            "dim_conflict_phase": facts["fact_energy_volatility"],
            "dim_response": facts["fact_strategic_responses"],
            "dim_event": facts["fact_shipping_disruptions"],
        }

        run_all(dim_sources, facts)
        print("✅ Dimension staging completed successfully")

if __name__ == "__main__":
    main()
