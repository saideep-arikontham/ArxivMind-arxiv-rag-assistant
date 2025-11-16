from datetime import datetime, timedelta

import psycopg2
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import asyncio

sys.path.insert(0, "/opt/airflow")

from src.db.utils.chat_history import insert_into_first_table


def hello_world():
    """Simple hello world function."""
    print("Hello from Airflow! Week 1 is working.")
    return "success"


def check_services():
    """Check if other services are accessible."""
    try:
        # Check API health
        response = requests.get("http://fastapi:8000/api/v1/health", timeout=5)
        print(f"API Health: {response.status_code}")

        # Check database connection
        conn = psycopg2.connect(host="postgres", port=5432, database="arxivmind_db", user="arxivmind_user", password="arxivmind_password")
        print("Database: Connected successfully")
        conn.close()

        return "Services are accessible"
    except Exception as e:
        print(f"Service check failed: {e}")
        raise

def log_in_table():
    """Log a record into postgres table"""
    asyncio.run(insert_into_first_table(name="Dag Ran Successfully"))



# DAG configuration
default_args = {
    "owner": "rag",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    "hello_world_week1",
    default_args=default_args,
    description="Hello World DAG for Week 1",
    schedule=None,
    catchup=False,
    tags=["week1", "testing"],
)

# Define tasks
hello_task = PythonOperator(
    task_id="hello_world",
    python_callable=hello_world,
    dag=dag,
)

service_check_task = PythonOperator(
    task_id="check_services",
    python_callable=check_services,
    dag=dag,
)

record_successful_dag_run = PythonOperator(
    task_id="log_in_table",
    python_callable=log_in_table,
    dag=dag,
)

# Set task dependencies
hello_task >> service_check_task >> record_successful_dag_run