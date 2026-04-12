import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Asset
from sqlalchemy import func

def clean():
    with app.app_context():
        # Find duplicates
        duplicates = db.session.query(
            Asset.lease_id, Asset.vin_serial, Asset.equipment_cost, func.count(Asset.id)
        ).group_by(
            Asset.lease_id, Asset.vin_serial, Asset.equipment_cost
        ).having(func.count(Asset.id) > 1).all()
        
        print(f"Processing {len(duplicates)} duplicate groups...")
        
        deleted_count = 0
        for d in duplicates:
            lease_id = d[0]
            vin = d[1]
            cost = d[2]
            
            # Get all assets in this group
            assets = Asset.query.filter_by(
                lease_id=lease_id,
                vin_serial=vin,
                equipment_cost=cost
            ).all()
            
            # Keep the first one, delete the rest
            if len(assets) > 1:
                to_delete = assets[1:]
                for a in to_delete:
                    db.session.delete(a)
                deleted_count += len(to_delete)
                
        db.session.commit()
        print(f"Deleted {deleted_count} duplicate assets.")

if __name__ == "__main__":
    clean()
