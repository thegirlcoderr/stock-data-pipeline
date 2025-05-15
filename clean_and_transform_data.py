import pandas as pd
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
import os

def load_env_vars():
    """Loads environment variables from .env file and returns them."""
    # Construct the path to the .env file relative to this script's location
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(current_script_dir, '.env')
    
    print(f"Attempting to load .env file from: {dotenv_path}")
    loaded = load_dotenv(dotenv_path=dotenv_path)
    if loaded:
        print(".env file loaded successfully by clean_and_transform_data.py.")
    else:
        print(f"Warning: .env file not found at {dotenv_path} or failed to load. Using system env vars if set.")

    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD_POSTGRES')
    
    if not all([db_host, db_name, db_user, db_password is not None]):
        print("Error: One or more database connection details are missing from .env.")
        return None
    return db_host, db_name, db_user, db_password

def fetch_raw_data(db_host, db_name, db_user, db_password, table_name="daily_stock_data"):
    """Fetches raw stock data from the specified table."""
    conn = None
    try:
        print(f"Connecting to database to fetch raw data from {table_name}...")
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host)
        query = f"SELECT symbol, trade_date, open_price, high_price, low_price, close_price, volume FROM {table_name} ORDER BY symbol, trade_date;"
        df = pd.read_sql_query(query, conn)
        print(f"Successfully fetched {len(df)} rows from {table_name}.")
        return df
    except psycopg2.Error as db_err:
        print(f"Database error while fetching raw data: {db_err}")
        return pd.DataFrame()
    except Exception as e:
        print(f"An unexpected error occurred while fetching raw data: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def clean_and_transform_data(df_raw):
    """Performs data cleaning and transformation."""
    if df_raw.empty:
        print("Raw data is empty, skipping cleaning and transformation.")
        return pd.DataFrame()

    df = df_raw.copy()

    # Ensure trade_date is datetime
    df['trade_date'] = pd.to_datetime(df['trade_date'])

    # Sort by symbol and date to ensure correct moving average and pct_change calculation
    df = df.sort_values(by=['symbol', 'trade_date'])

    # --- Data Cleansing Example: Missing Values ---
    # Check for missing values in critical price columns
    critical_cols = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
    missing_data_report = df[critical_cols].isnull().sum()
    print("\nMissing data report (before handling):")
    print(missing_data_report[missing_data_report > 0])

    # For this example, we'll drop rows where 'close_price' is NaN
    # In a real scenario, you might have more sophisticated imputation or logging.
    initial_rows = len(df)
    df.dropna(subset=['close_price'], inplace=True)
    rows_dropped = initial_rows - len(df)
    if rows_dropped > 0:
        print(f"Dropped {rows_dropped} rows due to missing 'close_price'.")

    # --- Data Transformation Example: New Features ---
    # Calculate 20-day Moving Average for close_price, grouped by symbol
    df['ma_20_day'] = df.groupby('symbol')['close_price'].transform(lambda x: x.rolling(window=20, min_periods=1).mean())
    
    # Calculate Daily Percentage Change in close_price, grouped by symbol
    # (close - previous_close) / previous_close * 100
    df['daily_pct_change'] = df.groupby('symbol')['close_price'].transform(lambda x: x.pct_change() * 100)
    
    # Fill NaN for the first pct_change value in each group (as there's no previous day)
    df['daily_pct_change'] = df['daily_pct_change'].fillna(0) 

    print("\nData after transformations (sample):")
    print(df.head())
    print(df.tail())
    print("\nColumns in transformed DataFrame:", df.columns.tolist())
    return df

def create_transformed_table_if_not_exists(db_host, db_name, db_user, db_password, table_name="transformed_stock_data"):
    """Creates the table for transformed data if it doesn't already exist."""
    conn = None
    cursor = None
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(10) NOT NULL,
        trade_date DATE NOT NULL,
        open_price NUMERIC(10, 2),
        high_price NUMERIC(10, 2),
        low_price NUMERIC(10, 2),
        close_price NUMERIC(10, 2),
        volume BIGINT,
        ma_20_day NUMERIC(10, 2),       -- New column for 20-day Moving Average
        daily_pct_change NUMERIC(10, 4), -- New column for Daily Percent Change
        transformed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (symbol, trade_date)     -- To prevent duplicate entries
    );
    """
    try:
        print(f"Attempting to create table '{table_name}' if it doesn't exist...")
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host)
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()
        print(f"Table '{table_name}' ensured to exist.")
    except psycopg2.Error as db_err:
        print(f"Database error during table creation for '{table_name}': {db_err}")
        if conn: conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred during table creation for '{table_name}': {e}")
        if conn: conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def store_transformed_data(df_transformed, db_host, db_name, db_user, db_password, table_name="transformed_stock_data"):
    """Stores the transformed DataFrame into the specified table."""
    if df_transformed.empty:
        print("Transformed data is empty, nothing to store.")
        return

    conn = None
    cursor = None
    try:
        print(f"Connecting to database to store transformed data into {table_name}...")
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host)
        cursor = conn.cursor()

        # Define columns for insertion, matching the new table structure
        cols = ['symbol', 'trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'ma_20_day', 'daily_pct_change']
        
        # Ensure DataFrame has all necessary columns and in the correct order for insertion
        # Handle cases where some columns might be missing after transformation (though unlikely with current logic)
        df_for_insert = df_transformed[cols].copy()
        
        tuples_to_insert = [tuple(x) for x in df_for_insert.to_numpy()]

        # Using ON CONFLICT to update existing rows if data for the same symbol and date is reprocessed
        insert_query = f"""
            INSERT INTO {table_name} (symbol, trade_date, open_price, high_price, low_price, close_price, volume, ma_20_day, daily_pct_change)
            VALUES %s
            ON CONFLICT (symbol, trade_date) DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                ma_20_day = EXCLUDED.ma_20_day,
                daily_pct_change = EXCLUDED.daily_pct_change,
                transformed_at = CURRENT_TIMESTAMP;
        """
        extras.execute_values(cursor, insert_query, tuples_to_insert)
        conn.commit()
        print(f"Successfully inserted/updated {len(tuples_to_insert)} rows into {table_name} on {db_host}.")

    except psycopg2.Error as db_err:
        print(f"Database error while storing transformed data: {db_err}")
        if conn: conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred while storing transformed data: {e}")
        if conn: conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == "__main__":
    print("--- Starting Data Cleaning and Transformation Process ---")
    
    db_credentials = load_env_vars()
    if db_credentials:
        db_host, db_name, db_user, db_password = db_credentials
        
        # 1. Ensure the target table for transformed data exists
        create_transformed_table_if_not_exists(db_host, db_name, db_user, db_password)
        
        # 2. Fetch raw data
        df_raw_data = fetch_raw_data(db_host, db_name, db_user, db_password)
        
        if not df_raw_data.empty:
            # 3. Clean and transform the data
            df_transformed_data = clean_and_transform_data(df_raw_data)
            
            if not df_transformed_data.empty:
                # 4. Store the transformed data
                store_transformed_data(df_transformed_data, db_host, db_name, db_user, db_password)
            else:
                print("No transformed data to store.")
        else:
            print("No raw data fetched to process.")
    else:
        print("Could not load database credentials. Exiting.")
        
    print("--- Data Cleaning and Transformation Process Finished ---")
