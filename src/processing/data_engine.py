from src.processing.builders.dimension_builder import DimensionBuilder
from src.processing.builders.fact_builder import FactBuilder
from src.processing.builders.feature_builder import FeatureBuilder
from src.processing.builders.base_pipeline import BasePipeline
from src.database.db_manager import DBManager


class DataEngine:
    """
    DataEngine: Orchestrates schema-driven pipeline.
    - Loads raw data
    - Builds dimensions, facts, features
    - Persists outputs into Postgres via DBManager
    """

    def __init__(self, schema_path="schema.yaml", env_path=".env"):
        self.base = BasePipeline(schema_path)
        self.schema_path = schema_path
        self.db = DBManager(env_path)

    def run(self):
        # Load raw data
        dfs = {
            "supply_chain": self.base.load_csv("supply_chain"),
            "imports": self.base.load_csv("imports"),
            "shipping": self.base.load_csv("shipping"),
            "disruptions": self.base.load_csv("disruptions"),
            "response": self.base.load_csv("response"),
            "price": self.base.load_csv("price"),
        }
        dfs = {k: self.base.clean_columns(v) for k, v in dfs.items()}

        # Build dimensions
        dim_builder = DimensionBuilder(self.schema_path)
        dims = dim_builder.run_all(dfs)

        # Persist dimensions
        for name, df in dims.items():
            self.db.save_table(df, name)

        # Build facts
        fact_builder = FactBuilder(self.schema_path)
        facts = fact_builder.run_all(dfs, dims)

        # Persist facts
        for name, df in facts.items():
            self.db.save_table(df, name)

        # Build features
        feature_builder = FeatureBuilder(self.schema_path)
        features = feature_builder.build_feature_table(
            facts["supply_chain"],
            facts["imports"],
            facts["shipping"],
            facts["disruption"],
            facts["response"],
            facts["price"],
        )

        # Persist features
        self.db.save_table(features, "final_feature_table")

        self.base.log("🎯 End-to-end pipeline completed and persisted to Postgres.")
        return {"dimensions": dims, "facts": facts, "features": features}
