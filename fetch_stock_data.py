import requests
import pandas as pd
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import extras # For execute_values

# Load environment variables from .env file
load_dotenv() 

# Alpha Vantage API Key
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# PostgreSQL Connection Details (from .env file)
DB_HOST = 'localhost'
DB_NAME = 'stock_data_db'
DB_USER = 'postgres'
DB_PASSWORD = os.getenv('DB_PASSWORD_POSTGRES')

def fetch_daily_data_from_alpha_vantage(symbol, outputsize="compact"):
    if not API_KEY:
        print("Error: ALPHA_VANTAGE_API_KEY not found in environment variables.")
        return pd.DataFrame()

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize={outputsize}&apikey={API_KEY}"
    
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

def insert_stock_data_to_db(df_to_insert):
    if df_to_insert.empty:
        print("No data to insert into the database.")
        return

    if DB_PASSWORD is None: 
        print("Error: DB_PASSWORD_POSTGRES is not set in the .env file or .env not loaded. Cannot connect to DB.")
        print("If your local PostgreSQL requires no password, ensure DB_PASSWORD_POSTGRES=\"\" is in a loaded .env file.")
        return

    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
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
        print(f"Successfully inserted/skipped {len(tuples_to_insert)} rows into daily_stock_data table.")

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

if __name__ == "__main__":
    symbol_to_fetch = "IBM" 
    print(f"--- Running fetch_stock_data.py for {symbol_to_fetch} ---")
    
    stock_df_api = fetch_daily_data_from_alpha_vantage(symbol_to_fetch, outputsize="compact") 

    if not stock_df_api.empty:
        print(f"\nSuccessfully fetched {len(stock_df_api)} days of data for {symbol_to_fetch} from API.")
        print("\nFirst 5 rows from API:")
        print(stock_df_api.head())
        
        print(f"\nAttempting to insert data for {symbol_to_fetch} into the database...")
        insert_stock_data_to_db(stock_df_api)
    else:
        print(f"Could not fetch data for {symbol_to_fetch} from API. Nothing to insert into DB.")
