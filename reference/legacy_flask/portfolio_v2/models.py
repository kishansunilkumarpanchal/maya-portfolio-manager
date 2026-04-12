from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

# --- Master Data ---

class Province(db.Model):
    __tablename__ = 'provinces'
    code = db.Column(db.String(10), primary_key=True)  # e.g., "ON", "BC"
    name = db.Column(db.String(100), nullable=False)
    
    customers = db.relationship('Customer', backref='province', lazy=True)

class AssetGroup(db.Model):
    __tablename__ = 'asset_groups'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False) # e.g., "Heavy Machinery"
    
    assets = db.relationship('Asset', backref='group', lazy=True)

class TaxRate(db.Model):
    __tablename__ = 'tax_rates'
    code = db.Column(db.String(20), primary_key=True)
    description = db.Column(db.String(200))
    rate1 = db.Column(db.Float)
    desc1 = db.Column(db.String(50))
    rate2 = db.Column(db.Float)
    desc2 = db.Column(db.String(50))
    rate3 = db.Column(db.Float)
    desc3 = db.Column(db.String(50))

# --- Customer Management ---

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(50), unique=True, nullable=True)
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    company_name = db.Column(db.String(500))
    trade_name = db.Column(db.String(500))
    address1 = db.Column(db.String(200))
    address2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    province_code = db.Column(db.String(10), db.ForeignKey('provinces.code'), nullable=True)
    postal_code = db.Column(db.String(20))
    search_name = db.Column(db.String(200), index=True) # Calculated field for search

    leases = db.relationship('Lease', backref='customer', lazy=True)

# --- Lease & Financials ---

class Lease(db.Model):
    __tablename__ = 'leases'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    lease_number = db.Column(db.String(50), unique=True, nullable=False)
    funding_date = db.Column(db.Date)
    tax_code = db.Column(db.String(20)) # Added field
    payment_start_date = db.Column(db.Date)
    total_terms = db.Column(db.Integer)
    last_payment_date = db.Column(db.Date) # Calculated: start + terms
    interest_rate = db.Column(db.Float)
    status = db.Column(db.String(50))

    financial_info = db.relationship('FinancialInfo', backref='lease', uselist=False, cascade="all, delete-orphan")
    payment_schedule = db.relationship('LeasePaymentSchedule', backref='lease', lazy=True, cascade="all, delete-orphan")
    assets = db.relationship('Asset', backref='lease', lazy=True, cascade="all, delete-orphan")

class FinancialInfo(db.Model):
    __tablename__ = 'financial_info'
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), primary_key=True)
    capital_cost = db.Column(db.Float)
    cap_cost_adjustment = db.Column(db.Float)
    downpayment = db.Column(db.Float)
    trade_amount = db.Column(db.Float)
    net_cap_cost = db.Column(db.Float) # Calculated: cap - adj - down - trade
    lessee_residual = db.Column(db.Float)
    lessor_residual = db.Column(db.Float)
    monthly_depreciation = db.Column(db.Float)
    monthly_payment = db.Column(db.Float)
    security_deposit = db.Column(db.Float)

class LeasePaymentSchedule(db.Model):
    __tablename__ = 'lease_payment_schedules'
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), nullable=False)
    payment_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    period_number = db.Column(db.Integer)
    type = db.Column(db.String(50)) # Rent, Tax, Fee

class PaymentStep(db.Model):
    __tablename__ = 'payment_steps'
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), default='Monthly') # Monthly, One-Time
    number_of_payments = db.Column(db.Integer, default=1)
    type = db.Column(db.String(50)) # Rent, Residual

    lease_rel = db.relationship('Lease', backref=db.backref('payment_steps', lazy=True, cascade="all, delete-orphan"))

class LeasePaymentScheduleVerify(db.Model):
    __tablename__ = 'lease_payment_schedules_verify'
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), nullable=False)
    payment_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    period_number = db.Column(db.Integer)
    type = db.Column(db.String(50)) # Rent, Residual

# --- Assets ---

class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), nullable=False)
    asset_id = db.Column(db.String(50)) # Calculated: Lease # + VIN last 3
    group_id = db.Column(db.Integer, db.ForeignKey('asset_groups.id'), nullable=True)
    year = db.Column(db.Integer)
    make_model = db.Column(db.String(500))
    vin_serial = db.Column(db.String(100))
    finance_source = db.Column(db.String(100))
    equipment_cost = db.Column(db.Float)
    percentage_value = db.Column(db.Float) # Calculated: cost / total lease cost
    status = db.Column(db.String(50))

class InactiveAssetLog(db.Model):
    __tablename__ = 'inactive_asset_logs'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), nullable=False)
    date_removed = db.Column(db.Date)
    original_cost = db.Column(db.Float)
    removed_net_cap_cost = db.Column(db.Float)
    removed_monthly_payment = db.Column(db.Float)
    removed_residual = db.Column(db.Float)
