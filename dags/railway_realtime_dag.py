from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.config import SQL_DIR
from src.ingestion.fetch_realtime import run_realtime
from src.transformations.run_sql import run_sql_files

# Set the interval to match your operator's feed refresh rate and rate limits.
with DAG(
    "railway_realtime",
    start_date=datetime(2024, 1, 1),
    schedule="*/10 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=1)},
) as dag:
    fetch = PythonOperator(task_id="fetch_snapshots", python_callable=run_realtime)
    disruptions = PythonOperator(
        task_id="update_disruptions",
        python_callable=run_sql_files,
        op_args=[[SQL_DIR / "marts" / "mart_service_disruptions.sql"]],
    )
    fetch >> disruptions
