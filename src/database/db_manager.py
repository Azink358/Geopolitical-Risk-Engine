import os
import pandas as pd
import sqlalchemy
from dotenv import load_dotenv

try:
    import streamlit as st
except ImportError:
    st = None  # Streamlit not available locally

class DBManager:
    """
    DBManager: Handles persistence to both local Postgres and Supabase.
    - Local: reads DATABASE_URL from .env
    - Cloud: reads DATABASE_URL from st.secrets (if available)
    """

    def __init__(self, env_path=".env"):
        load_dotenv(env_path)

        # Local connection
        local_url = os.getenv("DATABASE_URL")
        self.local_engine = sqlalchemy.create_engine(local_url) if local_url else None

        # Supabase connection (only if running in Streamlit with secrets)
        cloud_url = None
        if st is not None:
            try:
                cloud_url = st.secrets["DATABASE_URL"]
            except Exception:
                cloud_url = None
        self.cloud_engine = sqlalchemy.create_engine(cloud_url) if cloud_url else None

    def save_table_dual(self, df: pd.DataFrame, table_name: str):
        """Save DataFrame to both local and Supabase (if available)."""
        if self.local_engine:
            df.to_sql(table_name, self.local_engine, index=False, if_exists="replace")
            print(f"✅ Saved {table_name} to Local Postgres.")
        if self.cloud_engine:
            df.to_sql(table_name, self.cloud_engine, index=False, if_exists="replace")
            print(f"🌐 Saved {table_name} to Supabase.")

    def load_table(self, table_name: str, use_cloud=False) -> pd.DataFrame:
        engine = self.cloud_engine if use_cloud else self.local_engine
        return pd.read_sql_table(table_name, engine)

    def list_tables(self, use_cloud=False):
        engine = self.cloud_engine if use_cloud else self.local_engine
        inspector = sqlalchemy.inspect(engine)
        return inspector.get_table_names()
