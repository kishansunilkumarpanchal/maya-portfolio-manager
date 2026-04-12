import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Lease, FinancialInfo

def check():
    with app.app_context():
        # Check Lease L2659
        l = Lease.query.filter_by(lease_number='L2659').first()
        if l:
            print(f"Lease: {l.lease_number}")
            print(f"  Terms: {l.total_terms}")
            print(f"  Start Date: {l.payment_start_date}")
            print(f"  Funding Date: {l.funding_date}")
            if l.financial_info:
                print(f"  Monthly Payment: {l.financial_info.monthly_payment}")
                print(f"  Residual: {l.financial_info.lessee_residual}")
                print(f"  Net Cap Cost: {l.financial_info.net_cap_cost}")
            else:
                print("  No Financial Info!")
        else:
            print("Lease L2659 not found.")

if __name__ == "__main__":
    check()
