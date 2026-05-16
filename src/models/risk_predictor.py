# src/models/risk_predictor.py

import os
import logging
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from src.database.db_manager import DBManager
import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class RiskPredictor:
    """
    RiskPredictor trains and evaluates an XGBoost regression model
    to estimate GDP impact from the final_feature_table.
    """

    def __init__(self, schema_path="schema.yaml", env_path=".env", use_db=True):
        self.schema_path = schema_path
        self.env_path = env_path
        self.use_db = use_db
        self.model = None

    def load_features(self, csv_path="data/modeled/features/final_feature_table.csv"):
        """Load features either from DB or CSV snapshot."""
        if self.use_db:
            db = DBManager(self.env_path)
            df = db.load_table("final_feature_table")
            logger.info("Loaded features from database.")
        else:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded features from CSV: {csv_path}")

        # enforce integer keys
        for key in ["country_key", "date_key", "conflict_phase_key"]:
            if key in df.columns:
                df[key] = df[key].astype("Int64")

        return df

    @staticmethod
    def preprocess(df):
        """Prepare feature matrix and target."""
        if "estimated_gdp_impact_musd" not in df.columns:
            raise ValueError("Target column 'estimated_gdp_impact_musd' not found in features.")

        y = df["estimated_gdp_impact_musd"]
        x = df.drop(columns=["estimated_gdp_impact_musd"])

        # one-hot encode categorical keys
        x = pd.get_dummies(x, columns=["country_key", "conflict_phase_key"], drop_first=True)

        logger.info("Preprocessing complete: features and target prepared.")
        return x, y

    def train(self, df, test_size=0.2, random_state=42):
        """Train XGBoost regression model."""
        x, y = self.preprocess(df)
        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=test_size, random_state=random_state
        )

        self.model = XGBRegressor(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state
        )
        self.model.fit(x_train, y_train)
        self.feature_names = x_train.columns

        y_pred = self.model.predict(x_test)

        # ✅ Manual RMSE calculation (safe across all sklearn versions)
        mse = mean_squared_error(y_test, y_pred)
        rmse = mse ** 0.5
        r2 = r2_score(y_test, y_pred)

        logger.info(f"Model trained. RMSE: {rmse:.2f}, R²: {r2:.2f}")

        # === Log top 10 most important features ===
        importance = pd.Series(self.model.feature_importances_, index=x.columns)
        top10 = importance.sort_values(ascending=False).head(10)
        logger.info("Top 10 feature importances:")
        for feature, score in top10.items():
            logger.info(f"  {feature}: {score:.4f}")

        return rmse, r2

    def cross_validate(self, df, n_splits=5, random_state=42):
        """Run k-fold cross-validation to validate model stability."""
        x, y = self.preprocess(df)

        # Define k-fold splitter
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

        # XGBoost regressor with same params
        model = XGBRegressor(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state
        )

        # Cross-validation scores
        mse_scores = cross_val_score(model, x, y, cv=kf, scoring="neg_mean_squared_error")
        r2_scores = cross_val_score(model, x, y, cv=kf, scoring="r2")

        # Convert MSE to RMSE
        rmse_scores = np.sqrt(-mse_scores)

        logger.info(f"Cross-validation ({n_splits}-fold):")
        logger.info(f"  RMSE scores: {rmse_scores}")
        logger.info(f"  Mean RMSE: {rmse_scores.mean():.2f}")
        logger.info(f"  R² scores: {r2_scores}")
        logger.info(f"  Mean R²: {r2_scores.mean():.2f}")

        return rmse_scores, r2_scores

    def feature_importance(self):
        """Return feature importance scores."""
        if self.model is None:
            raise ValueError("Model not trained yet.")
        importance = pd.Series(self.model.feature_importances_)
        logger.info("Feature importance extracted.")
        return importance

    def save_model(self, path="data/modeled/risk_model.json"):
        """Save trained model to disk."""
        if self.model is None:
            raise ValueError("Model not trained yet.")
        self.model.save_model(path)
        logger.info(f"Model saved to {path}")

    def save_feature_importance(self, df, top_n=10):
        """Save top N feature importances to CSV for dashboard use."""
        importance = pd.Series(self.model.feature_importances_, index=self.feature_names)
        importance = importance.sort_values(ascending=False).head(top_n).reset_index()
        importance.columns = ["feature", "importance"]

        path = "data/modeled/feature_importance.csv"
        importance.to_csv(path, index=False)
        logger.info(f"💾 Feature importance saved to {path}")

