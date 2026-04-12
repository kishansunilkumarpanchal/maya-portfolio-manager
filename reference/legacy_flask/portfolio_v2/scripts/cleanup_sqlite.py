import sqlite3
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sqlite_path = os.path.join(base_dir, 'instance', 'portfolio.db')

conn = sqlite3.connect(sqlite_path)
c = conn.cursor()

# Get count before
c.execute("SELECT count(*) FROM customers WHERE customer_code IN ('T001', 'T002', 'T003')")
print(f"Test customers before: {c.fetchone()[0]}")

# Delete
c.execute("DELETE FROM customers WHERE customer_code IN ('T001', 'T002', 'T003')")
conn.commit()

# Get count after
c.execute("SELECT count(*) FROM customers WHERE customer_code IN ('T001', 'T002', 'T003')")
print(f"Test customers after: {c.fetchone()[0]}")

conn.close()
