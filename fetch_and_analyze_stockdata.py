# fetch_and_analyze_stockdata.py

import psycopg2
import pandas as pd
from dotenv import load_dotenv # Import dotenv
import os # Import os

# Load environment variables from .env file
load_dotenv()

# PostgreSQL connection details
DB_HOST = 'localhost' 
DB_NAME = 'stock_data_db'
DB_USER = 'postgres' 
# Load password from .env file
DB_PASSWORD = os.getenv('DB_PASSWORD_POSTGRES') 

def fetch_stock_data_from_db(): # Renamed function for clarity
    conn = None 
    if not DB_PASSWORD and DB_PASSWORD != "": # Allow empty string if no password is set locally
        print("Error: DB_PASSWORD_POSTGRES not found in environment variables.")
        print("Please ensure you have a .env file with DB_PASSWORD_POSTGRES.")
        return None
        
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
        # Query the correct table 'daily_stock_data' and specific columns
        query = """
            SELECT symbol, trade_date, open_price, high_price, low_price, close_price, volume 
            FROM daily_stock_data
        """
        df = pd.read_sql_query(query, conn)
        return df

    except psycopg2.Error as db_err:
        print(f"Database error occurred: {db_err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching data from database: {e}")
        return None
    finally:
        if conn:
            conn.close()

def analyze_stock_data(df):
    if df is not None and not df.empty:
        print("\n📊 Stock Data Analysis:")
        # Use correct column names with '_price' suffix
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
        
        if 'symbol' in df.columns:
            for symbol_name, group in df.groupby('symbol'):
                print(f"\n--- Analysis for {symbol_name} ---")
                if 'close_price' in group.columns:
                    print(f"  • Average Closing Price: {group['close_price'].mean():.2f}")
                # Add similar checks for high_price and low_price if desired for per-symbol analysis
                if 'high_price' in group.columns:
                    print(f"  • Highest Price: {group['high_price'].max():.2f}")
                if 'low_price' in group.columns:
                    print(f"  • Lowest Price: {group['low_price'].min():.2f}")
                print(f"  • Number of days of data: {len(group)}")
    else:
        print("No data to analyze or DataFrame is empty (Hint: Has data been inserted into 'daily_stock_data' yet?).")

def main():
    print(f"--- Running fetch_and_analyze_stockdata.py ---")
    df_from_db = fetch_stock_data_from_db()
    analyze_stock_data(df_from_db)

if __name__ == "__main__":
    main()