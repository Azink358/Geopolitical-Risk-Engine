import argparse
import logging
import pandas as pd
from src.processing.builders.dimension_builder import DimensionBuilder
from src.processing.builders.fact_builder import FactBuilder
from src.processing.builders.feature_builder import FeatureBuilder
from src.processing.builders.base_pipeline import BasePipeline
from src.database.db_manager import DBManager
from src.models.risk_predictor import RiskPredictor  # <-- NEW import

# === Configure logging globally ===
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)


def run_pipeline(schema_path="schema.yaml", env_path=".env",
                 build_dims=True, build_facts=True, build_features=True,
                 persist=True, train_model=False, run_cv=False):
    base = BasePipeline(schema_path)
    db = DBManager(env_path)

    # === Step 1: Load raw data ===
    dfs = {
        "supply_chain": base.load_csv("supply_chain"),
        "imports": base.load_csv("imports"),
        "shipping": base.load_csv("shipping"),
        "disruptions": base.load_csv("disruptions"),
        "response": base.load_csv("response"),
        "price": base.load_csv("price"),
    }
    dfs = {k: base.clean_columns(v) for k, v in dfs.items()}

    dims, facts, final_features = {}, {}, None

    # === Step 2: Build dimensions ===
    if build_dims:
        dim_builder = DimensionBuilder(schema_path)
        dims = dim_builder.run_all(dfs)
        if persist:
            for name, df in dims.items():
                db.save_table(df, f"dim_{name}")

    # === Step 3: Build facts ===
    if build_facts:
        fact_builder = FactBuilder(schema_path)
        facts = fact_builder.run_all(dfs, dims)
        if persist:
            for name, df in facts.items():
                db.save_table(df, f"fact_{name}")

    # === Step 4: Build features ===
    if build_features:
        feature_builder = FeatureBuilder(schema_path)
        final_features = feature_builder.build_feature_table(
            facts.get("supply_chain", pd.DataFrame()),
            facts.get("imports", pd.DataFrame()),
            facts.get("shipping", pd.DataFrame()),
            facts.get("disruption", pd.DataFrame()),
            facts.get("response", pd.DataFrame()),
            facts.get("price", pd.DataFrame()),
        )
        if persist:
            db.save_table(final_features, "final_feature_table")

    # === Step 5: Train model (optional) ===
    if train_model and final_features is not None:
        predictor = RiskPredictor(env_path=env_path, use_db=persist)
        df = predictor.load_features()
        rmse, r2 = predictor.train(df)
        predictor.save_model()
        predictor.save_feature_importance(df)  # <-- NEW line
        logging.info(f"✅ Risk model trained. RMSE={rmse:.2f}, R²={r2:.2f}")

    # === Step 6: Cross-validation (optional) ===
    if run_cv and final_features is not None:
        predictor = RiskPredictor(env_path=env_path, use_db=persist)
        df = predictor.load_features()
        rmse_scores, r2_scores = predictor.cross_validate(df, n_splits=5)

        # Export CV results to CSV
        cv_df = pd.DataFrame({
            "fold": list(range(1, len(rmse_scores) + 1)),
            "rmse": rmse_scores,
            "r2": r2_scores
        })
        cv_path = "data/modeled/cv_results.csv"
        cv_df.to_csv(cv_path, index=False)
        logging.info(f"💾 Cross-validation results saved to {cv_path}")

        # === Step 7: Consolidated summary export ===
    if train_model and final_features is not None:
        try:
            importance_df = pd.read_csv("data/modeled/feature_importance.csv")
        except FileNotFoundError:
            importance_df = pd.DataFrame(columns=["feature", "importance"])

        try:
            cv_df = pd.read_csv("data/modeled/cv_results.csv")
            mean_rmse = cv_df['rmse'].mean()
            mean_r2 = cv_df['r2'].mean()
        except FileNotFoundError:
            mean_rmse, mean_r2 = None, None

        summary_rows = [
            {"metric": "Mean RMSE", "value": mean_rmse},
            {"metric": "Mean R²", "value": mean_r2}
        ]
        summary_df = pd.DataFrame(summary_rows)

        if not importance_df.empty:
            importance_df = importance_df.rename(columns={"feature": "metric", "importance": "value"})
            summary_df = pd.concat([summary_df, importance_df], ignore_index=True)

        summary_path = "data/modeled/model_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        logging.info(f"💾 Consolidated model summary saved to {summary_path}")

    base.log("🎯 Pipeline run completed.")
    return {"dimensions": dims, "facts": facts, "features": final_features}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run schema-driven pipeline with CLI flags.")
    parser.add_argument("--schema", default="schema.yaml", help="Path to schema file")
    parser.add_argument("--env", default=".env", help="Path to .env file with DB credentials")
    parser.add_argument("--no-dims", action="store_true", help="Skip building dimensions")
    parser.add_argument("--no-facts", action="store_true", help="Skip building facts")
    parser.add_argument("--no-features", action="store_true", help="Skip building features")
    parser.add_argument("--no-persist", action="store_true", help="Skip persisting to database")
    parser.add_argument("--train-model", action="store_true", help="Train risk predictor model after pipeline")
    parser.add_argument("--cv", action="store_true", help="Run k-fold cross-validation after pipeline")  # <-- NEW flag

    args = parser.parse_args()

    run_pipeline(
        schema_path=args.schema,
        env_path=args.env,
        build_dims=not args.no_dims,
        build_facts=not args.no_facts,
        build_features=not args.no_features,
        persist=not args.no_persist,
        train_model=args.train_model,
        run_cv=args.cv
    )
