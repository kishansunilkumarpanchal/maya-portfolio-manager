import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Lease
from dateutil.relativedelta import relativedelta
import datetime

def update_dates():
    print("Updating Last Payment Dates (Formula: Start + Terms)...")
    
    with app.app_context():
        leases = Lease.query.all()
        count = 0
        changed = 0
        
        for lease in leases:
            if lease.payment_start_date and lease.total_terms is not None:
                # Logic: Last Payment = Start + Total Terms (months)
                # Explanation:
                # If Terms = 59.
                # Rent 1 = Start (Month 0)
                # ...
                # Rent 59 = Start + 58 months.
                # Residual = Start + 59 months.
                # So Last Date = Start + Terms.
                
                calculated_date = lease.payment_start_date + relativedelta(months=lease.total_terms)
                
                if lease.last_payment_date != calculated_date:
                    lease.last_payment_date = calculated_date
                    changed += 1
            else:
                # Cannot calculate if start or terms missing
                pass
                
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} leases...")
                db.session.commit()
        
        db.session.commit()
        print(f"Finished. Updated {changed} leases out of {count}.")

if __name__ == "__main__":
    update_dates()
