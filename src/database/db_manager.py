import os
import pandas as pd
import sqlalchemy
from dotenv import load_dotenv

class DBManager:
    """
    DBManager: Handles database persistence for modeled data.
    - Reads DATABASE_URL from .env
    - Connects to Postgres
    - Saves/loads dimension, fact, and feature tables
    """

    def __init__(self, env_path=".env"):
        load_dotenv(env_path)
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL not found in .env")
        self.engine = sqlalchemy.create_engine(db_url)

    def save_table(self, df: pd.DataFrame, table_name: str):
        """Save DataFrame to database table."""
        df.to_sql(table_name, self.engine, index=False, if_exists="replace")
        print(f"✅ Saved {table_name} to database.")

    def load_table(self, table_name: str) -> pd.DataFrame:
        """Load table from database into DataFrame."""
        return pd.read_sql_table(table_name, self.engine)

    def list_tables(self):
        """List all tables in the database."""
        inspector = sqlalchemy.inspect(self.engine)
        return inspector.get_table_names()
