import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_v2 import app, db
from models import LeasePaymentSchedule
from sqlalchemy import func

def check():
    with app.app_context():
        total = LeasePaymentSchedule.query.count()
        print(f"Total Payments: {total}")
        
        # Check for duplicates based on Lease ID + Date + Amount + Type
        duplicates = db.session.query(
            LeasePaymentSchedule.lease_id,
            LeasePaymentSchedule.payment_date,
            LeasePaymentSchedule.amount,
            LeasePaymentSchedule.type,
            func.count(LeasePaymentSchedule.id)
        ).group_by(
            LeasePaymentSchedule.lease_id,
            LeasePaymentSchedule.payment_date,
            LeasePaymentSchedule.amount,
            LeasePaymentSchedule.type
        ).having(func.count(LeasePaymentSchedule.id) > 1).all()
        
        print(f"Found {len(duplicates)} groups of duplicate payments.")
        
        dup_count = 0
        for d in duplicates:
            # print(f"  Lease: {d[0]}, Date: {d[1]} -> Count: {d[4]}")
            dup_count += (d[4] - 1)
            
        print(f"Estimated removable duplicates: {dup_count}")

if __name__ == "__main__":
    check()
