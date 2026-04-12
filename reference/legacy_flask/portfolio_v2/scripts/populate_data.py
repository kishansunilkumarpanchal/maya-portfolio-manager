import os
import pandas as pd
from app import app, db # Use app.py as import_v2 does
from import_v2 import import_data

def populate():
    print("Preparing data...")
    # 1. Create dummy data
    df = pd.DataFrame({
        'Customer Code': ['T001', 'T002', 'T003'],
        'Company Name': ['Alpha Corp', '', ''],
        'First Name': ['', 'John', 'Jane'],
        'Last Name': ['', 'Doe', ''],
        'Address 1': ['123 St', '456 Rd', '789 Ln'],
        'City': ['NYC', 'LA', 'SF'],
        'Province': ['NY', 'CA', 'CA'],
        'Postal Code': ['10001', '90210', '94105']
    })
    df.to_csv('import_customers.csv', index=False)
    
    # Ensure clean DB
    # We want to use a test DB.
    # We need to inject config into app.
    test_db = 'test_portfolio.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{test_db}'
    
    db_path = os.path.join(app.instance_path, test_db)
    if os.path.exists(db_path):
        os.remove(db_path)
    # Also check local path just in case
    if os.path.exists(test_db):
        os.remove(test_db)
        
    print("Using DB:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    with app.app_context():
        db.create_all()
        import_data()
        print("Population done.")

if __name__ == "__main__":
    populate()
