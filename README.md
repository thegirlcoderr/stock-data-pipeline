# Stock Data Pipeline Project

This project is a data pipeline designed to fetch daily stock market data from an external API, store it in a PostgreSQL database, and perform basic analysis on the stored data.

## Project Overview

The primary goal of this project is to build an end-to-end data pipeline that automates the collection, storage, and analysis of stock market data. Currently, the project focuses on:

1.  Fetching daily time series data for specified stock symbols from the Alpha Vantage API.
2.  Storing this data into a local PostgreSQL database.
3.  Reading the data from the database and performing simple analysis (e.g., average closing price, highest/lowest prices).

Future enhancements will include deploying the pipeline to the cloud (AWS RDS, Airflow on EC2), implementing more sophisticated data cleansing and transformation, and creating dashboards for visualization.

## Technologies Used

- **Python 3:** Core programming language for scripting.
- **Pandas:** For data manipulation and analysis.
- **Requests:** For making HTTP requests to the Alpha Vantage API.
- **Psycopg2:** Python adapter for PostgreSQL, used for database interaction.
- **python-dotenv:** For managing environment variables (API keys, database credentials).
- **PostgreSQL:** Relational database for storing stock data.
- **Git & GitHub:** For version control.

## Project Structure

stocks_and_data/
├── .env # Stores environment variables (API key, DB password) - DO NOT COMMIT
├── .gitignore # Specifies intentionally untracked files that Git should ignore
├── fetch_stock_data.py # Script to fetch data from Alpha Vantage and insert into DB
├── fetch_and_analyze_stockdata.py # Script to read data from DB and perform analysis
└── README.md # This file

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
    pip3 install pandas requests psycopg2-binary python-dotenv
    ```

    _(Note: `psycopg2-binary` is a good choice for ease of installation. For production, `psycopg2` might be preferred with build prerequisites met.)_

4.  **Set up PostgreSQL:**

    Install PostgreSQL locally (e.g., using Postgres.app for macOS, or the official installer for other OS).
    - Ensure the PostgreSQL server is running.
    - Create a database named `stock_data_db`.
      ```sql
      -- Example using psql:
      CREATE DATABASE stock_data_db;
      ```
    - Connect to the `stock_data_db` database and create the `daily_stock_data` table using the following SQL schema:
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
      DB_PASSWORD_POSTGRES="YOUR_LOCAL_DB_PASSWORD"
      ```
    - **Important:** The `.env` file is listed in `.gitignore` and should NOT be committed to version control.

## How to Run the Scripts

1.  **Fetch Data and Store in Database:**
    This script will fetch data for a predefined symbol (currently "IBM") from Alpha Vantage and insert it into your local `daily_stock_data` table.

    ```bash
    python3 fetch_stock_data.py
    ```

    You can change the `symbol_to_fetch` variable inside `fetch_stock_data.py` to get data for different stocks.

2.  **Analyze Data from Database:**
    This script will read the data previously stored in the `daily_stock_data` table and print a basic analysis.
    ```bash
    python3 fetch_and_analyze_stockdata.py
    ```

## Current Status

- Local data fetching from Alpha Vantage is implemented.
- Local storage of fetched data into PostgreSQL is working.
- Basic local analysis of stored data is implemented.
- Secrets management using `.env` is in place.

## Next Steps (Roadmap Highlights)

- Set up AWS RDS for cloud-based PostgreSQL storage.
- Integrate Apache Airflow for pipeline orchestration and scheduling.
- Implement more robust data cleansing and transformation steps.
- Define and calculate more Key Performance Indicators (KPIs).
- Develop a dashboard for data visualization (e.g., using Tableau, Power BI, or Python libraries like Dash/Streamlit).
