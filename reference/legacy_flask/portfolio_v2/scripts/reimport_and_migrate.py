import sys
import os
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import datetime

# Setup path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app_v2 import app, db
from models import Lease, LeasePaymentSchedule, PaymentStep

def parse_date(date_str):
    if pd.isna(date_str) or date_str == '':
        return None
    try:
        return pd.to_datetime(date_str).date()
    except:
        return None

def reimport_and_migrate():
    with app.app_context():
        print("Starting Re-import and Migration...")
        
        # 1. Clean Slate
        print("Clearing tables...")
        LeasePaymentSchedule.query.delete()
        PaymentStep.query.delete()
        db.session.commit()
        
        # 2. Import from CSV
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'import_payments.csv')
        if not os.path.exists(csv_path):
            print("Error: import_payments.csv not found!")
            return

        print(f"Reading {csv_path}...")
        df_pay = pd.read_csv(csv_path)
        df_pay.columns = [c.strip() for c in df_pay.columns]
        
        print("Importing Payments...")
        leases = {l.lease_number: l.id for l in Lease.query.all()}
        
        payment_objects = []
        count_imported = 0
        
        # Pre-process for deduplication per Lease
        # Convert Date Column to Datetime objects for correct sorting
        df_pay['Payment Date Obj'] = pd.to_datetime(df_pay['Payment Date'], errors='coerce')
        
        # Group by Lease Number
        grouped = df_pay.groupby('Lease Number')
        
        for lease_num, group in grouped:
            lease_id = leases.get(str(lease_num).strip())
            if not lease_id:
                continue
                
            # Sort by Date Object
            group = group.sort_values('Payment Date Obj')
            
            prev_date = None
            prev_amount = None
            
            for _, row in group.iterrows():
                p_date = row['Payment Date Obj']
                if pd.isna(p_date): continue
                p_date = p_date.date() # Convert timestamp to date
                
                amount = float(row.get('Amount') or 0)
                p_type = row.get('Type')
                
                # Deduplication Rule:
                # If same Amount and within 20 days of previous, skip (it's likely a duplicate/offset)
                if prev_date and (p_date - prev_date).days < 20 and abs(amount - prev_amount) < 0.01:
                    continue
                    
                p = LeasePaymentSchedule(
                    lease_id=lease_id,
                    payment_date=p_date,
                    amount=amount,
                    period_number=row.get('Period Number'),
                    type=p_type
                )
                payment_objects.append(p)
                
                prev_date = p_date
                prev_amount = amount
                count_imported += 1
                
        # Bulk Insert
        if payment_objects:
            db.session.bulk_save_objects(payment_objects)
            db.session.commit()
        print(f"Imported {count_imported} unique payments.")
        
        # 3. Migrate to Steps
        print("Migrating to Steps...")
        all_leases = Lease.query.all()
        step_objects = []
        
        for lease in all_leases:
            payments = LeasePaymentSchedule.query.filter_by(lease_id=lease.id).order_by(LeasePaymentSchedule.payment_date).all()
            if not payments: continue
            
            # Filter Residuals for Steps (Handled by logic)
            clean_payments = [p for p in payments if p.type not in ['Residual', 'Purchase Option', 'Lessee Residual']]
            
            if not clean_payments: continue
            
            current_step = None
            steps = []
            
            for p in clean_payments:
                is_gap = False
                if current_step:
                    expected_next = current_step['start_date'] + relativedelta(months=current_step['count'])
                    diff = abs((p.payment_date - expected_next).days)
                    if diff > 5: # 5 day tolerance
                        is_gap = True
                        
                if (current_step is None or 
                    abs(p.amount - current_step['amount']) > 0.01 or 
                    p.type != current_step['type'] or 
                    is_gap):
                    
                    if current_step:
                        steps.append(current_step)
                        
                    current_step = {
                        'start_date': p.payment_date,
                        'amount': p.amount,
                        'type': p.type,
                        'count': 1
                    }
                else:
                    current_step['count'] += 1
                    
            if current_step:
                steps.append(current_step)
                
            for s in steps:
                st = PaymentStep(
                    lease_id=lease.id,
                    start_date=s['start_date'],
                    amount=s['amount'],
                    frequency='Monthly',
                    number_of_payments=s['count'],
                    type=s['type']
                )
                step_objects.append(st)
        
        if step_objects:
            db.session.bulk_save_objects(step_objects)
            db.session.commit()
            
        print(f"Migration Complete. Created {len(step_objects)} steps.")

if __name__ == "__main__":
    reimport_and_migrate()
