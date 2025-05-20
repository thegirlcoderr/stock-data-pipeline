import requests
import pandas as pd
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import extras 
import argparse 

def fetch_daily_data_from_alpha_vantage(api_key, symbol, outputsize="compact"):
    if not api_key:
        print("Error: ALPHA_VANTAGE_API_KEY was not provided or loaded.")
        return pd.DataFrame()

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize={outputsize}&apikey={api_key}"
    
    print(f"Fetching data from Alpha Vantage for {symbol}...")
    response = requests.get(url)
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
        return pd.DataFrame()
    except Exception as err:
        print(f"Other error occurred: {err}")
        return pd.DataFrame()

    data = response.json()
    time_series = data.get("Time Series (Daily)", {})

    if not time_series:
        print(f"No 'Time Series (Daily)' data found for {symbol}.")
        if "Information" in data: print(f"API Information: {data['Information']}")
        elif "Error Message" in data: print(f"API Error Message: {data['Error Message']}")
        else: print(f"Full API response: {data}")
        return pd.DataFrame()

    stock_data_list = []
    for date_str, daily_values in time_series.items():
        stock_data_list.append({
            "symbol": symbol,
            "trade_date": pd.to_datetime(date_str).date(),
            "open_price": float(daily_values["1. open"]),
            "high_price": float(daily_values["2. high"]),
            "low_price": float(daily_values["3. low"]),
            "close_price": float(daily_values["4. close"]),
            "volume": int(daily_values["5. volume"])
        })
    
    if not stock_data_list:
        print(f"No data processed for {symbol}")
        return pd.DataFrame()
            
    df = pd.DataFrame(stock_data_list)
    return df.sort_values(by="trade_date")

def insert_stock_data_to_db(df_to_insert, db_host, db_name, db_user, db_password):
    if df_to_insert.empty:
        print("No data to insert into the database.")
        return

    if not all([db_host, db_name, db_user, db_password is not None]):
        print("Error: One or more database connection details are missing.")
        return

    conn = None
    cursor = None
    try:
        print(f"Attempting to connect to DB: Host={db_host}, DBName={db_name}, User={db_user}") 
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host)
        cursor = conn.cursor()
        
        cols = ['symbol', 'trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']
        tuples_to_insert = [tuple(x) for x in df_to_insert[cols].to_numpy()]

        insert_query = """
            INSERT INTO daily_stock_data (symbol, trade_date, open_price, high_price, low_price, close_price, volume)
            VALUES %s
            ON CONFLICT (symbol, trade_date) DO NOTHING; 
        """
        
        extras.execute_values(cursor, insert_query, tuples_to_insert)
        conn.commit()
        print(f"Successfully inserted/skipped {len(tuples_to_insert)} rows into daily_stock_data table on {db_host}.")

    except psycopg2.Error as db_err:
        print(f"Database error during insertion: {db_err}")
        if conn:
            conn.rollback() 
    except Exception as e:
        print(f"An unexpected error occurred during data insertion: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def run_pipeline(symbol_to_fetch, output_size="compact"):
    """
    Main pipeline logic: fetches stock data and stores it in the database.
    """
 
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(current_script_dir, '.env') 
    
    print(f"Attempting to load .env file from: {dotenv_path}")
    loaded = load_dotenv(dotenv_path=dotenv_path)
    if loaded:
        print(".env file loaded successfully by script.")
    else:
        print(f"Warning: .env file not found at {dotenv_path} or failed to load. Using system env vars if set.")

    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD_POSTGRES')

    print(f"--- Running stock data pipeline for symbol: {symbol_to_fetch} ---")
    
    stock_df_api = fetch_daily_data_from_alpha_vantage(api_key, symbol_to_fetch, outputsize=output_size) 

    if not stock_df_api.empty:
        print(f"\nSuccessfully fetched {len(stock_df_api)} days of data for {symbol_to_fetch} from API.")
        print("\nFirst 5 rows from API:")
        print(stock_df_api.head())
        
        print(f"\nAttempting to insert data for {symbol_to_fetch} into the database...")
        insert_stock_data_to_db(stock_df_api, db_host, db_name, db_user, db_password)
    else:
        print(f"Could not fetch data for {symbol_to_fetch} from API. Nothing to insert into DB.")

if __name__ == "__main__":
    # This block runs if the script is executed directly from the command line
    parser = argparse.ArgumentParser(description="Fetch and store stock data for a given symbol.")
    parser.add_argument(
        "--symbol", 
        type=str, 
        default="IBM",  # Default symbol if none is provided
        help="Stock symbol to fetch data for (e.g., AAPL, MSFT)."
    )
    parser.add_argument(
        "--outputsize",
        type=str,
        default="compact", # Default output size
        help="Output size for Alpha Vantage API ('compact' or 'full')."
    )
    args = parser.parse_args()

    run_pipeline(symbol_to_fetch=args.symbol, output_size=args.outputsize)
