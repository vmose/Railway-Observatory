from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.config import SQL_DIR, env
from src.ingestion.fetch_gtfs import load_gtfs
from src.transformations.run_sql import run_sql_dir
from src.validation.validate_feed import run_quality_checks

with DAG(
    "railway_schedule",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 3, "retry_delay": timedelta(minutes=5)},
) as dag:
    init = PythonOperator(task_id="init_schema", python_callable=run_sql_dir, op_args=[SQL_DIR / "raw"])
    # validates the zip, then loads into raw.*; skipped automatically if the feed is unchanged
    load = PythonOperator(task_id="load_gtfs", python_callable=lambda: load_gtfs(env("GTFS_STATIC_URL")))
    staging = PythonOperator(task_id="staging", python_callable=run_sql_dir, op_args=[SQL_DIR / "staging"])
    marts = PythonOperator(task_id="marts", python_callable=run_sql_dir, op_args=[SQL_DIR / "marts"])
    checks = PythonOperator(task_id="quality_checks", python_callable=run_quality_checks,
                            op_args=[SQL_DIR / "quality_checks"])
    init >> load >> staging >> marts >> checks
