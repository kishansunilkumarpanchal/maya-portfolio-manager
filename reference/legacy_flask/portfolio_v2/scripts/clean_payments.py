from app_v2 import app, db
from models import LeasePaymentSchedule
from sqlalchemy import func

def clean():
    with app.app_context():
        # Find duplicates
        print("Finding duplicate payments...")
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
        
        print(f"Processing {len(duplicates)} duplicate groups...")
        
        deleted_count = 0
        for d in duplicates:
            lease_id = d[0]
            date = d[1]
            amount = d[2]
            type_ = d[3]
            
            # Get all payments in this group
            payments = LeasePaymentSchedule.query.filter_by(
                lease_id=lease_id,
                payment_date=date,
                amount=amount,
                type=type_
            ).all()
            
            # Keep the first one, delete the rest
            if len(payments) > 1:
                to_delete = payments[1:]
                for p in to_delete:
                    db.session.delete(p)
                deleted_count += len(to_delete)
                
            if deleted_count % 10000 == 0:
                print(f"Deleted {deleted_count} so far...")
                db.session.commit() # Commit in chunks
                
        db.session.commit()
        print(f"Total deleted payments: {deleted_count}")

if __name__ == "__main__":
    clean()
