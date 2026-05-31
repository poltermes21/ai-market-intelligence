from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def _fetch_and_store():
    import sys
    sys.path.insert(0, "/opt/airflow")
    from ingestion.hackernews import run
    count = run()
    print(f"HackerNews: stored {count} articles")


with DAG(
    dag_id="hackernews_ingestion",
    default_args=default_args,
    schedule_interval="0 7 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "hackernews"],
) as dag:

    fetch_store = PythonOperator(
        task_id="fetch_and_store",
        python_callable=_fetch_and_store,
    )

    run_dbt = BashOperator(
        task_id="run_dbt_staging",
        bash_command=(
            "cd /opt/airflow/dbt_project && "
            "dbt run --select staging.stg_articles --profiles-dir ."
        ),
    )

    fetch_store >> run_dbt
