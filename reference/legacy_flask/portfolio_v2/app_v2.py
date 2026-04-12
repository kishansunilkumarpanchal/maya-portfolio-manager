from flask import Flask, render_template, request, redirect, url_for, jsonify
import datetime
from models import db, Customer, Lease, FinancialInfo, Asset, LeasePaymentSchedule, InactiveAssetLog, PaymentStep
from sqlalchemy import func
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Financial Helpers ---
def calculate_npv(rate, values):
    """
    Calculate NPV given a periodic rate and list of values.
    rate: periodic rate (e.g. 0.01 for 1%)
    values: list of cash flows [cf0, cf1, cf2, ...]
    """
    total = 0.0
    for i, v in enumerate(values):
        total += v / ((1 + rate) ** i)
    return total

def calculate_irr(values, guess=0.1):
    """
    Calculate IRR using Newton-Raphson method.
    values: list of cash flows
    Returns periodic rate (decimal).
    """
    max_iter = 100
    tol = 1e-6
    rate = guess
    
    for _ in range(max_iter):
        npv = 0.0
        d_npv = 0.0
        
        for i, v in enumerate(values):
            denom = (1 + rate) ** i
            npv += v / denom
            if i > 0:
                d_npv -= i * v / ((1 + rate) ** (i + 1))
                
        if abs(npv) < tol:
            return rate
            
        if d_npv == 0:
            return None # Failed to converge
            
        rate = rate - npv / d_npv
        
        if rate <= -1: # Avoid invalid rates
             rate = -0.99
             
    return rate

# DB Config
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'instance', 'portfolio.db')

database_url = os.getenv('DATABASE_URL')
# Hande Heroku/SQLAlchemy postgres scheme difference if needed
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super_secret_key_v2'

db.init_app(app)

@app.route('/')
def dashboard():
    # KPI: Total Leases (Count of Leases, not Assets)
    total_leases = Lease.query.count()
    
    # KPI: Total Portfolio Value (Sum of Net Cap Cost for Active Leases)
    # We filter Leases by status='ACTV' and sum their FinancialInfo.net_cap_cost
    total_value = db.session.query(func.sum(FinancialInfo.net_cap_cost))\
        .join(Lease)\
        .filter(Lease.status == 'ACTV')\
        .scalar() or 0
    
    # KPI: Active Leases (Status is 'ACTV')
    active_leases = Lease.query.filter(Lease.status == 'ACTV').count()
    
    # Recent Leases
    recent_leases = Lease.query.order_by(Lease.funding_date.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           total_leases=total_leases, 
                           total_value=total_value, 
                           active_leases=active_leases,
                           recent_leases=recent_leases)

@app.route('/leases')
def leases():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Status Filter
    status = request.args.get('status', 'ACTV') # Default to Active
    
    query = Lease.query.order_by(Lease.lease_number)
    
    if status != 'All':
        query = query.filter(Lease.status == status)
    
    # Search
    search = request.args.get('search')
    if search:
        query = query.join(Customer).filter(
            (Lease.lease_number.contains(search)) | 
            (Customer.search_name.contains(search))
        )
        
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    leases = pagination.items
    
    return render_template('leases.html', leases=leases, pagination=pagination, search=search, status=status) 

def generate_cash_flows(lease):
    """
    Generates monthly cash flows from PaymentSteps.
    Returns: (list of cash flows for IRR, list of future payment objects for display)
    """
    from dateutil.relativedelta import relativedelta
    
    # 1. Initial Investment (t=0)
    total_asset_cost = sum(a.equipment_cost for a in lease.assets) if lease.assets else 0
    active_asset_cost = sum(a.equipment_cost for a in lease.assets if a.status == 'ACTV') if lease.assets else 0
    
    proration_factor = 1.0
    if total_asset_cost > 0:
        proration_factor = active_asset_cost / total_asset_cost
        
    initial_outflow = 0.0
    if lease.financial_info:
        initial_outflow = -(lease.financial_info.net_cap_cost * proration_factor)
        
    cash_flows = [initial_outflow]
    expanded_payments = []
    
    # 2. Expand Steps
    steps = PaymentStep.query.filter_by(lease_id=lease.id).order_by(PaymentStep.start_date).all()
    
    # Track periods for IRR (t=0 is initial). First payment is t=1.
    last_date = None
    
    for step in steps:
        current_date = step.start_date
        for i in range(step.number_of_payments):
            amount = step.amount * proration_factor
            
            # Append to cash flows
            cash_flows.append(amount)
            
            # Calculate cumulative period number
            period_num = i + 1
            if lease.payment_start_date:
                # diff in months + 1
                period_num = (current_date.year - lease.payment_start_date.year) * 12 + \
                             (current_date.month - lease.payment_start_date.month) + 1
            
            expanded_payments.append({
                'payment_date': current_date,
                'amount': amount,
                'type': step.type or 'Rent',
                'period_number': period_num
            })
            
            last_date = current_date
            current_date += relativedelta(months=1)
            
    # 3. Append Residual (Automatic)
    # Add to the LAST cash flow (concurrent with last payment)
    if lease.financial_info and lease.financial_info.lessee_residual > 0:
        res_amount = lease.financial_info.lessee_residual * proration_factor
        
        if len(cash_flows) > 1:
            cash_flows[-1] += res_amount
        else:
            cash_flows.append(res_amount)
            
        # Add 1 month to the last payment date
        if last_date:
            res_date = last_date + relativedelta(months=1)
        else:
            res_date = datetime.date.today()

        expanded_payments.append({
            'payment_date': res_date,
            'amount': res_amount,
            'type': 'Residual', # Changed label
            'period_number': 'Res'
        })
        
    return cash_flows, expanded_payments

@app.route('/lease/<int:id>')
def lease_detail(id):
    lease = Lease.query.get_or_404(id)
    
    # Generate Dynamic Cash Flows
    cash_flows, all_generated_payments = generate_cash_flows(lease)
    
    # Filter for future (Display)
    today = datetime.date.today()
    future_payments = [p for p in all_generated_payments if p['payment_date'] >= today]
    
    # --- Metrics Calculation ---
    
    # 1. Remaining Term & Total
    remaining_term = len(future_payments)
    remaining_total = sum(p['amount'] for p in future_payments)
    
    # 2. IRR
    monthly_irr = calculate_irr(cash_flows)
    irr_annual = (monthly_irr * 12 * 100) if monthly_irr else 0.0
    
    # 3. NPV
    periodic_rate = monthly_irr if monthly_irr is not None else 0.0
    # NPV of Future Flows (t=1 to N)
    npv_value = 0.0
    
    current_t = 0
    prev_date = None
    
    for p in future_payments:
        # Increment period only if date advances
        if prev_date is None or p['payment_date'] > prev_date:
            current_t += 1
        
        npv_value += p['amount'] / ((1 + periodic_rate) ** current_t)
        prev_date = p['payment_date']

    return render_template('lease_detail.html', lease=lease, future_payments=future_payments,
                           metric_irr=irr_annual,
                           metric_npv=npv_value,
                           metric_rem_term=remaining_term,
                           metric_rem_total=remaining_total)

@app.route('/lease/new', methods=['GET', 'POST'])
def create_lease():
    if request.method == 'POST':
        # 1. Lease Details
        lease_number = request.form.get('lease_number')
        
        # Check uniqueness
        if Lease.query.filter_by(lease_number=lease_number).first():
            return "Error: Lease Number already exists.", 400
            
        new_lease = Lease(
            customer_id=request.form.get('customer_id'),
            lease_number=lease_number,
            status=request.form.get('status'),
            interest_rate=float(request.form.get('interest_rate') or 0),
            total_terms=int(request.form.get('total_terms') or 0),
            payment_start_date=datetime.datetime.strptime(request.form.get('payment_start_date'), '%Y-%m-%d').date(),
        )
        
        funding_str = request.form.get('funding_date')
        if funding_str:
            new_lease.funding_date = datetime.datetime.strptime(funding_str, '%Y-%m-%d').date()
            
        # Calculate Last Payment Date
        if new_lease.payment_start_date and new_lease.total_terms:
            from dateutil.relativedelta import relativedelta
            new_lease.last_payment_date = new_lease.payment_start_date + relativedelta(months=new_lease.total_terms)
            
        db.session.add(new_lease)
        db.session.flush() # Get ID
        
        # 2. Financial Info
        fin = FinancialInfo(
            lease_id=new_lease.id,
            capital_cost=float(request.form.get('capital_cost') or 0),
            cap_cost_adjustment=float(request.form.get('cap_cost_adjustment') or 0),
            downpayment=float(request.form.get('downpayment') or 0),
            trade_amount=float(request.form.get('trade_amount') or 0),
            net_cap_cost=float(request.form.get('net_cap_cost') or 0),
            monthly_payment=float(request.form.get('monthly_payment') or 0),
            lessee_residual=float(request.form.get('lessee_residual') or 0),
            lessor_residual=float(request.form.get('lessor_residual') or 0),
            security_deposit=float(request.form.get('security_deposit') or 0),
            monthly_depreciation=float(request.form.get('monthly_depreciation') or 0)
        )
        db.session.add(fin)
        
        # 3. Assets
        # Check if lists are present
        years = request.form.getlist('asset_year[]')
        makes = request.form.getlist('asset_make[]')
        vins = request.form.getlist('asset_vin[]')
        costs = request.form.getlist('asset_cost[]')
        
        for i in range(len(years)):
            # Must have at least make or vin to prevent empty rows
            if makes[i] or vins[i]:
                vin = vins[i] or ""
                suffix = vin[-3:] if len(vin) >= 3 else f"{i+1}"
                asset = Asset(
                    lease_id=new_lease.id,
                    asset_id=f"{lease_number}-{suffix}", 
                    year=int(years[i]) if years[i] else 0,
                    make_model=makes[i],
                    vin_serial=vins[i],
                    equipment_cost=float(costs[i]) if costs[i] else 0,
                    status=new_lease.status
                )
                db.session.add(asset)
        
        # 4. Default Payment Step (Rent)
        # Create one step for the entire term
        step = PaymentStep(
            lease_id=new_lease.id,
            start_date=new_lease.payment_start_date,
            amount=fin.monthly_payment,
            frequency='Monthly',
            number_of_payments=new_lease.total_terms,
            type='Rent'
        )
        db.session.add(step)
        
        db.session.commit()
        return redirect(url_for('lease_detail', id=new_lease.id))

    # GET
    customers = Customer.query.order_by(Customer.company_name, Customer.last_name).all()
    return render_template('create_lease.html', customers=customers)

@app.route('/lease/<int:id>/edit', methods=['GET', 'POST'])
def edit_lease(id):
    lease = Lease.query.get_or_404(id)
    
    if request.method == 'POST':
        # 1. Update Lease Basics
        lease.status = request.form.get('status')
        lease.interest_rate = request.form.get('interest_rate')
        
        start_date_str = request.form.get('payment_start_date')
        if start_date_str:
             lease.payment_start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        funding_date_str = request.form.get('funding_date')
        if funding_date_str:
             lease.funding_date = datetime.datetime.strptime(funding_date_str, '%Y-%m-%d').date()
             
        lease.total_terms = int(request.form.get('total_terms'))
        
        # 2. Update Financial Info
        if not lease.financial_info:
            lease.financial_info = FinancialInfo(lease_id=lease.id)
            db.session.add(lease.financial_info)
            
        lease.financial_info.net_cap_cost = float(request.form.get('net_cap_cost') or 0)
        lease.financial_info.monthly_payment = float(request.form.get('monthly_payment') or 0)
        lease.financial_info.lessee_residual = float(request.form.get('lessee_residual') or 0)
        lease.financial_info.purchase_option = float(request.form.get('purchase_option') or 0)
        
        # 3. Handle Payment Schedule (Full Replacement Strategy)
        # Delete existing schedule and steps
        LeasePaymentSchedule.query.filter_by(lease_id=lease.id).delete()
        PaymentStep.query.filter_by(lease_id=lease.id).delete()
        
        # Recreate from Form Data
        sched_dates = request.form.getlist('sched_date[]')
        sched_amounts = request.form.getlist('sched_amount[]')
        sched_types = request.form.getlist('sched_type[]')
        
        # Temp list to hold rows for step condensation
        temp_rows = []
        
        for i in range(len(sched_dates)):
            if sched_dates[i] and sched_amounts[i]:
                p_date = datetime.datetime.strptime(sched_dates[i], '%Y-%m-%d').date()
                p_amount = float(sched_amounts[i])
                p_type = sched_types[i]
                
                # SKIP Residuals (They are handled dynamically via FinancialInfo)
                if p_type == 'Residual':
                    continue
                
                # Save to Legacy Table (for now, or UI compatibility)
                new_payment = LeasePaymentSchedule(
                    lease_id=lease.id,
                    payment_date=p_date,
                    amount=p_amount,
                    period_number=i + 1,
                    type=p_type
                )
                db.session.add(new_payment)
                
                temp_rows.append({
                    'date': p_date,
                    'amount': p_amount,
                    'type': p_type
                })

        # Condense into PaymentSteps
        from dateutil.relativedelta import relativedelta
        if temp_rows:
            # Sort by date
            temp_rows.sort(key=lambda x: x['date'])
            
            current_step = None
            steps = []
            
            for row in temp_rows:
                is_gap = False
                if current_step:
                    expected_next = current_step['start_date'] + relativedelta(months=current_step['count'])
                    if row['date'] != expected_next:
                        is_gap = True
                
                if (current_step is None or 
                    abs(row['amount'] - current_step['amount']) > 0.01 or 
                    row['type'] != current_step['type'] or 
                    is_gap):
                    
                    if current_step:
                        steps.append(current_step)
                    
                    current_step = {
                        'start_date': row['date'],
                        'amount': row['amount'],
                        'type': row['type'],
                        'count': 1
                    }
                else:
                    current_step['count'] += 1
            
            if current_step:
                steps.append(current_step)
                
            for s in steps:
                step_obj = PaymentStep(
                    lease_id=lease.id,
                    start_date=s['start_date'],
                    amount=s['amount'],
                    frequency='Monthly',
                    number_of_payments=s['count'],
                    type=s['type']
                )
                db.session.add(step_obj)

        # 4. Recalculate Last Payment Date

        # 4. Recalculate Last Payment Date
        if lease.payment_start_date and lease.total_terms:
            from dateutil.relativedelta import relativedelta
            lease.last_payment_date = lease.payment_start_date + relativedelta(months=lease.total_terms)

        db.session.commit()
        return redirect(url_for('lease_detail', id=lease.id))
    
    
    # GET: Load Schedule sorted by Date
    schedule = LeasePaymentSchedule.query.filter_by(lease_id=id).order_by(LeasePaymentSchedule.payment_date).all()
    
    # Validation: If schedule is empty (e.g. new lease or cleared), generate from current settings
    if not schedule:
        _, generated_payments = generate_cash_flows(lease)
        # Convert to object-like structure for template
        schedule = []
        for p in generated_payments:
             # Skip Residuals for the Schedule Table (they are in Financial Info)
             if p['type'] == 'Residual':
                 continue
                 
             schedule.append({
                 'payment_date': p['payment_date'],
                 'amount': p['amount'],
                 'type': p['type']
             })
    
    return render_template('edit_lease.html', lease=lease, schedule=schedule)

@app.route('/asset/<int:id>', methods=['GET', 'POST'])
def asset_detail(id):
    asset = Asset.query.get_or_404(id)
    
    if request.method == 'POST':
        old_status = asset.status
        
        asset.year = int(request.form.get('year') or 0)
        asset.make_model = request.form.get('make_model')
        asset.vin_serial = request.form.get('vin_serial')
        asset.equipment_cost = float(request.form.get('equipment_cost') or 0)
        new_status = request.form.get('status')
        asset.status = new_status
        
        # --- Automated Financial Update Logic ---
        # If status changed from ACTV to something else (SOLD, STCK, CANC)
        if old_status == 'ACTV' and new_status != 'ACTV':
            lease = Lease.query.get(asset.lease_id)
            if lease and lease.financial_info:
                # 1. Verify we have other active assets to calculate ratio against "Total Active BEFORE this removal"
                # Actually, simply: Ratio = This Asset Cost / Sum of All Active Assets (Before Removal)
                # But 'status' is already updated in object? No, not committed.
                
                # Fetch all currently active assets (including this one, effectively)
                active_assets = [a for a in lease.assets if a.status == 'ACTV']
                total_active_cost = sum(a.equipment_cost for a in active_assets)
                
                if total_active_cost > 0:
                    removal_ratio = asset.equipment_cost / total_active_cost
                    
                    # 2. Calculate Removal Amounts
                    remove_cap = lease.financial_info.net_cap_cost * removal_ratio
                    remove_pmt = lease.financial_info.monthly_payment * removal_ratio
                    remove_res = lease.financial_info.lessee_residual * removal_ratio
                    
                    # 3. Log Inactive Asset
                    log = InactiveAssetLog(
                        asset_id=asset.id,
                        lease_id=lease.id,
                        date_removed=datetime.date.today(),
                        original_cost=asset.equipment_cost,
                        removed_net_cap_cost=remove_cap,
                        removed_monthly_payment=remove_pmt,
                        removed_residual=remove_res
                    )
                    db.session.add(log)
                    
                    # 4. Reduce Lease Financials
                    lease.financial_info.net_cap_cost -= remove_cap
                    lease.financial_info.monthly_payment -= remove_pmt
                    lease.financial_info.lessee_residual -= remove_res
                    if lease.financial_info.purchase_option:
                        lease.financial_info.purchase_option -= (lease.financial_info.purchase_option * removal_ratio)
                        
                    # 5. Reduce Future Schedule
                    today = datetime.date.today()
                    future_schedules = LeasePaymentSchedule.query.filter(
                        LeasePaymentSchedule.lease_id == lease.id,
                        LeasePaymentSchedule.payment_date >= today
                    ).all()
                    
                    for sched in future_schedules:
                        sched.amount -= (sched.amount * removal_ratio)
                        
        db.session.commit()
        return redirect(url_for('lease_detail', id=asset.lease_id))
        
    return render_template('asset_detail.html', asset=asset)

@app.route('/asset/<int:id>/status', methods=['POST'])
def update_asset_status(id):
    asset = Asset.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status:
        asset.status = new_status
        db.session.commit()
    
    # Redirect back to the lease detail page
    return redirect(url_for('lease_detail', id=asset.lease_id))

@app.route('/api/customer-search')
def customer_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    # Search for customers with similar names
    customers = Customer.query.filter(Customer.search_name.contains(query))\
        .order_by(Customer.search_name)\
        .limit(10).all()
        
    results = [{'id': c.id, 'text': f"{c.company_name or ((c.last_name or '') + ', ' + (c.first_name or ''))} ({c.customer_code})"} for c in customers]
    return jsonify(results)

@app.route('/api/customer/create', methods=['POST'])
def create_customer_api():
    data = request.get_json()
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    company_name = data.get('company_name')
    customer_code = data.get('customer_code')
    
    if not customer_code:
        return jsonify({'error': 'Customer Code is required'}), 400
        
    if Customer.query.filter_by(customer_code=customer_code).first():
         return jsonify({'error': 'Customer Code already exists'}), 400

    new_customer = Customer(
        first_name=first_name,
        last_name=last_name,
        company_name=company_name,
        customer_code=customer_code,
        search_name=f"{company_name or ''} {last_name or ''} {first_name or ''} {customer_code}".strip() # Basic search name gen
    )
    db.session.add(new_customer)
    db.session.commit()
    
    # Return formatted for selection
    display_name = f"{new_customer.company_name or ((new_customer.last_name or '') + ', ' + (new_customer.first_name or ''))} ({new_customer.customer_code})"
    
    return jsonify({
        'id': new_customer.id,
        'text': display_name
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=9002, debug=True)
