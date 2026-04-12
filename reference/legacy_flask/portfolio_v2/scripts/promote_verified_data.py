import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import LeasePaymentSchedule, LeasePaymentScheduleVerify

def promote():
    with app.app_context():
        # Verify we have data
        count = LeasePaymentScheduleVerify.query.count()
        if count == 0:
            print("Error: Verification table is empty! Run recalculation first.")
            return

        print(f"Promoting {count} records from Verify to Live table...")

        # Clear Live Table
        try:
            num_deleted = LeasePaymentSchedule.query.delete()
            db.session.commit()
            print(f"Cleared {num_deleted} records from live table.")
        except Exception as e:
            print(f"Error clearing table: {e}")
            db.session.rollback()
            return

        # Copy data in batches to avoid memory issues
        offset = 0
        batch_size = 5000
        total_copied = 0
        
        while True:
            batch = LeasePaymentScheduleVerify.query.offset(offset).limit(batch_size).all()
            if not batch:
                break
            
            new_records = []
            for v in batch:
                new_records.append(LeasePaymentSchedule(
                    lease_id=v.lease_id,
                    payment_date=v.payment_date,
                    amount=v.amount,
                    period_number=v.period_number,
                    type=v.type
                ))
            
            db.session.bulk_save_objects(new_records)
            db.session.commit()
            
            total_copied += len(new_records)
            print(f"Copied {total_copied} records...")
            offset += batch_size
            
        print("Promotion complete.")

if __name__ == "__main__":
    promote()
