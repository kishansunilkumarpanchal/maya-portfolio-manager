
import sys
import os
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Setup path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app_v2 import app, db
from models import Lease, PaymentStep, LeasePaymentSchedule

def reimport_steps_from_excel():
    with app.app_context():
        print("Starting Re-import of Steps from Excel...")
        
        # 1. Clear Tables
        print("Clearing PaymentStep and LeasePaymentSchedule tables...")
        PaymentStep.query.delete()
        LeasePaymentSchedule.query.delete()
        db.session.commit()
        
        # 2. Read Excel
        excel_path = os.path.join(os.path.dirname(__file__), '../../portfolio_v1/mock_data.xlsm')
        if not os.path.exists(excel_path):
            print(f"Error: {excel_path} not found!")
            return

        print(f"Reading {excel_path} (AssetData)...")
        # Load AssetData. Header is row 1 (0-indexed) -> So header=1
        df = pd.read_excel(excel_path, sheet_name='AssetData', header=1)
        
        # Identify Columns
        # 'Unit #' is Lease Number (Col 0)
        # 'Lessee Residual' (Col 17 approx?) -> Look for column named 'Lessee Residual'
        # Date columns -> Look for datetime columns
        
        lease_col = 'Unit #'
        residual_col = 'Lessee Residual'
        
        if lease_col not in df.columns:
            # Fallback or error
            print(f"Error: Could not find '{lease_col}' column.")
            print("Columns found:", df.columns.tolist())
            return
            
        date_cols = [c for c in df.columns if isinstance(c, (datetime, pd.Timestamp))]
        date_cols.sort()
        
        if not date_cols:
            print("Error: No date columns found in AssetData.")
            return
            
        print(f"Found {len(date_cols)} date columns from {date_cols[0]} to {date_cols[-1]}.")
        
        # 3. Aggregate Data by Lease
        print("Aggregating data by Lease...")
        
        # We need to map Lease Number -> ID
        existing_leases = {l.lease_number: l.id for l in Lease.query.all()}
        
        # Group by Lease Number
        grouped = df.groupby(lease_col)
        
        total_steps_created = 0
        
        for lease_num, group in grouped:
            lease_num_str = str(lease_num).strip()
            lease_id = existing_leases.get(lease_num_str)
            
            if not lease_id:
                print(f"Skipping Lease {lease_num_str}: Not found in DB.")
                continue
                
            # Calulcate Total Residual for this lease (sum of units)
            total_residual = group[residual_col].sum() if residual_col in group.columns else 0
            
            # Aggregate Monthly Payments
            # Sum columns for the date range
            # Result is a Series with index=Date, value=SumAmount
            monthly_sums = group[date_cols].sum(numeric_only=True)
            
            # Identify valid payments (non-zero)
            # Actually, sometimes 0 might be valid? But usually 0 means no payment.
            # We filter out NaNs or 0s?
            # Let's keep 0 only if it's explicitly 0? Use non-na?
            # In Excel, empty is NaN.
            monthly_sums = monthly_sums.dropna()
            monthly_sums = monthly_sums[monthly_sums > 0.01] # Filter small amounts/zeros
            
            if monthly_sums.empty:
                continue
            
            # Generate Steps
            steps = []
            current_step = None
            
            sorted_dates = sorted(monthly_sums.index)
            
            for d in sorted_dates:
                amount = float(monthly_sums[d])
                date_val = d.date() if hasattr(d, 'date') else d
                
                # Check for "gap" logic?
                is_gap = False
                if current_step:
                    expected_next = current_step['start_date'] + relativedelta(months=current_step['count'])
                    # Tolerance: if diff is huge. But we are iterating sorted_dates which might have gaps?
                    # The dates strictly follow column headers.
                    # If there's a gap in columns, it means skipped months?
                    # But columns are continuous usually.
                    # Let's check difference between this date and expected next
                    diff_days = abs((date_val - expected_next).days)
                    if diff_days > 5:
                        is_gap = True

                if (current_step is None or 
                    abs(amount - current_step['amount']) > 0.01 or 
                    is_gap):
                    
                    if current_step:
                        steps.append(current_step)
                    
                    current_step = {
                        'start_date': date_val,
                        'amount': amount,
                        'count': 1,
                        'type': 'Rent' # Default
                    }
                else:
                    current_step['count'] += 1
            
            if current_step:
                steps.append(current_step)
            
            # Post-Process: Remove Residual Step
            # If the last step looks like a residual payment
            if steps:
                last = steps[-1]
                # If amount matches residual sum (within tolerance) AND count is 1
                if abs(last['amount'] - total_residual) < 1.0 and last['count'] == 1:
                    print(f"Lease {lease_num_str}: Excluding residual step {last['amount']} (Total Res: {total_residual})")
                    steps.pop()
            
            # Write to DB
            for s in steps:
                st = PaymentStep(
                    lease_id=lease_id,
                    start_date=s['start_date'],
                    amount=s['amount'],
                    frequency='Monthly',
                    number_of_payments=s['count'],
                    type=s['type']
                )
                db.session.add(st)
                total_steps_created += 1
                
        db.session.commit()
        print(f"Done. Created {total_steps_created} steps.")

if __name__ == "__main__":
    reimport_steps_from_excel()
