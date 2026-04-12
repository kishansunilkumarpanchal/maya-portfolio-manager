import pandas as pd
from app_v2 import app, db
from models import Customer, Lease, FinancialInfo, LeasePaymentSchedule, Province, AssetGroup, TaxRate, Asset
from datetime import datetime
import os

def parse_date(date_str):
    if pd.isna(date_str) or date_str == '':
        return None
    try:
        return pd.to_datetime(date_str).date()
    except:
        return None

def import_data():
    print("Starting data import...")
    
    # --- 1. Master Data ---
    # Import Provinces
    if os.path.exists(os.path.join('data', 'import_provinces.csv')):
        print("Importing Provinces...")
        df_prov = pd.read_csv(os.path.join('data', 'import_provinces.csv'))
        for _, row in df_prov.iterrows():
            if not Province.query.get(row['Code']):
                p = Province(code=row['Code'], name=row['Name'])
                db.session.add(p)
        db.session.commit()

    # Import Asset Groups
    if os.path.exists(os.path.join('data', 'import_asset_groups.csv')):
        print("Importing Asset Groups...")
        df_groups = pd.read_csv(os.path.join('data', 'import_asset_groups.csv'))
        for _, row in df_groups.iterrows():
            if not AssetGroup.query.get(row['ID']):
                g = AssetGroup(id=row['ID'], description=row['Description'])
                db.session.add(g)
        db.session.commit()

    # Import Tax Rates
    if os.path.exists(os.path.join('data', 'import_tax_rates.csv')):
        print("Importing Tax Rates...")
        df_tax = pd.read_csv(os.path.join('data', 'import_tax_rates.csv'))
        for _, row in df_tax.iterrows():
            if not TaxRate.query.get(row['Code']):
                t = TaxRate(
                    code=row['Code'],
                    description=row['Description'],
                    rate1=row['Rate1'], desc1=row['Desc1'],
                    rate2=row['Rate2'], desc2=row['Desc2'],
                    rate3=row['Rate3'], desc3=row['Desc3']
                )
                db.session.add(t)
        db.session.commit()

    # --- 2. Customers ---
    print("Importing Customers...")
    if os.path.exists(os.path.join('data', 'import_customers.csv')):
        df_cust = pd.read_csv(os.path.join('data', 'import_customers.csv'))
        # Clean column names just in case
        df_cust.columns = [c.strip() for c in df_cust.columns]
        
        for _, row in df_cust.iterrows():
            code = str(row['Customer Code']).strip()
            if not Customer.query.filter_by(customer_code=code).first():
                c = Customer(
                    customer_code=code,
                    first_name=row.get('First Name'),
                    middle_name=row.get('Middle Name'),
                    last_name=row.get('Last Name'),
                    company_name=row.get('Company Name'),
                    trade_name=row.get('Trade Name'),
                    address1=row.get('Address 1'),
                    address2=row.get('Address 2'),
                    city=row.get('City'),
                    province_code=row.get('Province'),
                    postal_code=row.get('Postal Code')
                )
                
                # Calculate Search Name
                company = row.get('Company Name')
                if company and pd.notna(company):
                    c.search_name = str(company).strip()
                else:
                    first = str(row.get('First Name', '')).strip()
                    last = str(row.get('Last Name', '')).strip()
                    if pd.isna(row.get('First Name')): first = ""
                    if pd.isna(row.get('Last Name')): last = ""
                    
                    if last and first:
                        c.search_name = f"{last}, {first}"
                    elif last:
                        c.search_name = last
                    elif first:
                        c.search_name = first
                    else:
                        c.search_name = "Unknown"
                        
                db.session.add(c)
        db.session.commit()
    else:
        print("import_customers.csv not found!")

    # --- 3. Leases ---
    print("Importing Leases...")
    if os.path.exists(os.path.join('data', 'import_leases.csv')):
        df_lease = pd.read_csv(os.path.join('data', 'import_leases.csv'))
        df_lease.columns = [c.strip() for c in df_lease.columns]
        
        # Cache customers for lookup
        customers = {c.customer_code: c.id for c in Customer.query.all()}
        
        for _, row in df_lease.iterrows():
            lease_num = str(row['Lease Number']).strip()
            cust_code = str(row['Customer Code']).strip()
            
            if lease_num and not Lease.query.filter_by(lease_number=lease_num).first():
                cust_id = customers.get(cust_code)
                if cust_id:
                    l = Lease(
                        lease_number=lease_num,
                        customer_id=cust_id,
                        funding_date=parse_date(row.get('Funding Date')),
                        payment_start_date=parse_date(row.get('Payment Start Date')),
                        total_terms=row.get('Total Terms'),
                        interest_rate=row.get('Interest Rate'),
                        status=row.get('Status')
                    )
                    db.session.add(l)
                else:
                    print(f"Warning: Customer {cust_code} not found for Lease {lease_num}")
        db.session.commit()
    else:
        print("import_leases.csv not found!")

    # --- 4. Financials ---
    print("Importing Financials...")
    if os.path.exists(os.path.join('data', 'import_financials.csv')):
        df_fin = pd.read_csv(os.path.join('data', 'import_financials.csv'))
        df_fin.columns = [c.strip() for c in df_fin.columns]
        
        # Cache leases for lookup
        leases = {l.lease_number: l.id for l in Lease.query.all()}
        
        for _, row in df_fin.iterrows():
            lease_num = str(row['Lease Number']).strip()
            lease_id = leases.get(lease_num)
            
            if lease_id and not FinancialInfo.query.get(lease_id):
                f = FinancialInfo(
                    lease_id=lease_id,
                    capital_cost=row.get('Capital Cost'),
                    cap_cost_adjustment=row.get('Cap Cost Adjustment'),
                    downpayment=row.get('Downpayment'),
                    trade_amount=row.get('Trade Amount'),
                    lessee_residual=row.get('Lessee Residual'),
                    lessor_residual=row.get('Lessor Residual'),
                    monthly_depreciation=row.get('Monthly Depreciation'),
                    monthly_payment=row.get('Monthly Payment'),
                    security_deposit=row.get('Security Deposit')
                )
                # Calculate Net Cap Cost
                try:
                    cap = f.capital_cost or 0
                    adj = f.cap_cost_adjustment or 0
                    down = f.downpayment or 0
                    trade = f.trade_amount or 0
                    # Correct Formula: Cap + Adj - Down - Trade
                    f.net_cap_cost = cap + adj - down - trade
                except:
                    f.net_cap_cost = 0
                    
                db.session.add(f)
        db.session.commit()
    else:
        print("import_financials.csv not found!")

    # --- 5. Payments ---
    print("Importing Payments...")
    if os.path.exists(os.path.join('data', 'import_payments.csv')):
        # Read in chunks if file is very large, but 1.3MB is fine for memory
        df_pay = pd.read_csv(os.path.join('data', 'import_payments.csv'))
        df_pay.columns = [c.strip() for c in df_pay.columns]
        
        # Cache leases for lookup (re-fetch in case new ones added, though unlikely in this flow)
        leases = {l.lease_number: l.id for l in Lease.query.all()}
        
        payment_objects = []
        for _, row in df_pay.iterrows():
            lease_num = str(row['Lease Number']).strip()
            lease_id = leases.get(lease_num)
            
            if lease_id:
                # Check for duplicates (Lease + Date + Amount + Type)
                existing = LeasePaymentSchedule.query.filter_by(
                    lease_id=lease_id,
                    payment_date=parse_date(row.get('Payment Date')),
                    amount=row.get('Amount'),
                    type=row.get('Type')
                ).first()
                
                if not existing:
                    p = LeasePaymentSchedule(
                        lease_id=lease_id,
                        payment_date=parse_date(row.get('Payment Date')),
                        amount=row.get('Amount'),
                        period_number=row.get('Period Number'),
                        type=row.get('Type')
                    )
                    payment_objects.append(p)
        
        if payment_objects:
            # Bulk insert for performance
            db.session.bulk_save_objects(payment_objects)
            db.session.commit()
    else:
        print("import_payments.csv not found!")

    # --- 6. Assets ---
    print("Importing Assets...")
    if os.path.exists(os.path.join('data', 'import_assets.csv')):
        # Try default encoding first, then fallback if needed
        try:
            df_asset = pd.read_csv(os.path.join('data', 'import_assets.csv'))
        except UnicodeDecodeError:
            df_asset = pd.read_csv(os.path.join('data', 'import_assets.csv'), encoding='cp1252')
            
        df_asset.columns = [c.strip() for c in df_asset.columns]
        
        # Clean Equipment Cost column first
        def clean_cost(val):
            s = str(val).replace(',', '').replace('$', '').strip()
            try:
                return float(s)
            except:
                return 0.0
        
        df_asset['Equipment Cost Clean'] = df_asset['Equipment Cost'].apply(clean_cost)
        
        # Calculate Total Equipment Cost per Lease
        lease_totals = df_asset.groupby('Lease Number')['Equipment Cost Clean'].sum().to_dict()
        
        # Cache leases for lookup
        leases = {l.lease_number: l.id for l in Lease.query.all()}
        
        count = 0
        for _, row in df_asset.iterrows():
            lease_num = str(row['Lease Number']).strip()
            lease_id = leases.get(lease_num)
            
            if lease_id:
                # Generate Asset ID (Lease # + last 3 of VIN if available, else random/index)
                vin = str(row.get('VIN Serial', ''))
                if pd.isna(vin) or vin == 'nan':
                    vin = ''
                    
                suffix = vin[-3:] if len(vin) >= 3 else f"{count:03d}"
                asset_id = f"{lease_num}-{suffix}"
                
                equipment_cost = row['Equipment Cost Clean']

                # Calculate Percentage Value
                # percentage = equipment_cost / total_equipment_cost_for_lease
                total_cost = lease_totals.get(lease_num, 0.0)
                percentage_value = 0.0
                if total_cost and total_cost > 0:
                    percentage_value = (equipment_cost / total_cost) * 100

                # Check if asset already exists
                existing_asset = Asset.query.filter_by(asset_id=asset_id).first()
                if not existing_asset:
                    a = Asset(
                        lease_id=lease_id,
                        asset_id=asset_id,
                        group_id=row.get('Asset Group'),
                        year=row.get('Year'),
                        make_model=row.get('Make Model'),
                        vin_serial=vin,
                        finance_source=row.get('Finance Source'),
                        equipment_cost=equipment_cost,
                        percentage_value=percentage_value,
                        status=row.get('Status')
                    )
                    db.session.add(a)
                    count += 1
                else:
                    print(f"Skipping existing asset: {asset_id}")
        db.session.commit()
        print(f"Imported {count} assets.")
    else:
        print("import_assets.csv not found!")

    print("Data import completed successfully.")

if __name__ == "__main__":
    with app.app_context():
        try:
            # Reset Database
            print("Dropping existing tables...")
            db.drop_all()
            print("Creating new tables...")
            db.create_all()
            import_data()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error during import: {e}")
