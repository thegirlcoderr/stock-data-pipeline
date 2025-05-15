from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

# --- PATH DEFINITIONS ---
# These paths tell Airflow where to find your Python interpreter and scripts.

# Path to the Python interpreter inside virtual environment (airflow_venv)
# Example: "/Users/linda/airflow_venv/bin/python3"
python_interpreter_path = "/Users/linda/airflow_venv/bin/python3" # FIXME: VERIFY THIS PATH

# Path to project directory where scripts and .env file are located
# Example: "/Users/linda/Desktop/stocks_and_data"
project_directory_path = "/Users/linda/Desktop/stocks_and_data" # FIXME: VERIFY THIS PATH

# Path to virtual environment's 'activate' script
venv_activate_path = "/Users/linda/airflow_venv/bin/activate" # FIXME: VERIFY THIS PATH

# Full paths to scripts
fetch_script_path = f"{project_directory_path}/fetch_stock_data.py"
analyze_script_path = f"{project_directory_path}/fetch_and_analyze_stockdata.py"
# --- END OF PATH DEFINITIONS ---

# --- DAG Definition ---
# This block defines your workflow (the DAG).
with DAG(
    dag_id="stock_data_pipeline", # Unique identifier for this DAG in Airflow
    schedule="@daily",  # How often the DAG should run. "@daily" means once a day at midnight UTC.
                        # Other options: "@hourly", cron expressions (e.g., "0 0 * * MON-FRI"), None (for manual trigger only)
    start_date=pendulum.datetime(2024, 5, 14, tz="UTC"), # The date from which the DAG's schedule starts.
                                                        # It's good practice to use a date in the past.
    catchup=False, # If True, Airflow would try to run for all missed schedules between start_date and now.
                   # False is usually better for development to avoid many backruns.
    tags=["stock_data", "pipeline", "data_engineering"], # Tags help organize and filter DAGs in the UI.
    doc_md="""
    ### Stock Data Pipeline DAG
    This DAG orchestrates a pipeline to:
    1. Fetch daily stock data from Alpha Vantage API.
    2. Store the fetched data into an AWS RDS PostgreSQL database.
    3. Run a basic analysis script on the data in the database.
    """
) as dag:
    # --- Task 1: Fetch and Load Stock Data ---
    # This task uses BashOperator to run your fetch_stock_data.py script.
    fetch_and_load_stock_data_task = BashOperator(
        task_id="fetch_and_load_stock_data", # Unique ID for this task within the DAG
        # The bash command to execute:
        # 1. Activates the virtual environment.
        # 2. Changes directory to your project folder (so .env file is found by the script).
        # 3. Runs the fetch_stock_data.py script using the venv's Python.
        bash_command=(
            f"source {venv_activate_path} && "
            f"cd {project_directory_path} && "
            f"{python_interpreter_path} {fetch_script_path}"
        ),
        # Environment variables for the task's execution environment
        env={
            "no_proxy": "*",  # Helps with potential macOS SIGSEGV issues
            "PYTHONUNBUFFERED": "1", # Ensures Python script output is logged immediately
            "PYTHONFAULTHANDLER": "1" # Provides more detailed tracebacks for some crashes
        }
    )

    # --- Task 2: Analyze Stock Data ---
    # This task also uses BashOperator to run your fetch_and_analyze_stockdata.py script.
    run_analysis_task = BashOperator(
        task_id="run_stock_analysis", # Unique ID for this task
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
    )

    # --- Task Dependencies ---
    # This line defines the order of execution:
    # fetch_and_load_stock_data_task must complete successfully before run_analysis_task can start.
    fetch_and_load_stock_data_task >> run_analysis_task
