import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Customer, Lease
import pandas as pd
import os

def verify():
    # 1. Create dummy data for import
    df = pd.DataFrame({
        'Customer Code': ['T001', 'T002'],
        'Company Name': ['Alpha Corp', ''], # Empty for second
        'First Name': ['', 'John'],
        'Last Name': ['', 'Doe'],
        'Address 1': ['123 St', '456 Rd'],
        'City': ['NYC', 'LA'],
        'Province': ['NY', 'CA'],
        'Postal Code': ['10001', '90210']
    })
    df.to_csv(os.path.join('data', 'import_customers.csv'), index=False)
    
    # 2. Run Import
    from import_v2 import import_data
    
    # Ensure clean DB
    test_db_path = 'instance/test_portfolio.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{test_db_path.split("/")[-1]}' # Use relative path for init
    
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    print("Context created")
    with app.app_context():
        # Override DB path for session 
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_portfolio.db'
        
        print("Creating tables...")
        db.create_all()
        print("Tables created")
        
        # Run Import
        print("Calling import_data...")
        import_data()
        print("Import finished")
        
        # 3. Verify Search Name Population
        print("Verifying...")
        c1 = Customer.query.filter_by(customer_code='T001').first()
        if c1:
            print(f"Customer 1 Search Name: '{c1.search_name}' (Expected: 'Alpha Corp')")
        else:
            print("Customer 1 not found")
        
        c2 = Customer.query.filter_by(customer_code='T002').first()
        if c2:
            print(f"Customer 2 Search Name: '{c2.search_name}' (Expected: 'Doe, John')")
        else:
            print("Customer 2 not found")
        
        # 4. Verify Search Logic (Query)
        # Search for 'Alpha'
        search_term = 'Alpha'
        results = Customer.query.filter(Customer.search_name.contains(search_term)).all()
        print(f"Search for '{search_term}' returned {len(results)} results.")
        
        # Search for 'Doe'
        search_term = 'Doe'
        results = Customer.query.filter(Customer.search_name.contains(search_term)).all()
        print(f"Search for '{search_term}' returned {len(results)} results.")

if __name__ == "__main__":
    print("Main start")
    verify()
    print("Main end")
