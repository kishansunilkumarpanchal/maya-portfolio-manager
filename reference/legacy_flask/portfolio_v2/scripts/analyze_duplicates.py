import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Asset
from sqlalchemy import func

def analyze():
    with app.app_context():
        total = Asset.query.count()
        print(f"Total Assets: {total}")
        
        # Check for duplicates based on Lease ID + VIN + Cost
        # (Assuming these should be unique per asset)
        duplicates = db.session.query(
            Asset.lease_id, Asset.vin_serial, Asset.equipment_cost, func.count(Asset.id)
        ).group_by(
            Asset.lease_id, Asset.vin_serial, Asset.equipment_cost
        ).having(func.count(Asset.id) > 1).all()
        
        print(f"Found {len(duplicates)} groups of duplicates.")
        
        dup_count = 0
        for d in duplicates:
            print(f"  Lease: {d[0]}, VIN: {d[1]}, Cost: {d[2]} -> Count: {d[3]}")
            dup_count += (d[3] - 1)
            
        print(f"Estimated removable duplicates: {dup_count}")

if __name__ == "__main__":
    analyze()
