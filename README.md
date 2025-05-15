# stock-data-pipeline

This project implements an end-to-end data pipeline to fetch daily stock market data from an external API, store it in a PostgreSQL database on AWS RDS, orchestrate the workflow with Apache Airflow, and visualize key metrics using Grafana.

A data pipeline project that fetches financial data from the Alpha Vantage API, transforms it using Python scripts, stores it in a PostgreSQL database (hosted on AWS RDS), and visualizes the data through Grafana. Apache Airflow orchestrates the entire workflow.

## Architecture Diagram

```mermaid
graph TD
    A[Alpha Vantage API] --> B(Python Scripts: Fetch & Transform);
    C(Apache Airflow) -- Orchestrates --> B;
    B -- Writes Data --> D[PostgreSQL DB on AWS RDS];
    D -- Queried by --> E[Grafana Dashboard];

    subgraph "Data Pipeline"
        direction LR
        A
        B
        C
        D
    end

    subgraph "Visualization"
        direction LR
        E
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px,color:#333
    style B fill:#bbf,stroke:#333,stroke-width:2px,color:#333
    style C fill:#f8d568,stroke:#333,stroke-width:2px,color:#333
    style D fill:#9f9,stroke:#333,stroke-width:2px,color:#333
    style E fill:#ffb366,stroke:#333,stroke-width:2px,color:#333
```

## Project Overview

The primary goal of this project is to build an automated system for collecting, processing, storing, and analyzing stock market data for multiple symbols. This allows for tracking price trends, moving averages, and other potential Key Performance Indicators (KPIs).

### Key Features:

1. **Data Fetching:** Fetches daily time series data (closing price, open, high, low, volume) for user-specified stock symbols (e.g., IBM, AAPL, MSFT) from the Alpha Vantage API.
2. **Data Transformation:** Calculates key metrics such as the 20-day Moving Average (MA) and daily percentage change for fetched stock data.
3. **Data Storage:** Stores both raw and transformed stock data in a PostgreSQL database hosted on **AWS RDS**.
4. **Orchestration:** An **Apache Airflow DAG (`stock_data_pipeline`)** manages the data fetching, transformation, and loading tasks, allowing for parameterized runs (by stock symbol) and configured retries.
5. **Data Visualization:** A **Grafana dashboard** connects to the AWS RDS database to display interactive charts, currently showing closing prices and 20-day moving averages for selected stocks.

## Technologies Used

- **Python 3**
- **Pandas**
- **Requests**
- **Psycopg2**
- **python-dotenv**
- **PostgreSQL**
- **AWS RDS**
- **Apache Airflow**
- **Grafana**
- **Git & GitHub**

## Project Structure

```
stock-data-pipeline/
├── .env
├── .gitignore
├── dags/
│   └── stock_data_pipeline_dag.py
├── Workspace_stock_data.py
├── clean_and_transform_data.py
├── Workspace_and_analyze_stockdata.py
├── grafana_dashboards/
│   └── dashboard_export.json (optional)
├── images/
│   └── screenshot.png
└── README.md
```

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/stock-data-pipeline.git
cd stock-data-pipeline
```

### 2. Create Virtual Environment and Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas requests psycopg2-binary python-dotenv argparse
```

### 3. AWS RDS PostgreSQL Setup

- Create an RDS PostgreSQL instance.
- Ensure it's publicly accessible and port 5432 is open.
- Create a database (e.g., `stock_data_db`).

Example SQL for table setup:

```sql
-- Raw data table
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

-- Transformed data table
CREATE TABLE IF NOT EXISTS transformed_stock_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price NUMERIC(10,2),
    high_price NUMERIC(10,2),
    low_price NUMERIC(10,2),
    close_price NUMERIC(10,2),
    volume BIGINT,
    ma_20_day NUMERIC(10,2),
    daily_pct_change NUMERIC(10,4),
    transformed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, trade_date)
);
```

### 4. Create `.env` File

```env
ALPHA_VANTAGE_API_KEY="your_api_key"
DB_HOST="your-db-host.rds.amazonaws.com"
DB_NAME="stock_data_db"
DB_USER="your_db_username"
DB_PASSWORD_POSTGRES="your_db_password"
```

Ensure `.env` is in your `.gitignore`.

### 5. Set Up Apache Airflow

- Install Airflow in a separate virtual environment.
- Run:

```bash
pip install apache-airflow
airflow db migrate
```

- Put your DAG file in `~/airflow/dags` or link it:

```bash
ln -s /path/to/stock-data-pipeline/dags/stock_data_pipeline_dag.py ~/airflow/dags/
```

### 6. Set Up Grafana

- Install Grafana (e.g., via Homebrew or official package).
- Start Grafana: `brew services start grafana`
- Visit: [http://localhost:3000](http://localhost:3000)
- Add your PostgreSQL RDS as a data source.

## Running the Pipeline

### 1. Start Airflow

```bash
source ~/airflow_venv/bin/activate
airflow standalone
```

- Open Airflow UI at `http://localhost:8080`
- Unpause and trigger the `stock_data_pipeline` DAG.

### 2. Open Grafana Dashboard

- Go to `http://localhost:3000`
- View your dashboard (e.g., "Stock Price Dashboard")

## Dashboard Preview

![Grafana Dashboard](images/Screenshot.png)

(Optional: Import `grafana_dashboards/dashboard_export.json` in Grafana to reproduce this layout.)

## Current Status

✅ End-to-end pipeline: fetch → transform → store
✅ Orchestration with Apache Airflow
✅ Visualization with Grafana
✅ Secrets managed with `.env`

## Next Steps

- Add more KPIs (e.g., % change, volume trends)
- Data validation & anomaly detection
- Notifications on DAG failure
- Modularize ETL scripts
- Deploy to the cloud (e.g., EC2, ECS, or Lambda + Step Functions)

```

---

Let me know if you'd like this as a downloadable file or want to customize the visuals or sections further.
```
