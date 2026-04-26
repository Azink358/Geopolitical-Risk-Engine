import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, r2_score

class GeopoliticalModel:
    """
    GeopoliticalModel trains and evaluates an XGBoost Regressor
    to predict geopolitical risk outcomes.

    Methods:
    --------
    train(feature_matrix, target_values):
        Train an XGBoost Regressor on the feature matrix.

    evaluate(feature_matrix, true_values):
        Return RMSE and R-Squared scores for model performance.

    plot_feature_importance(feature_names):
        Generate a bar plot of feature importances.

    save_model(file_path):
        Save the trained model to disk using Joblib.

    load_model(file_path):
        Load a trained model from disk using Joblib.
    """

    def __init__(self):
        """Initialize the GeopoliticalModel with an XGBRegressor."""
        self.model = XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        self.is_trained = False

    def train(self, feature_matrix: pd.DataFrame, target_values: pd.Series):
        """
        Train the XGBoost Regressor.

        Args:
            feature_matrix (pd.DataFrame): Input features for training.
            target_values (pd.Series): Target variable ('Supply_Chain_Disruption_Index').
        """
        self.model.fit(feature_matrix, target_values)
        self.is_trained = True
        return self.model

    def evaluate(self, feature_matrix: pd.DataFrame, true_values: pd.Series) -> dict:
        """
        Evaluate the model using RMSE and R-Squared metrics.

        Args:
            feature_matrix (pd.DataFrame): Input features for evaluation.
            true_values (pd.Series): Ground truth target values.

        Returns:
            dict: Dictionary containing RMSE and R2 scores.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation.")

        # Predict target values using the trained model
        predicted_values = self.model.predict(feature_matrix)

        # Calculate evaluation metrics
        root_mean_squared_error = np.sqrt(mean_squared_error(true_values, predicted_values))
        r_squared_score = r2_score(true_values, predicted_values)

        return {
            "RMSE": root_mean_squared_error,
            "R2": r_squared_score
        }

    def plot_feature_importance(self, feature_names: list):
        """
        Plot feature importance scores.

        Args:
            feature_names (list): Names of features in the matrix.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before plotting feature importance.")

        importance_scores = self.model.feature_importances_

        plt.figure(figsize=(10, 6))
        plt.barh(feature_names, importance_scores)
        plt.xlabel("Importance Score")
        plt.ylabel("Features")
        plt.title("Geopolitical Factors Impacting Supply Chain Disruption")
        plt.tight_layout()
        plt.show()

    def save_model(self, file_path: str):
        """
        Save the trained model to disk.

        Args:
            file_path (str): File path to save the model.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before saving.")
        joblib.dump(self.model, file_path)

    def load_model(self, file_path: str):
        """
        Load a trained model from disk.

        Args:
            file_path (str): File path to load the model from.
        """
        self.model = joblib.load(file_path)
        self.is_trained = True
        return self.model
