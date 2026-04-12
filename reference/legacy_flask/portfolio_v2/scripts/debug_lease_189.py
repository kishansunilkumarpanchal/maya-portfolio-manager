from app_v2 import app, db
from models import Lease, LeasePaymentSchedule, PaymentStep

def debug():
    with app.app_context():
        l = Lease.query.get(189)
        if not l:
            print("Lease 189 not found")
            return

        print(f"Lease {l.id} ({l.lease_number})")
        
        # Check Source Data
        payments = LeasePaymentSchedule.query.filter_by(lease_id=l.id).order_by(LeasePaymentSchedule.payment_date).all()
        print(f"Source Payments: {len(payments)}")
        for p in payments[:10]:
            print(f"  {p.payment_date}: {p.amount} ({p.type})")
        print("  ...")
        
        # Check Created Steps
        steps = PaymentStep.query.filter_by(lease_id=l.id).order_by(PaymentStep.start_date).all()
        print(f"Created Steps: {len(steps)}")
        for s in steps[:10]:
            print(f"  Start: {s.start_date}, Count: {s.number_of_payments}, Amt: {s.amount}, Type: {s.type}")
            
if __name__ == "__main__":
    debug()
