from app_v2 import app, db
from models import Lease, LeasePaymentSchedule, PaymentStep

def debug():
    with app.app_context():
        # L2659 has ID 1637 (from previous context)
        # Or search by lease number
        l = Lease.query.filter_by(lease_number='L2659').first()
        if not l:
            print("Lease L2659 not found")
            return

        print(f"Lease {l.id} ({l.lease_number})")
        print(f"Financial Info: NetCap={l.financial_info.net_cap_cost}, Res={l.financial_info.lessee_residual}")
        
        # Check Source Data (post-import)
        payments = LeasePaymentSchedule.query.filter_by(lease_id=l.id).order_by(LeasePaymentSchedule.payment_date).all()
        print(f"Source Payments: {len(payments)}")
        if payments:
            print(f"  First: {payments[0].payment_date} {payments[0].amount} {payments[0].type}")
            print(f"  Last:  {payments[-1].payment_date} {payments[-1].amount} {payments[-1].type}")
        
        # Check Created Steps
        steps = PaymentStep.query.filter_by(lease_id=l.id).order_by(PaymentStep.start_date).all()
        print(f"Created Steps: {len(steps)}")
        
        if steps:
            for s in steps:
                print(f"  Start: {s.start_date}, Count: {s.number_of_payments}, Amt: {s.amount}, Type: {s.type}")
                
        # 3. Check CSV Raw
        import pandas as pd
        import os
        csv_path = 'import_payments.csv'
        if os.path.exists(csv_path):
            print("\nRAW CSV DATA (First 30 rows for L2659):")
            df = pd.read_csv(csv_path)
            df.columns = [c.strip() for c in df.columns]
            rows = df[df['Lease Number'] == 'L2659'].sort_values('Payment Date')
            for _, row in rows.head(30).iterrows():
                print(f"  {row['Payment Date']}: {row['Amount']} ({row['Type']})")

            
if __name__ == "__main__":
    debug()
