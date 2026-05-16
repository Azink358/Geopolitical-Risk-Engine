import logging

class Validator:
    """
    Validator enforces schema compliance for fact tables.

    Responsibilities:
      - Ensure grain columns have no nulls
      - Ensure grain columns are unique (no duplicates)
      - Verify required metrics exist in the DataFrame
      - Provide logging feedback for validation steps
    """

    def __init__(self):
        # Configure logger for Validator
        logging.basicConfig(level=logging.INFO, format="INFO:%(name)s:%(message)s")
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_fact(self, df, grain_cols, metrics=None):
        """
        Validate a fact table against schema rules.

        Parameters
        ----------
        df : pd.DataFrame
            Fact table DataFrame to validate
        grain_cols : list
            List of grain columns that define uniqueness
        metrics : list, optional
            List of required metric columns (from schema.yaml)

        Raises
        ------
        ValueError
            If nulls or duplicates are found in grain columns,
            or if required metrics are missing
        """

        # 1. Null check
        if df[grain_cols].isnull().any().any():
            raise ValueError(f"❌ Nulls found in grain columns {grain_cols}")
        else:
            self.logger.info(f"✅ No nulls in grain columns {grain_cols}")

        # 2. Duplicate check
        if df.duplicated(subset=grain_cols).any():
            raise ValueError(f"❌ Duplicates found on grain {grain_cols}")
        else:
            self.logger.info(f"✅ No duplicates on grain {grain_cols}")

        # 3. Metrics existence check
        if metrics:
            missing = [m for m in metrics if m not in df.columns]
            if missing:
                raise ValueError(f"❌ Missing required metrics: {missing}")
            else:
                self.logger.info(f"✅ All required metrics present: {metrics}")
