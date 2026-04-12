import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Customer, Lease, Asset, FinancialInfo

def verify():
    with app.app_context():
        print("--- Data Verification Report ---")
        
        # Counts
        c_count = Customer.query.count()
        l_count = Lease.query.count()
        a_count = Asset.query.count()
        f_count = FinancialInfo.query.count()
        
        print(f"Customers: {c_count}")
        print(f"Leases:    {l_count}")
        print(f"Assets:    {a_count}")
        print(f"Financials:{f_count}")
        
        print("-" * 30)
        
        # Orphans
        orphaned_leases = Lease.query.filter(Lease.customer_id == None).count()
        orphaned_assets = Asset.query.filter(Lease.id == None).count() # Should be handled by FK, but checking logic
        
        print(f"Orphaned Leases: {orphaned_leases}")
        
        # Missing Financials
        leases_without_fin = 0
        leases = Lease.query.all()
        for l in leases:
            if not l.financial_info:
                leases_without_fin += 1
        print(f"Leases without Financials: {leases_without_fin}")
        
        # Negative Net Cap Cost
        neg_cap = FinancialInfo.query.filter(FinancialInfo.net_cap_cost < 0).count()
        print(f"Negative Net Cap Cost: {neg_cap}")
        
        print("-" * 30)
        print("Verification Complete.")

if __name__ == "__main__":
    verify()
