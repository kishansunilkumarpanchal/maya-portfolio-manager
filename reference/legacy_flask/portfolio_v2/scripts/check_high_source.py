import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Customer, Lease, LeasePaymentSchedule

def check():
    with app.app_context():
        # 1. Fuzzy search for Customer
        print("--- Customers Matching 'High' ---")
        customers = Customer.query.filter(Customer.search_name.contains('High')).all()
        if not customers:
            print("No customers found with 'High' in search_name.")
            # Try checking company name directly just in case search_name failed population
            others = Customer.query.filter(Customer.company_name.contains('High')).all()
            print(f"Found {len(others)} in company_name.")
            for c in others:
                 print(f"ID: {c.id}, Company: {c.company_name}, SearchName: '{c.search_name}'")
        
        for c in customers:
            print(f"Customer: ID={c.id}, Name='{c.search_name}', Code={c.customer_code}")
            # 2. Check Leases for this customer
            leases = Lease.query.filter_by(customer_id=c.id).all()
            print(f"  Leases: {len(leases)}")
            for l in leases:
                print(f"    Lease: {l.lease_number}, Status: '{l.status}'")

if __name__ == "__main__":
    check()
