from __future__ import annotations

import pendulum
from datetime import timedelta # Import timedelta for retry_delay

from airflow.models.dag import DAG
from airflow.models.param import Param 
from airflow.operators.bash import BashOperator

# --- PATH DEFINITIONS ---
python_interpreter_path = "/Users/linda/airflow_venv/bin/python3" 
project_directory_path = "/Users/linda/Desktop/stocks_and_data" 
venv_activate_path = "/Users/linda/airflow_venv/bin/activate" 
fetch_script_path = f"{project_directory_path}/fetch_stock_data.py"
analyze_script_path = f"{project_directory_path}/fetch_and_analyze_stockdata.py"
# --- END OF PATH DEFINITIONS ---

# Default arguments for all tasks in the DAG
# These can be overridden at the task level
default_args = {
    'owner': 'airflow', # The owner of the DAG
    'depends_on_past': False, # Tasks do not depend on the success of their previous run
    'email_on_failure': False, # Disable email on failure for now (requires email setup)
    'email_on_retry': False,   # Disable email on retry for now
    'retries': 1, # Number of retries to attempt before marking the task as failed
    'retry_delay': timedelta(minutes=1), # How long to wait before retrying (e.g., 1 minute)
}

with DAG(
    dag_id="stock_data_pipeline",
    default_args=default_args, # Apply the default_args to this DAG
    schedule=None, 
    start_date=pendulum.datetime(2024, 5, 14, tz="UTC"),
    catchup=False,
    tags=["stock_data", "pipeline", "parameterized"],
    params={
        "stock_symbol": Param("IBM", type="string", title="Stock Symbol", description="The stock symbol to fetch data for (e.g., AAPL, MSFT, IBM)."),
        "output_size": Param("compact", type="string", enum=["compact", "full"], title="Output Size", description="Alpha Vantage API output size ('compact' for last 100, 'full' for all history).")
    },
    doc_md="""
    ### Parameterized Stock Data Pipeline DAG
    This DAG orchestrates the fetching, storing, and analysis of daily stock data.
    - Fetches data from Alpha Vantage API for a configurable stock symbol.
    - Stores data into the `daily_stock_data` table in PostgreSQL (AWS RDS).
    - Runs a basic analysis script on the data in the database.
    """
) as dag:
    fetch_and_load_stock_data_task = BashOperator(
        task_id="fetch_and_load_stock_data",
        bash_command=(
            f"source {venv_activate_path} && "
            f"cd {project_directory_path} && "
            f"{python_interpreter_path} {fetch_script_path} "
            f"--symbol \"{{{{ params.stock_symbol }}}}\" "
            f"--outputsize \"{{{{ params.output_size }}}}\""
        ),
        env={
            "no_proxy": "*",
            "PYTHONUNBUFFERED": "1",
            "PYTHONFAULTHANDLER": "1"
        }
        # Retries for this task will use the default_args (1 retry, 1 min delay)
        # You could override them here if needed, e.g., retries=3
    )

    run_analysis_task = BashOperator(
        task_id="run_stock_analysis",
        bash_command=(
            f"source {venv_activate_path} && "
            f"cd {project_directory_path} && "
            f"{python_interpreter_path} {analyze_script_path}"
        ),
        env={
            "no_proxy": "*",
            "PYTHONUNBUFFERED": "1",
            "PYTHONFAULTHANDLER": "1"
        }
        # Retries for this task will also use the default_args
    )

    fetch_and_load_stock_data_task >> run_analysis_task
