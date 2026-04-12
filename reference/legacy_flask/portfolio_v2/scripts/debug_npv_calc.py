from app_v2 import app, generate_cash_flows, calculate_irr
from models import Lease
import datetime

def debug_npv():
    with app.app_context():
        l = Lease.query.filter_by(lease_number='L2659').first()
        
        # Generator
        cash_flows, payments = generate_cash_flows(l)
        
        # IRR
        monthly_irr = calculate_irr(cash_flows)
        print(f"Monthly IRR: {monthly_irr}")
        
        # Display Payments (Future)
        today = datetime.date.today()
        future_payments = [p for p in payments if p['payment_date'] >= today]
        
        periodic_rate = monthly_irr if monthly_irr is not None else 0.0
        
        # 1. Current Logic (Enumerate)
        npv_incorrect = 0.0
        for i, p in enumerate(future_payments):
            npv_incorrect += p['amount'] / ((1 + periodic_rate) ** (i + 1))
            
        print(f"NPV (Current/Incorrect): {npv_incorrect}")
        
        # 2. Correct Logic (Group by Period/Date)
        npv_correct = 0.0
        
        # We need to determine the period index (t) relative to the first future payment?
        # Or relative to "now"? 
        # Usually NPV displayed is "Sum of PVs".
        # If we assume the first future payment is t=1
        
        start_date = future_payments[0]['payment_date'] if future_payments else today
        
        # Simple logical fix: If date is same as prev, don't increment exponent
        current_t = 0
        prev_date = None
        
        for p in future_payments:
            if prev_date is None or p['payment_date'] > prev_date:
                current_t += 1
            # If p['payment_date'] == prev_date, current_t stays same
            
            npv_correct += p['amount'] / ((1 + periodic_rate) ** current_t)
            prev_date = p['payment_date']
            
        print(f"NPV (Corrected): {npv_correct}")
        print(f"Difference: {abs(npv_correct - npv_incorrect)}")

if __name__ == "__main__":
    debug_npv()
