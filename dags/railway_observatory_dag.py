from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from railway_observatory.pipeline import load_schedule, load_realtime, run_sql_models, run_quality_checks

DEFAULT_ARGS = {"owner": "railway-observatory", "retries": 2, "retry_delay": timedelta(minutes=2)}

with DAG(
    dag_id="railway_observatory",
    description="Collect railway timetable and realtime observations, then model them with SQL.",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2025, 1, 1),
    schedule="0 * * * *",
    catchup=False,
    tags=["railway", "gtfs", "observatory"],
) as dag:
    schedule = PythonOperator(task_id="load_schedule", python_callable=load_schedule)
    realtime = PythonOperator(task_id="load_realtime_snapshot", python_callable=load_realtime)
    models = PythonOperator(task_id="run_sql_models", python_callable=run_sql_models)
    quality = PythonOperator(task_id="run_quality_checks", python_callable=run_quality_checks)
    [schedule, realtime] >> models >> quality
