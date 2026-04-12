import sys
import os
import pandas as pd
from dateutil.relativedelta import relativedelta
from sqlalchemy import text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Lease, PaymentStep, FinancialInfo

def import_steps():
    file_path = os.path.join('data', 'Lease rate export_25_12.xlsx')
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print(f"Reading {file_path}...")
    df = pd.read_excel(file_path)
    
    # Normalize columns
    df.columns = [c.strip() for c in df.columns]
    
    with app.app_context():
        # 1. Clear existing PaymentSteps
        print("Clearing payment_steps table...")
        db.session.query(PaymentStep).delete()
        db.session.commit()
        
        # Cache leases for speed
        print("Caching leases...")
        measure_leases = Lease.query.all()
        lease_map = {l.lease_number: l for l in measure_leases}
        
        count_steps = 0
        updated_residuals = 0
        
        for _, row in df.iterrows():
            lease_num = str(row['UnitNumber']).strip()
            lease = lease_map.get(lease_num)
            
            if not lease:
                print(f"Warning: Lease {lease_num} not found. Skipping.")
                continue
            
            # --- Rent Step ---
            # RateSTerm is 1-based (e.g. Month 1)
            # Start Date = Lease Start + (StartTerm - 1) months
            if not lease.payment_start_date:
                print(f"Warning: Lease {lease_num} has no start date. Skipping.")
                continue
                
            start_term = int(row['RateSTerm'])
            end_term = int(row['RateETerm'])
            amount = float(row['LeaseRate'])
            
            step_start_date = lease.payment_start_date + relativedelta(months=(start_term - 1))
            num_payments = end_term - start_term + 1
            
            step = PaymentStep(
                lease_id=lease.id,
                start_date=step_start_date,
                amount=amount,
                frequency='Monthly',
                number_of_payments=num_payments,
                type='Rent'
            )
            db.session.add(step)
            count_steps += 1
            
            # --- Residual Update ---
            # Update FinancialInfo if OptResidual is present
            opt_residual = row.get('OptResidual', 0)
            if pd.notna(opt_residual) and opt_residual > 0:
                fin = FinancialInfo.query.get(lease.id)
                if not fin:
                    # Create if missing (should exist from previous migration, but safe to check)
                    fin = FinancialInfo(lease_id=lease.id)
                    db.session.add(fin)
                
                # Only update if different (to avoid useless dirtiness, though inexpensive here)
                if fin.lessee_residual != opt_residual:
                    fin.lessee_residual = float(opt_residual)
                    updated_residuals += 1
                    
        db.session.commit()
        print(f"Import Complete.")
        print(f"  Created {count_steps} payment steps.")
        print(f"  Updated {updated_residuals} lease residuals.")

if __name__ == "__main__":
    import_steps()
