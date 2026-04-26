"""
Database Manager for Macro-Sentry Geopolitical Risk Engine.

Responsibilities:
    - Connect to target database using .env configuration
    - Drop/reload fact and dimension tables based on schema.yaml
    - Provide utility functions for querying and diagnostics
"""

import os
import logging
from pathlib import Path

import pandas as pd
import sqlalchemy
from sqlalchemy import text
import yaml
from dotenv import load_dotenv


class DBManager:
    """Minimal manager for database ingestion and queries."""

    def __init__(self,
                 schema_path: str = "schema.yaml",
                 processed_dir: str = "data/processed") -> None:
        # Logging setup
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

        # Load environment variables
        load_dotenv()

        # Prefer DATABASE_URL if defined
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            host = os.getenv("DB_HOST")
            port = os.getenv("DB_PORT")
            name = os.getenv("DB_NAME")
            user = os.getenv("DB_USER")
            password = os.getenv("DB_PASSWORD")
            if not all([host, port, name, user, password]):
                raise ValueError("Missing database credentials in .env file")
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"

        self.db_url = db_url
        self.engine = sqlalchemy.create_engine(self.db_url)

        # Load schema definition
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = yaml.safe_load(f)

        self.processed_dir = Path(processed_dir)

    def drop_all_tables(self) -> None:
        """Drop all tables defined in schema.yaml."""
        with self.engine.begin() as conn:
            for fact in self.schema.get("facts", []):
                conn.execute(text(f"DROP TABLE IF EXISTS {fact['name']} CASCADE;"))
                self.logger.info("Dropped table: %s", fact["name"])
            for dim in self.schema.get("dimensions", []):
                conn.execute(text(f"DROP TABLE IF EXISTS {dim['name']} CASCADE;"))
                self.logger.info("Dropped table: %s", dim["name"])

    def load_all(self) -> None:
        """Load all fact CSVs into database tables."""
        summary = []
        for fact in self.schema.get("facts", []):
            table_name = fact["name"]
            csv_path = self.processed_dir / f"{table_name}.csv"

            if not csv_path.exists():
                self.logger.warning("Processed file not found: %s", csv_path)
                summary.append((table_name, "❌ Not Found"))
                continue

            df = pd.read_csv(csv_path)
            df.to_sql(table_name, self.engine, if_exists="replace", index=False)
            self.logger.info("Loaded %s (rows: %d)", table_name, len(df))
            summary.append((table_name, len(df)))

        self.logger.info("📊 Ingestion Summary")
        for table_name, count in summary:
            self.logger.info("%-25s %s", table_name, count)

    def query(self, sql: str) -> pd.DataFrame:
        """Run a SQL query and return DataFrame."""
        with self.engine.begin() as conn:
            return pd.read_sql(text(sql), conn)
