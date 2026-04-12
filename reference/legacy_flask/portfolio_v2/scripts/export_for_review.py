import csv
import os
import sys
import datetime

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_v2 import app
from models import db, Lease, Customer, FinancialInfo, Asset

def export_data():
    output_file = 'current_portfolio.csv'
    
    headers = [
        'Lease Number', 'Status', 'Funding Date', 'Payment Start Date', 'Total Terms', 'Interest Rate', 'Tax Code',
        'Customer Code', 'Company Name', 'First Name', 'Last Name',
        'Net Cap Cost', 'Monthly Payment', 'Lessee Residual', 'Security Deposit',
        'Asset Year', 'Asset Make', 'Asset VIN', 'Asset Cost'
    ]

    with app.app_context():
        leases = Lease.query.all()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            count = 0
            for lease in leases:
                # Basic Info
                l_num = lease.lease_number
                status = lease.status
                fund_date = lease.funding_date
                start_date = lease.payment_start_date
                terms = lease.total_terms
                rate = lease.interest_rate
                tax = lease.tax_code or ''
                
                # Customer Info
                cust = lease.customer
                c_code = cust.customer_code if cust else ''
                c_company = cust.company_name if cust else ''
                c_first = cust.first_name if cust else ''
                c_last = cust.last_name if cust else ''
                
                # Financial Info
                fin = lease.financial_info
                net_cap = fin.net_cap_cost if fin else 0.0
                payment = fin.monthly_payment if fin else 0.0
                residual = fin.lessee_residual if fin else 0.0
                deposit = fin.security_deposit if fin else 0.0
                
                # Assets
                # If no assets, write one row with empty asset fields
                if not lease.assets:
                    row = [
                        l_num, status, fund_date, start_date, terms, rate, tax,
                        c_code, c_company, c_first, c_last,
                        net_cap, payment, residual, deposit,
                        '', '', '', 0.0
                    ]
                    writer.writerow(row)
                    count += 1
                else:
                    for asset in lease.assets:
                        row = [
                            l_num, status, fund_date, start_date, terms, rate, tax,
                            c_code, c_company, c_first, c_last,
                            net_cap, payment, residual, deposit,
                            asset.year, asset.make_model, asset.vin_serial, asset.equipment_cost
                        ]
                        writer.writerow(row)
                        count += 1
                        
        print(f"Exported {count} rows to {output_file}")

if __name__ == "__main__":
    export_data()
