# Stock Data Pipeline Project

This project is a data pipeline designed to fetch daily stock market data from an external API, store it in a PostgreSQL database, and perform basic analysis on the stored data.

## Project Overview

The primary goal of this project is to build an end-to-end data pipeline that automates the collection, storage, and analysis of stock market data.

**Current Functionality:**

1.  **Data Fetching:** Fetches daily time series data for a user-specified stock symbol from the Alpha Vantage API.
2.  **Data Storage:** Stores this data into a PostgreSQL database hosted on **AWS RDS**.
3.  **Data Analysis:** Runs a script to perform simple analysis (e.g., average closing price, highest/lowest prices) on the data stored in RDS.
4.  **Orchestration:** An **Apache Airflow DAG (`stock_data_pipeline`)** manages the fetching and analysis tasks, allowing for parameterized runs and retries.

## Technologies Used

- **Python 3:** Core programming language for scripting.
- **Pandas:** For data manipulation and analysis.
- **Requests:** For making HTTP requests to the Alpha Vantage API.
- **Psycopg2:** Python adapter for PostgreSQL, used for database interaction.
- **python-dotenv:** For managing environment variables (API keys, database credentials).
- **PostgreSQL:** Relational database for storing stock data.
- **Apache Airflow:** For workflow automation, scheduling, and monitoring.
- **Git & GitHub:** For version control.

## Project Structure

The project directory (`stocks_and_data/`) contains the following key files:

- `.env`: Stores environment variables (API key, **RDS credentials**). (This file is listed in `.gitignore` and should NOT be committed to GitHub).
- `.gitignore`: Specifies files and directories that Git should ignore.
- `dags/`: This subfolder within your project contains your Airflow DAG definition files.
  - `stock_data_pipeline_dag.py`: The main Airflow DAG that orchestrates the pipeline.
- `fetch_stock_data.py`: Script to fetch data from Alpha Vantage and insert into the database (now parameterized).
- `fetch_and_analyze_stockdata.py`: Script to read data from the database and perform basic analysis.
- `README.md`: This file, providing documentation for the project.

**Note on Airflow's System DAGs Folder:** For Airflow (especially `airflow standalone`) to recognize your DAGs, the `stock_data_pipeline_dag.py` file from your project's `dags` folder (or a symbolic link to it) must be present in Airflow's system `dags` folder (typically `~/airflow/dags/`).

## Setup and Installation

1.  **Clone the Repository (if applicable):**

    ```bash
    git clone [https://github.com/thegirlcoderr/stock-data-pipeline.git](https://github.com/thegirlcoderr/stock-data-pipeline.git)
    cd stock-data-pipeline
    ```

    _(Replace `stock-data-pipeline` with your actual repository name if different in the `cd` command, though the URL uses it.)_

2.  **Install Python 3:**
    Ensure you have Python 3 installed on your system.

3.  **Install Required Python Libraries:**
    Navigate to the project directory in your terminal and run:

    ```bash
    pip3 install pandas requests psycopg2-binary python-dotenv argparse
    ```

    _(Note: `psycopg2-binary` is a good choice for ease of installation. For production, `psycopg2` might be preferred with build prerequisites met.)_

4.  **Set up AWS RDS PostgreSQL Instance:**

    - Create a PostgreSQL instance on AWS RDS (refer to AWS documentation or previous guides if needed).
    - Ensure the instance is publicly accessible (for development/testing from your local machine) and its **Security Group** is configured to allow inbound connections on port `5432` from your current IP address.
    - Within your RDS instance, create a database named `stock_data_db`.
    - Connect to this `stock_data_db` on RDS (e.g., using pgAdmin) and create the `daily_stock_data` table using the following SQL schema:
      ```sql
      CREATE TABLE IF NOT EXISTS daily_stock_data (
          id SERIAL PRIMARY KEY,
          symbol VARCHAR(10) NOT NULL,
          trade_date DATE NOT NULL,
          open_price NUMERIC(10, 2),
          high_price NUMERIC(10, 2),
          low_price NUMERIC(10, 2),
          close_price NUMERIC(10, 2),
          volume BIGINT,
          fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE (symbol, trade_date)
      );
      ```

5.  **Create the Environment File (`.env`):**

    - In the root of the project directory (`stocks_and_data/`), create a file named `.env`.
    - Add your Alpha Vantage API key and local PostgreSQL database password (if any) to this file:
      ```env
      ALPHA_VANTAGE_API_KEY="YOUR_ALPHA_VANTAGE_API_KEY"
      DB_HOST="YOUR_RDS_INSTANCE_ENDPOINT"
      DB_NAME="stock_data_db"
      DB_USER="YOUR_RDS_MASTER_USERNAME"
      DB_PASSWORD_POSTGRES="YOUR_RDS_MASTER_PASSWORD"
      ```
      (If your local PostgreSQL doesn't require a password for the `postgres` user, you can leave `DB_PASSWORD_POSTGRES=""`).
    - **Important:** The `.env` file is listed in `.gitignore` and should NOT be committed to version control.

6.  **Set up Apache Airflow Locally:**
    _ Install Apache Airflow in its own Python virtual environment (e.g., `airflow_venv` typically created in your home directory `~`). This involves:
    _ Creating the venv: `python3 -m venv ~/airflow_venv`
    _ Activating it: `source ~/airflow_venv/bin/activate`
    _ Installing Airflow: `pip3 install "apache-airflow[postgres]" psycopg2-binary` (and potentially Rust/Cargo if dependencies like `libcst` require compilation on your system).
    _ Initializing the Airflow metadata database: `airflow db migrate`
    _ (User creation is handled by `airflow standalone`).
    _ **Symbolic Link for DAG:** To make your project's DAG visible to your local Airflow installation, create a symbolic link from Airflow's system `dags` folder to your project's DAG file.
    _ Ensure your DAG file is located at `/Users/linda/Desktop/stocks_and_data/dags/stock_data_pipeline_dag.py`.
    _ Remove or backup any existing file with the same name in `~/airflow/dags/`.
    _ In a terminal, run:
    `bash
ln -s /Users/linda/Desktop/stocks_and_data/dags/stock_data_pipeline_dag.py ~/airflow/dags/stock_data_pipeline_dag.py
`

## How to Run the Pipeline with Airflow

1.  **Start Apache Airflow:**

    - Open a terminal window.
    - Activate Airflow's virtual environment: `source ~/airflow_venv/bin/activate`
    - Start Airflow in standalone mode: `airflow standalone`
    - Keep this terminal window running. Note the admin password if it's displayed (or retrieve it from `/Users/linda/airflow/simple_auth_manager_passwords.json.generated`).

2.  **Access the Airflow Web UI:**

    - Open your web browser and go to `http://localhost:8080`.
    - Log in with username `admin` and the retrieved password.

3.  **Trigger the `stock_data_pipeline` DAG:**

    - On the "DAGs" page, find the DAG named `stock_data_pipeline`.
    - Ensure the toggle switch to its left is ON (unpaused).
    - Click the play button (▶️) next to the DAG name.
    - Select "Trigger DAG w/ config" (or similar).
    - A dialog will appear where you can:
      - Enter the desired **`stock_symbol`** (e.g., "AAPL", "MSFT"). Defaults to "IBM".
      - Select the **`output_size`** ("compact" or "full"). Defaults to "compact".
    - Click "Trigger".

4.  **Monitor the DAG Run:**
    - Click on the `stock_data_pipeline` DAG name to go to its detail page.
    - Use the "Grid" view to see the status of the DAG run and its tasks (`fetch_and_load_stock_data` and `run_stock_analysis`).
    - You can click on individual task instances to view their logs.

## Current Status

- Data fetching from Alpha Vantage API is parameterized.
- Data storage in **AWS RDS PostgreSQL** is implemented.
- Basic data analysis script is functional.
- The entire pipeline (fetch, store, analyze) is orchestrated by an **Apache Airflow DAG** with parameters and task retries.
- Secrets management using `.env` is in place for script execution.

## Next Steps (Roadmap Highlights)

- Implement more robust data cleansing and transformation steps (Phase 3).
- Define and calculate more Key Performance Indicators (KPIs).
- Develop a dashboard for data visualization (Phase 4).
- Explore different Airflow operators (e.g., `PythonOperator` for more direct Python function calls if `BashOperator` presents issues).
- Enhance Airflow error handling and notifications further.
- Consider deploying Apache Airflow to a cloud environment (e.g., AWS MWAA or EC2).
