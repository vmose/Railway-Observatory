import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
SAMPLE_GTFS = ROOT / "data" / "sample" / "sample_gtfs.zip"


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL", "postgresql://observatory:observatory@localhost:5432/observatory"
    )


def env(name: str) -> str:
    return os.environ.get(name, "").strip()


def auth_headers() -> dict:
    header, key = env("GTFS_API_KEY_HEADER"), env("GTFS_API_KEY")
    return {header: key} if header and key else {}
