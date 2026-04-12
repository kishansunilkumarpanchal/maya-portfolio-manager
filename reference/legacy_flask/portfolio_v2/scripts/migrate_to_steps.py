import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_v2 import app, db
from models import LeasePaymentSchedule, PaymentStep, Lease
from sqlalchemy import func
import datetime
from dateutil.relativedelta import relativedelta

def migrate():
    with app.app_context():
        # Create table if not exists
        db.create_all()
        
        # Clear existing steps to avoid duplicates during re-runs
        db.session.query(PaymentStep).delete()
        
        print("Migrating Payment Schedules to Steps...")
        
        leases = Lease.query.all()
        total_steps = 0
        
        for lease in leases:
            # Get payments sorted by date
            payments = LeasePaymentSchedule.query.filter_by(lease_id=lease.id).order_by(LeasePaymentSchedule.payment_date).all()
            
            if not payments:
                continue
                
            current_step = None
            steps = []
            
            # Deduplicate and Clean List
            cleaned_payments = []
            prev_accepted_date = None
            
            for p in payments:
                # 1. Skip Residuals (Handled by logic)
                if p.type in ['Residual', 'Purchase Option', 'Lessee Residual']:
                    continue
                    
                # 2. Skip Duplicates (Close dates)
                # If within 25 days of previous accepted payment, skip
                if prev_accepted_date and (p.payment_date - prev_accepted_date).days < 25:
                    continue
                    
                cleaned_payments.append(p)
                prev_accepted_date = p.payment_date
            
            for p in cleaned_payments:
                # Start a new step if:
                # 1. No current step
                # 2. Amount different
                # 3. Type different
                # 4. Gap in dates (not monthly)
                
                is_gap = False
                if current_step:
                    expected_next_date = current_step['start_date'] + relativedelta(months=current_step['count'])
                    # Allow small wiggle room? for now exact match or close
                    diff_days = abs((p.payment_date - expected_next_date).days)
                    if diff_days > 5: # Allow 5 day variance for "Monthly" alignment
                        is_gap = True
                
                if (current_step is None or 
                    abs(p.amount - current_step['amount']) > 0.01 or 
                    p.type != current_step['type'] or 
                    is_gap):
                    
                    # Save old step
                    if current_step:
                        steps.append(current_step)
                    
                    # Start new
                    current_step = {
                        'start_date': p.payment_date,
                        'amount': p.amount,
                        'type': p.type,
                        'count': 1
                    }
                else:
                    # Continue step
                    current_step['count'] += 1
            
            # Save last step
            if current_step:
                steps.append(current_step)
                
            # Commit steps to DB
            for s in steps:
                step_obj = PaymentStep(
                    lease_id=lease.id,
                    start_date=s['start_date'],
                    amount=s['amount'],
                    frequency='Monthly',
                    number_of_payments=s['count'],
                    type=s['type']
                )
                db.session.add(step_obj)
                total_steps += 1
                
        db.session.commit()
        print(f"Migration complete. Created {total_steps} PaymentSteps.")

if __name__ == "__main__":
    migrate()
