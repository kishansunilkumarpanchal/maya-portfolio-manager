import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app, db
from models import Lease, Asset

def check():
    with app.app_context():
        lease_count = Lease.query.count()
        asset_count = Asset.query.count()
        
        print(f"Total Leases Row Count: {lease_count}")
        print(f"Total Assets Row Count: {asset_count}")

if __name__ == "__main__":
    check()
