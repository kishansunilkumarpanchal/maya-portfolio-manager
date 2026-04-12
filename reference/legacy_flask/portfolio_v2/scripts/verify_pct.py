import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Asset

def verify():
    with app.app_context():
        # Lease 1663 had multiple assets in the log (L2685-529, L2685-533, L2685-471)
        lease_id = 1663 
        assets = Asset.query.filter(Asset.lease_id == lease_id).all()
        
        print(f"Lease {lease_id} Assets:")
        total_pct = 0
        total_cost = 0
        for a in assets:
            print(f"Asset {a.asset_id}: Cost={a.equipment_cost}, Pct={a.percentage_value}")
            total_pct += a.percentage_value
            total_cost += a.equipment_cost
            
        print(f"Total Cost: {total_cost}")
        print(f"Total Pct: {total_pct}")

if __name__ == "__main__":
    verify()
