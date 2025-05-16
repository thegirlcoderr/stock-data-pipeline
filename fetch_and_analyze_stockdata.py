import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# PostgreSQL Connection Details (all from .env file)
DB_HOST = os.getenv('DB_HOST') 
DB_NAME = os.getenv('DB_NAME') 
DB_USER = os.getenv('DB_USER') 
DB_PASSWORD = os.getenv('DB_PASSWORD_POSTGRES') 

def fetch_stock_data_from_db(): # Function name can remain, but it now fetches transformed data
    conn = None
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD is not None]):
        print("Error: One or more database connection details (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD_POSTGRES) are not correctly set in the .env file.")
        if DB_PASSWORD is None:
             print("Specifically, DB_PASSWORD_POSTGRES seems to be missing from .env or .env was not loaded.")
        return None
        
    try:
        print(f"Attempting to connect to DB: Host={DB_HOST}, DBName={DB_NAME}, User={DB_USER}") 
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
        # Query the new 'transformed_stock_data' table
        query = """
            SELECT symbol, trade_date, open_price, high_price, low_price, close_price, volume, ma_20_day, daily_pct_change 
            FROM transformed_stock_data 
            ORDER BY symbol, trade_date; 
        """ # Added ORDER BY for consistency
        df = pd.read_sql_query(query, conn)
        print(f"Successfully fetched {len(df)} rows from transformed_stock_data on {DB_HOST}.")
        return df

    except psycopg2.Error as db_err:
        print(f"Database error occurred while connecting or querying transformed_stock_data: {db_err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching data from transformed_stock_data: {e}")
        return None
    finally:
        if conn:
            conn.close()

def analyze_stock_data(df):
    if df is not None and not df.empty:
        print("\n📊 Transformed Stock Data Analysis:") # Updated title
        if 'close_price' in df.columns:
            avg_close = df['close_price'].mean()
            print(f"• Average Closing Price: {avg_close:.2f}")
        else:
            print("• 'close_price' column not found for averaging.")

        if 'high_price' in df.columns:
            highest_price = df['high_price'].max()
            print(f"• Highest Price: {highest_price:.2f}")
        else:
            print("• 'high_price' column not found.")

        if 'low_price' in df.columns:
            lowest_price = df['low_price'].min()
            print(f"• Lowest Price: {lowest_price:.2f}")
        else:
            print("• 'low_price' column not found.")
        
        # You could add analysis for 'ma_20_day' or 'daily_pct_change' here
        if 'ma_20_day' in df.columns:
            print(f"• Latest MA_20_Day (overall last row): {df['ma_20_day'].iloc[-1] if not df['ma_20_day'].empty else 'N/A'}")

        if 'symbol' in df.columns:
            for symbol_name, group in df.groupby('symbol'):
                print(f"\n--- Analysis for {symbol_name} ---")
                if 'close_price' in group.columns:
                    print(f"  • Average Closing Price: {group['close_price'].mean():.2f}")
                if 'high_price' in group.columns:
                    print(f"  • Highest Price: {group['high_price'].max():.2f}")
                if 'low_price' in group.columns:
                    print(f"  • Lowest Price: {group['low_price'].min():.2f}")
                if 'ma_20_day' in group.columns and not group['ma_20_day'].empty:
                     print(f"  • Latest MA_20_Day: {group['ma_20_day'].iloc[-1]}") # Gets the last MA for that group
                print(f"  • Number of days of data: {len(group)}")
    else:
        print("No transformed data to analyze or DataFrame is empty.")

def main():
    print(f"--- Running fetch_and_analyze_stockdata.py (on transformed data) ---")
    df_from_db = fetch_stock_data_from_db()
    analyze_stock_data(df_from_db)

if __name__ == "__main__":
    main()
