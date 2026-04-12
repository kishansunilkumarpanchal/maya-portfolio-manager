from app import app, db
from models import Lease, LeasePaymentSchedule, LeasePaymentScheduleVerify, FinancialInfo
from datetime import date
import pandas as pd

def recalculate_uneven():
    print("Starting Uneven Schedule Recalculation (Date Shifting)...")
    
    # 1. Clear Verify Table
    LeasePaymentScheduleVerify.query.delete()
    db.session.commit()
    print("Cleared verification table.")
    
    leases = Lease.query.all()
    count = 0
    
    new_records = []
    
    for lease in leases:
        if not lease.payment_start_date:
            continue
            
        # Get existing payments sorted by period or date (original import)
        # We rely on existing data having correct *order* and *amounts*
        existing_payments = LeasePaymentSchedule.query.filter_by(lease_id=lease.id).order_by(LeasePaymentSchedule.payment_date).all()
        
        if not existing_payments:
            continue
            
        start_date = pd.to_datetime(lease.payment_start_date)
        
        for i, payment in enumerate(existing_payments):
            # Calculate new date: Start Date + i months
            new_date = start_date + pd.DateOffset(months=i)
            
            # Determine type
            # If it's the last payment AND matches residual amount, mark as Residual
            p_type = 'Rent'
            if i == len(existing_payments) - 1:
                # Check if it looks like a residual? 
                # Or just trust the loop. 
                # User said: "last payment would always be residual payment after all the payments are done"
                # BUT wait, the existing list might mix rent and residual.
                # If we assume the existing list is the full set of cashflows.
                
                # Logic Refinement:
                # If the list length > lease.total_terms, the extras are likely residuals.
                # If list length == lease.total_terms, maybe no residual in list?
                
                # User's heuristic: "last payment would be residual payment"
                # We will mark the very last record as Residual.
                p_type = 'Residual' 
            else:
                p_type = 'Rent'

            verify_record = LeasePaymentScheduleVerify(
                lease_id=lease.id,
                payment_date=new_date.date(),
                amount=payment.amount,  # <--- PRESERVE ORIGINAL AMOUNT
                period_number=i + 1,
                type=p_type
            )
            new_records.append(verify_record)
            
        if len(new_records) > 1000:
            db.session.bulk_save_objects(new_records)
            db.session.commit()
            new_records = []
            
        count += 1
        
    if new_records:
        db.session.bulk_save_objects(new_records)
        db.session.commit()
        
    print(f"Processed {count} leases.")
    
    # Verification for L2659
    print("\n--- Verification for L2659 ---")
    l2659 = Lease.query.filter_by(lease_number='L2659').first()
    if l2659:
        print(f"Start Date: {l2659.payment_start_date}")
        schedules = LeasePaymentScheduleVerify.query.filter_by(lease_id=l2659.id).order_by(LeasePaymentScheduleVerify.period_number).all()
        for s in schedules:
            print(f"Period {s.period_number}: {s.payment_date} | {s.type} | ${s.amount:,.2f}")

if __name__ == "__main__":
    with app.app_context():
        recalculate_uneven()
