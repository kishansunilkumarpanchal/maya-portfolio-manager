from app_v2 import app, db, generate_cash_flows, calculate_irr, calculate_npv
from models import Lease

def verify():
    with app.app_context():
        l = Lease.query.filter_by(lease_number='L2659').first()
        if not l:
            print("Lease L2659 not found")
            return

        print(f"Lease {l.lease_number}")
        
        # Generator
        cash_flows, payments = generate_cash_flows(l)
        
        # IRR
        irr_monthly = calculate_irr(cash_flows)
        irr_annual = (irr_monthly * 12 * 100) if irr_monthly else 0.0
        
        # NPV
        # Filter for future (Display)
        import datetime
        today = datetime.date.today()
        future_payments = [p for p in payments if p['payment_date'] >= today]
        
        periodic_rate = irr_monthly if irr_monthly else 0.0
        npv_value = 0.0
        for i, p in enumerate(future_payments):
            npv_value += p['amount'] / ((1 + periodic_rate) ** (i + 1))
            
        print(f"IRR: {irr_annual:.2f}%")
        print(f"NPV: ${npv_value:,.2f}")
        print("-" * 20)
        print("Cash Flows (First 5 + Last 5):")
        print(f"  Initial: {cash_flows[0]}")
        for cf in cash_flows[1:6]:
            print(f"  Flow: {cf}")
        print("  ...")
        for cf in cash_flows[-5:]:
            print(f"  Flow: {cf}")

if __name__ == "__main__":
    verify()
