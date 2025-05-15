from __future__ import annotations

import pendulum
from datetime import timedelta

from airflow.models.dag import DAG
from airflow.models.param import Param 
from airflow.operators.bash import BashOperator

# --- PATH DEFINITIONS ---
python_interpreter_path = "/Users/linda/airflow_venv/bin/python3" 
project_directory_path = "/Users/linda/Desktop/stocks_and_data" 
venv_activate_path = "/Users/linda/airflow_venv/bin/activate" 

fetch_script_path = f"{project_directory_path}/fetch_stock_data.py"
transform_script_path = f"{project_directory_path}/clean_and_transform_data.py" # Path to new script
analyze_script_path = f"{project_directory_path}/fetch_and_analyze_stockdata.py"
# --- END OF PATH DEFINITIONS ---

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id="stock_data_pipeline",
    default_args=default_args,
    schedule=None, 
    start_date=pendulum.datetime(2024, 5, 14, tz="UTC"), # Adjusted start date slightly
    catchup=False,
    tags=["stock_data", "pipeline", "transform"], # Added new tag
    params={
        "stock_symbol": Param("IBM", type="string", title="Stock Symbol", description="The stock symbol to fetch data for (e.g., AAPL, MSFT, IBM)."),
        "output_size": Param("compact", type="string", enum=["compact", "full"], title="Output Size", description="Alpha Vantage API output size ('compact' for last 100, 'full' for all history).")
    },
    doc_md="""
    ### Stock Data Pipeline DAG
    This DAG orchestrates a pipeline to:
    1. Fetch daily stock data from Alpha Vantage API for a configurable symbol.
    2. Store the raw data into an AWS RDS PostgreSQL database.
    3. Clean and transform the raw data (e.g., calculate moving averages).
    4. Store transformed data into a new table.
    5. Run a basic analysis script on the transformed data.
    """
) as dag:
    fetch_and_load_raw_data_task = BashOperator( # Renamed task_id for clarity
        task_id="fetch_and_load_raw_data",
        bash_command=(
            f"source {venv_activate_path} && "
            f"cd {project_directory_path} && "
            f"{python_interpreter_path} {fetch_script_path} "
            f"--symbol \"{{{{ params.stock_symbol }}}}\" "
            f"--outputsize \"{{{{ params.output_size }}}}\""
        ),
        env={
            "no_proxy": "*", "PYTHONUNBUFFERED": "1", "PYTHONFAULTHANDLER": "1"
        }
    )

    clean_and_transform_data_task = BashOperator(
        task_id="clean_and_transform_data",
        bash_command=(
            f"source {venv_activate_path} && "
            f"cd {project_directory_path} && "
            f"{python_interpreter_path} {transform_script_path}"
        ),
        env={
            "no_proxy": "*", "PYTHONUNBUFFERED": "1", "PYTHONFAULTHANDLER": "1"
        }
    )

    run_analysis_on_transformed_data_task = BashOperator( # Renamed task_id
        task_id="run_analysis_on_transformed_data",
        bash_command=(
            f"source {venv_activate_path} && "
            f"cd {project_directory_path} && "
            f"{python_interpreter_path} {analyze_script_path}"
        ),
        env={
            "no_proxy": "*", "PYTHONUNBUFFERED": "1", "PYTHONFAULTHANDLER": "1"
        }
    )

    # Define task dependencies
    fetch_and_load_raw_data_task >> clean_and_transform_data_task >> run_analysis_on_transformed_data_task
