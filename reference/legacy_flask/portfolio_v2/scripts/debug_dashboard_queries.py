from app import app, db, Asset, Lease, FinancialInfo
from sqlalchemy import func

def debug_queries():
    print("--- Debugging Dashboard Queries ---")
    
    # 1. Total Assets
    total_leases = Asset.query.count()
    print(f"Total Assets (count): {total_leases}")
    
    # 2. Active Leases
    active_leases = Lease.query.filter(Lease.status == 'ACTV').count()
    print(f"Active Leases (count): {active_leases}")
    
    # 3. Total Portfolio Value
    try:
        total_value = db.session.query(func.sum(FinancialInfo.net_cap_cost))\
            .join(Lease)\
            .filter(Lease.status == 'ACTV')\
            .scalar()
        print(f"Total Portfolio Value: {total_value}")
    except Exception as e:
        print(f"Error calculating total value: {e}")
        
    # Check sample data
    print("\n--- Sample Data Check ---")
    print(f"First 5 Lease Statuses: {[l.status for l in Lease.query.limit(5).all()]}")
    
if __name__ == "__main__":
    with app.app_context():
        debug_queries()
