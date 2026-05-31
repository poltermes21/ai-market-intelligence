from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
}


def _run_full_dbt():
    import subprocess
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", "."],
        cwd="/opt/airflow/dbt_project",
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(f"dbt run failed:\n{result.stderr}")


def _generate_report():
    import sys
    sys.path.insert(0, "/opt/airflow")
    from report.generator import generate_daily_report
    report = generate_daily_report()
    print(f"Report generated ({len(report)} chars)")


with DAG(
    dag_id="daily_report",
    default_args=default_args,
    schedule_interval="0 10 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["report", "daily"],
) as dag:

    run_dbt_all = BashOperator(
        task_id="run_dbt_all_models",
        bash_command=(
            "cd /opt/airflow/dbt_project && "
            "dbt run --profiles-dir . && dbt run --select marts.daily_snapshot --profiles-dir ."
        ),
    )

    generate_report = PythonOperator(
        task_id="generate_daily_report",
        python_callable=_generate_report,
    )

    run_dbt_all >> generate_report
