from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.operators.dummy_operator import DummyOperator

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'trigger_dbt_github_action',
    default_args=default_args,
    description='Trigger GitHub Action to run dbt models',
    schedule_interval=timedelta(hours=6),
    catchup=False,
    tags=['dbt', 'github-actions'],
)

start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

trigger_github_action = SimpleHttpOperator(
    task_id='trigger_dbt_run',
    http_conn_id='github_api',
    endpoint='repos/YOUR_USERNAME/dbt-airflow-github_actions/dispatches',
    method='POST',
    headers={
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'token {{ var.value.github_token }}'
    },
    data='{"event_type": "trigger-dbt-run"}',
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

start_task >> trigger_github_action >> end_task