"""
Data Engine orchestrates all staging modules.

Runs each stager sequentially, validates against schema.yaml,
and writes processed fact tables to data/processed/.
"""

import importlib
import yaml
from pathlib import Path


class DataEngine:
    def __init__(self, schema_path="schema.yaml"):
        self.schema_path = Path(schema_path)
        with open(self.schema_path, "r") as f:
            self.schema = yaml.safe_load(f)

        # Register stagers here
        self.stagers = [
            "src.processing.staging.stg_energy_volatility.EnergyVolatilityStager",
            "src.processing.staging.stg_maritime_costs.MaritimeCostsStager",
            "src.processing.staging.stg_disruption_events.DisruptionEventsStager",
            "src.processing.staging.stg_strategic_responses.StrategicResponsesStager",
            "src.processing.staging.stg_supply_chain.SupplyChainImpactStager",
            "src.processing.staging.stg_apac_dependency.APACDependencyStager",
        ]

    def run_all(self):
        for stager_path in self.stagers:
            module_name, class_name = stager_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            stager_class = getattr(module, class_name)
            stager = stager_class(schema_path=self.schema_path)
            print(f"🚀 Running {class_name}...")
            stager.run()
        print("✅ All stagers completed successfully")
