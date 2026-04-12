import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Customer, Lease

def check():
    # Use SAME test DB
    test_db = 'test_portfolio.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{test_db}'
    
    print("Using DB:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    with app.app_context():
        # Verify Population
        print("Verifying Population...")
        c1 = Customer.query.filter_by(customer_code='T001').first()
        if c1:
            print(f"T001: '{c1.search_name}' (Expected: 'Alpha Corp')")
        else:
            print("T001 Not Found")
            
        c2 = Customer.query.filter_by(customer_code='T002').first()
        if c2:
            print(f"T002: '{c2.search_name}' (Expected: 'Doe, John')")
        else:
            print("T002 Not Found")
            
        c3 = Customer.query.filter_by(customer_code='T003').first()
        if c3:
             print(f"T003: '{c3.search_name}' (Expected: 'Jane')") # First name only
        else:
             print("T003 Not Found")

        # Verify Search Query Logic
        print("Verifying Search Logic...")
        
        # Test 1: By Company
        search_term = 'Alpha'
        # We need to replicate the search query from app_v2 manually to test it?
        # Or we can just test the expression:
        results = Customer.query.filter(Customer.search_name.contains(search_term)).all()
        print(f"Search '{search_term}': Found {len(results)}")
        
        # Test 2: By Name part
        search_term = 'Doe'
        results = Customer.query.filter(Customer.search_name.contains(search_term)).all()
        print(f"Search '{search_term}': Found {len(results)}")
        
        # Test 3: By First Name
        search_term = 'Jane'
        results = Customer.query.filter(Customer.search_name.contains(search_term)).all()
        print(f"Search '{search_term}': Found {len(results)}")

if __name__ == "__main__":
    check()
