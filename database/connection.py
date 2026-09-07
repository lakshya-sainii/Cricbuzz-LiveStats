from pathlib import Path
import os
import sqlite3

import pandas as pd
import pyodbc
from dotenv import load_dotenv

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME", "CricbuzzLiveStats")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "deployment_data"
CLOUD_DB = Path("/tmp/cricbuzz_cloud.db")

TABLES = [
    "teams",
    "players",
    "venues",
    "series",
    "matches",
    "player_match_stats",
]


def is_cloud_database():
    """Local machine uses SQL Server; Streamlit Cloud falls back to exported CSV data."""
    return not bool(DB_SERVER)


def _build_cloud_database():
    if CLOUD_DB.exists():
        return

    missing = [name for name in TABLES if not (DATA_DIR / f"{name}.csv").exists()]
    if missing:
        raise FileNotFoundError(
            "Missing deployment CSV files: " + ", ".join(f"{name}.csv" for name in missing)
        )

    conn = sqlite3.connect(CLOUD_DB)
    try:
        for table in TABLES:
            df = pd.read_csv(DATA_DIR / f"{table}.csv")
            df.to_sql(table, conn, if_exists="replace", index=False)

        # Add indexes useful for analytics and CRUD lookups.
        conn.execute("CREATE INDEX IF NOT EXISTS idx_players_id ON players(player_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_id ON matches(match_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_player ON player_match_stats(player_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_match ON player_match_stats(match_id)")
        conn.commit()
    finally:
        conn.close()


def get_connection():
    if not is_cloud_database():
        connection_string = (
            f"DRIVER={{{DB_DRIVER}}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )
        return pyodbc.connect(connection_string)

    _build_cloud_database()
    return sqlite3.connect(CLOUD_DB)
