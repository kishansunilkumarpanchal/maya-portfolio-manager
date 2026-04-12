import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Customer
import pandas as pd

def fix():
    with app.app_context():
        customers = Customer.query.all()
        print(f"Found {len(customers)} customers. Updating search_name...")
        
        count = 0
        for c in customers:
            updated = False
            # Recalculate Logic (duplicate of import_v2 logic)
            # We don't have the CSV row here, but we have the object fields.
            
            # 1. Company Name
            if c.company_name:
                new_search = c.company_name.strip()
            else:
                first = (c.first_name or "").strip()
                last = (c.last_name or "").strip()
                
                if last and first:
                    new_search = f"{last}, {first}"
                elif last:
                    new_search = last
                elif first:
                    new_search = first
                else:
                    new_search = "Unknown"
            
            if c.search_name != new_search:
                c.search_name = new_search
                updated = True
                count += 1
                
        if count > 0:
            db.session.commit()
            print(f"Updated {count} customers.")
        else:
            print("No customers needed updating.")

if __name__ == "__main__":
    fix()
