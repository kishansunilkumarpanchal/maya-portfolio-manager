import sys
import os
from dateutil.relativedelta import relativedelta
from datetime import datetime

# Setup path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app_v2 import app, db
from models import Lease, PaymentStep

def clean_redundant_residuals():
    with app.app_context():
        print("Starting Residual Cleanup...")
        
        leases = Lease.query.all()
        count_deleted = 0
        
        for lease in leases:
            if not lease.financial_info or lease.financial_info.lessee_residual <= 0:
                continue
                
            residual_amt = lease.financial_info.lessee_residual
            
            # Get steps sorted by date
            steps = PaymentStep.query.filter_by(lease_id=lease.id).order_by(PaymentStep.start_date).all()
            if not steps: continue
            
            # Check LAST step
            last_step = steps[-1]
            
            # Logic: If last step matches residual amount and is a single payment (and probably labeled as Rent)
            if (abs(last_step.amount - residual_amt) < 0.01 and 
                last_step.number_of_payments == 1):
                
                print(f"Removing redundant step for Lease {lease.lease_number}: "
                      f"{last_step.start_date} Amt: {last_step.amount} Type: {last_step.type}")
                
                db.session.delete(last_step)
                count_deleted += 1
                
        db.session.commit()
        print(f"Cleanup Complete. Removed {count_deleted} redundant residual steps.")

if __name__ == "__main__":
    clean_redundant_residuals()
