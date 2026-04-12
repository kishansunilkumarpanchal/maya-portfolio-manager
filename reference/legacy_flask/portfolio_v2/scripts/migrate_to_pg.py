import sys
import os
import sqlite3
import pandas as pd
from sqlalchemy import text

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db

def migrate():
    # Path to SQLite DB
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sqlite_path = os.path.join(base_dir, 'instance', 'portfolio.db')
    
    if not os.path.exists(sqlite_path):
        print(f"Error: SQLite database not found at {sqlite_path}")
        return

    print(f"Reading from SQLite: {sqlite_path}")
    
    # Tables in dependency order (Parents first)
    tables = [
        'provinces',
        'asset_groups',
        'tax_rates',
        'customers',
        'leases',
        'financial_info',
        'lease_payment_schedules',
        'payment_steps',
        'assets',
        'inactive_asset_logs',
        # 'lease_payment_schedules_verify' # Optional, usually temporary
    ]

    sqlite_conn = sqlite3.connect(sqlite_path)

    with app.app_context():
        # 1. Reset Database Scheme (Drop & Create)
        print("Dropping existing tables in Postgres...")
        db.drop_all()
        
        print("Creating tables in PostgreSQL...")
        db.create_all()
        
        # 2. Migrate Data

        # 3. Migrate Data
        for table in tables:
            print(f"Migrating {table}...")
            try:
                # Read from SQLite
                df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
                
                if df.empty:
                    print(f"  No data in {table}.")
                    continue
                
                # Write to Postgres
                # 'append' works, but we must ensure column names match exactly.
                # SQLite usually stores booleans as 0/1, Postgres needs True/False (drivers usually handle this)
                # Dates might be strings in SQLite, pandas converts to datetime, psycopg2 handles that.
                
                df.to_sql(table, db.engine, if_exists='append', index=False)
                print(f"  Transferred {len(df)} rows.")
                
            except Exception as e:
                print(f"Error migrating {table}: {e}")
                # Stop immediately if a parent table fails
                raise e
                
        # 4. Reset Sequences
        # Postgres SERIAL columns need their sequences updated to max(id)
        print("Resetting sequences...")
        tables_with_id = ['asset_groups', 'customers', 'leases', 'lease_payment_schedules', 'payment_steps', 'assets', 'inactive_asset_logs']
        
        for table in tables_with_id:
            try:
                # Check if table has an 'id' column first? Assuming yes based on list
                sql = text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 0) + 1, false) FROM {table};")
                db.session.execute(sql)
                db.session.commit()
                print(f"  Reset sequence for {table}")
            except Exception as e:
                print(f"  Could not reset sequence for {table} (Might include non-serial PK): {e}")
                db.session.rollback()

    sqlite_conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
