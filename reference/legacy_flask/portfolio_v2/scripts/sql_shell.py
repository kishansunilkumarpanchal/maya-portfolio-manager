import sqlite3
import pandas as pd
import os

DB_PATH = 'portfolio.db'

def run_shell():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file '{DB_PATH}' not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    print(f"Connected to {DB_PATH}")
    print("Type your SQL query and press Enter. Type 'exit' or 'quit' to leave.")
    print("-" * 50)

    while True:
        query = input("SQL> ")
        if query.lower() in ('exit', 'quit'):
            break
        
        if not query.strip():
            continue

        try:
            # Use pandas for nice formatting of tables
            df = pd.read_sql_query(query, conn)
            print("\n")
            print(df.to_string())
            print("\n" + "-" * 50)
        except Exception as e:
            print(f"Error: {e}")
            print("-" * 50)

    conn.close()
    print("Connection closed.")

if __name__ == "__main__":
    run_shell()
