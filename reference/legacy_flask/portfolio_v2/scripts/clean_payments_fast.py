import sys
import os
# Add parent dir to path to import app_v2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_v2 import app, db
from sqlalchemy import text

from models import LeasePaymentSchedule

def clean_sql():
    with app.app_context():
        count_before = LeasePaymentSchedule.query.count()
        print(f"Count before: {count_before}")
        
        # SQL to delete duplicates, keeping the one with the lowest ID
        sql = text("""
            DELETE FROM lease_payment_schedules
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM lease_payment_schedules
                GROUP BY lease_id, payment_date, amount, type
            )
        """)
        
        print("Executing fast SQL cleanup...")
        result = db.session.execute(sql)
        db.session.commit()
        
        count_after = LeasePaymentSchedule.query.count()
        print(f"Count after: {count_after}")
        print(f"Delta: {count_before - count_after}")

if __name__ == "__main__":
    clean_sql()
