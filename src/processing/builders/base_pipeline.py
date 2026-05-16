import os
import logging
import pandas as pd
import yaml

class BasePipeline:
    """
    BasePipeline provides shared utilities for all builder classes.

    Responsibilities:
      - Configure logging for consistent output across builders
      - Load raw CSV files based on schema.yaml
      - Clean column names for consistency
      - Provide a save() method to persist DataFrames to CSV
      - Store schema path reference for validation and alignment
    """

    def __init__(self, schema_path="schema.yaml"):
        # Store schema path for reference
        self.schema_path = schema_path

        # Load schema.yaml into memory
        with open(schema_path, "r") as f:
            self.schema = yaml.safe_load(f)

        # Configure logger
        logging.basicConfig(level=logging.INFO, format="INFO:%(name)s:%(message)s")
        self.logger = logging.getLogger(self.__class__.__name__)

    def log(self, message: str):
        """
        Log a message with builder context.
        Parameters
        ----------
        message : str
            Message to log
        """
        self.logger.info(message)

    def load_csv(self, file_key: str) -> pd.DataFrame:
        """
        Load a raw CSV file based on schema.yaml file mapping.

        Parameters
        ----------
        file_key : str
            Logical name of the file (e.g., 'supply_chain', 'imports')

        Returns
        -------
        pd.DataFrame
            Loaded DataFrame
        """
        raw_path = self.schema["paths"]["raw_data"]
        filename = self.schema["files"][file_key]
        full_path = os.path.join(raw_path, filename)

        self.log(f"Loading CSV for {file_key} from {full_path}")
        return pd.read_csv(full_path)

    def clean_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean DataFrame column names:
          - Strip whitespace
          - Lowercase
          - Replace spaces with underscores

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame

        Returns
        -------
        pd.DataFrame
            Cleaned DataFrame
        """
        df.columns = (
            df.columns.str.strip()
                      .str.lower()
                      .str.replace(" ", "_")
        )
        self.log("Cleaned DataFrame column names.")
        return df

    def save(self, df: pd.DataFrame, subdir: str, name: str):
        """
        Save a DataFrame to CSV in the modeled directory.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to save
        subdir : str
            Subdirectory under data/modeled (e.g., 'facts', 'dimensions', 'features')
        name : str
            File name (without extension)

        Behavior
        --------
        - Creates directory if missing
        - Saves DataFrame as CSV
        - Logs save action
        """
        path = os.path.join(self.schema["paths"]["modeled_data"], subdir)
        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, f"{name}.csv")
        df.to_csv(file_path, index=False)
        self.log(f"Saved {name} to {file_path}")
