from flask import Flask, render_template, request, redirect, url_for
from models import db, Customer, Lease, FinancialInfo, Asset, LeasePaymentSchedule
from sqlalchemy import func
import os
import datetime

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'portfolio.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super_secret_key_v2'

db.init_app(app)

@app.route('/')
def dashboard():
    # KPI: Total Assets (User requested "Total Leases" to be count of assets)
    total_leases = Asset.query.count()
    
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
            (Customer.company_name.contains(search)) |
            (Customer.last_name.contains(search))
        )
        
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    leases = pagination.items
    
    return render_template('leases.html', leases=leases, pagination=pagination, search=search, status=status)

@app.route('/lease/<int:id>')
def lease_detail(id):
    lease = Lease.query.get_or_404(id)
    
    # Filter for future payments (including today)
    from datetime import date
    future_payments = LeasePaymentSchedule.query.filter(
        LeasePaymentSchedule.lease_id == id,
        LeasePaymentSchedule.payment_date >= date.today()
    ).order_by(LeasePaymentSchedule.payment_date).all()
    
    return render_template('lease_detail.html', lease=lease, future_payments=future_payments)

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
        # Delete existing schedule
        LeasePaymentSchedule.query.filter_by(lease_id=lease.id).delete()
        
        # Recreate from Form Data
        sched_dates = request.form.getlist('sched_date[]')
        sched_amounts = request.form.getlist('sched_amount[]')
        sched_types = request.form.getlist('sched_type[]')
        
        for i in range(len(sched_dates)):
            if sched_dates[i] and sched_amounts[i]:
                p_date = datetime.datetime.strptime(sched_dates[i], '%Y-%m-%d').date()
                p_amount = float(sched_amounts[i])
                p_type = sched_types[i]
                
                new_payment = LeasePaymentSchedule(
                    lease_id=lease.id,
                    payment_date=p_date,
                    amount=p_amount,
                    period_number=i + 1,
                    type=p_type
                )
                db.session.add(new_payment)

        # 4. Recalculate Last Payment Date (based on logic or schedule?)
        # Let's rely on the formula as per verified logic: Start + Terms
        # OR should we take the Max Date from the schedule we just saved?
        # User agreed to "Start + Terms" logic recently. Let's stick to that for the field.
        if lease.payment_start_date and lease.total_terms:
            from dateutil.relativedelta import relativedelta
            lease.last_payment_date = lease.payment_start_date + relativedelta(months=lease.total_terms)

        db.session.commit()
        return redirect(url_for('lease_detail', id=lease.id))
    
    # GET: Load Schedule sorted by Date
    schedule = LeasePaymentSchedule.query.filter_by(lease_id=id).order_by(LeasePaymentSchedule.payment_date).all()
    
    return render_template('edit_lease.html', lease=lease, schedule=schedule)

@app.route('/asset/<int:id>/status', methods=['POST'])
def update_asset_status(id):
    asset = Asset.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status:
        asset.status = new_status
        db.session.commit()
    
    # Redirect back to the lease detail page
    return redirect(url_for('lease_detail', id=asset.lease_id))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=9002, debug=False)
