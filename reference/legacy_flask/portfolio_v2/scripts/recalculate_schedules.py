import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Lease, LeasePaymentScheduleVerify
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd

def add_months(start_date, months):
    return start_date + pd.DateOffset(months=months)

def recalculate():
    print("Starting schedule recalculation...")
    
    # Clear existing verify table
    LeasePaymentScheduleVerify.query.delete()
    db.session.commit()
    print("Cleared lease_payment_schedules_verify table.")
    
    leases = Lease.query.all()
    total_leases = len(leases)
    print(f"Processing {total_leases} leases...")
    
    new_schedules = []
    
    for lease in leases:
        if not lease.payment_start_date or not lease.total_terms:
            continue
            
        monthly_payment = 0.0
        residual_amount = 0.0
        
        if lease.financial_info:
            monthly_payment = lease.financial_info.monthly_payment or 0.0
            residual_amount = lease.financial_info.lessee_residual or 0.0
            
        # 1. Generate Rent Payments from Steps
        steps = sorted(lease.payment_steps, key=lambda x: x.start_date)
        last_payment_date = None
        
        for step in steps:
            if step.type == 'Rent' and step.frequency == 'Monthly':
                for i in range(step.number_of_payments):
                    payment_date = step.start_date + relativedelta(months=i)
                    p = LeasePaymentScheduleVerify(
                        lease_id=lease.id,
                        payment_date=payment_date,
                        amount=step.amount,
                        period_number=0,
                        type='Rent'
                    )
                    new_schedules.append(p)
                    last_payment_date = payment_date
        
        # 2. Add Residual Payment
        # Use info from financial_info (updated by import script)
        if lease.financial_info and lease.financial_info.lessee_residual and lease.financial_info.lessee_residual > 0:
            if last_payment_date:
                # Add 1 month to last rent payment (User requested: "last rent date + 1 month")
                residual_date = last_payment_date + relativedelta(months=1)
                
                res_p = LeasePaymentScheduleVerify(
                    lease_id=lease.id,
                    payment_date=residual_date,
                    amount=lease.financial_info.lessee_residual,
                    period_number=0,
                    type='Residual'
                )
                new_schedules.append(res_p)
            

        
        # Batch commit every 100 leases to prevent memory issues
        if len(new_schedules) > 1000:
            db.session.bulk_save_objects(new_schedules)
            db.session.commit()
            new_schedules = []
            
    # Commit remaining
    if new_schedules:
        db.session.bulk_save_objects(new_schedules)
        db.session.commit()
        
    print("Recalculation complete.")
    
    # Verification for L2659
    print("\n--- Verification for L2659 ---")
    l2659 = Lease.query.filter_by(lease_number='L2659').first()
    if l2659:
        schedules = LeasePaymentScheduleVerify.query.filter_by(lease_id=l2659.id).order_by(LeasePaymentScheduleVerify.period_number).all()
        for s in schedules:
            print(f"Period {s.period_number}: {s.payment_date} | {s.type} | ${s.amount:,.2f}")
    else:
        print("L2659 not found.")

if __name__ == "__main__":
    with app.app_context():
        # Ensure table exists
        db.create_all()
        recalculate()
