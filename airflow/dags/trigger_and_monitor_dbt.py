from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
import requests
import time

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
}

dag = DAG(
    'trigger_and_monitor_dbt',
    default_args=default_args,
    description='Trigger GitHub Action and monitor dbt run status',
    schedule_interval=timedelta(hours=2),  # Run every 2 hours
    catchup=False,
    tags=['dbt', 'github-actions', 'monitoring'],
)

def wait_and_check_status(**context):
    """Wait for GitHub Action to start and monitor its progress"""
    from airflow.models import Variable
    
    github_token = Variable.get("github_token")
    github_repo = Variable.get("github_repo")
    
    print("⏳ Waiting 30 seconds for GitHub Action to start...")
    time.sleep(30)
    
    # Check workflow status multiple times
    max_checks = 10  # Check for up to 10 minutes
    check_interval = 60  # Check every minute
    
    for attempt in range(1, max_checks + 1):
        print(f"\n🔍 Status Check #{attempt}/{max_checks}")
        
        url = f'https://api.github.com/repos/{github_repo}/actions/runs'
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {github_token}'
        }
        
        response = requests.get(url, headers=headers, params={'per_page': 3})
        
        if response.status_code == 200:
            runs = response.json()['workflow_runs']
            
            if runs:
                latest_run = runs[0]
                status = latest_run['status']
                conclusion = latest_run.get('conclusion')
                workflow_name = latest_run['name']
                run_url = latest_run['html_url']
                created_at = latest_run['created_at']
                
                print(f"📊 Workflow: {workflow_name}")
                print(f"📅 Started: {created_at}")
                print(f"🔗 URL: {run_url}")
                print(f"📊 Status: {status}")
                print(f"✅ Result: {conclusion or 'in_progress'}")
                
                if status == 'completed':
                    if conclusion == 'success':
                        print("🎉 SUCCESS: dbt run completed successfully!")
                        return "success"
                    elif conclusion == 'failure':
                        print("❌ FAILED: dbt run failed!")
                        raise Exception("GitHub Action failed - check logs")
                    else:
                        print(f"⚠️ COMPLETED with status: {conclusion}")
                        return conclusion
                        
                elif status == 'in_progress':
                    print(f"⏳ Still running... (check {attempt}/{max_checks})")
                    if attempt < max_checks:
                        print(f"⏰ Waiting {check_interval} seconds before next check...")
                        time.sleep(check_interval)
                    continue
                else:
                    print(f"🔄 Status: {status}")
                    if attempt < max_checks:
                        time.sleep(check_interval)
                    continue
            else:
                print("❓ No workflow runs found")
                if attempt < max_checks:
                    time.sleep(check_interval)
                continue
        else:
            print(f"❌ API Error: {response.status_code}")
            if attempt < max_checks:
                time.sleep(check_interval)
            continue
    
    # If we get here, we've exceeded max checks
    print("⏰ TIMEOUT: Exceeded maximum monitoring time")
    print("🔗 Check GitHub Actions manually for current status")
    return "timeout"

start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

trigger_github_action = SimpleHttpOperator(
    task_id='trigger_dbt_run',
    http_conn_id='github_api',
    endpoint='repos/{{var.value.github_repo}}/dispatches',
    method='POST',
    headers={
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'token {{ var.value.github_token }}'
    },
    data='{"event_type": "trigger-dbt-run"}',
    log_response=True,
    dag=dag,
)

monitor_status = PythonOperator(
    task_id='monitor_dbt_status',
    python_callable=wait_and_check_status,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

start_task >> trigger_github_action >> monitor_status >> end_task