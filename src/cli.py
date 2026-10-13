"""Run the pipeline without Airflow:  python -m src.cli <command>"""
import argparse

from src.config import SAMPLE_GTFS, SQL_DIR, env
from src.ingestion.fetch_gtfs import load_gtfs
from src.ingestion.fetch_realtime import run_realtime
from src.transformations.run_sql import run_sql_dir
from src.validation.validate_feed import run_quality_checks


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["init", "load-gtfs", "load-sample", "transform", "check", "realtime"])
    p.add_argument("--source", help="GTFS zip path or URL (default: $GTFS_STATIC_URL)")
    a = p.parse_args()

    if a.command == "init":
        run_sql_dir(SQL_DIR / "raw")
    elif a.command == "load-gtfs":
        print("feed_id:", load_gtfs(a.source or env("GTFS_STATIC_URL")))
    elif a.command == "load-sample":
        print("feed_id:", load_gtfs(str(SAMPLE_GTFS)))
    elif a.command == "transform":
        run_sql_dir(SQL_DIR / "staging")
        run_sql_dir(SQL_DIR / "marts")
    elif a.command == "check":
        run_quality_checks(SQL_DIR / "quality_checks")
    elif a.command == "realtime":
        print(run_realtime())


if __name__ == "__main__":
    main()
