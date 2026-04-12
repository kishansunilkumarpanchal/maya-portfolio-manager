
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app_v2 import app
from models import Lease, PaymentStep

def verify_lease(lease_num):
    with app.app_context():
        l = Lease.query.filter_by(lease_number=lease_num).first()
        if not l:
            print(f"Lease {lease_num} not found.")
            return
        
        print(f"--- Steps for Lease {lease_num} ---")
        steps = PaymentStep.query.filter_by(lease_id=l.id).order_by(PaymentStep.start_date).all()
        for s in steps:
            print(f"Start: {s.start_date}, Amount: {s.amount}, Count: {s.number_of_payments}, Type: {s.type}")

if __name__ == "__main__":
    verify_lease('L2659')
    # Verify another random one if needed
