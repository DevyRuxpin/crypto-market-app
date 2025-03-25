# routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime
import pyotp

from database import db
from models import User, Portfolio, Watchlist, WatchlistSymbol
from forms import LoginForm, SignupForm, TwoFactorForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            # Check if 2FA is enabled
            if user.two_factor_enabled:
                session['user_id'] = user.id  # Store user ID for 2FA verification
                return redirect(url_for('auth.two_factor'))
            
            # No 2FA, proceed with login
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html', form=form)

@auth_bp.route('/two-factor', methods=['GET', 'POST'])
def two_factor():
    # Check if user ID is in session
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    form = TwoFactorForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('auth.login'))
        
        # Verify 2FA code
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(form.code.data):
            # Code is valid, complete login
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Clear session
            session.pop('user_id', None)
            
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid authentication code', 'danger')
    
    return render_template('two_factor.html', form=form)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = SignupForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return render_template('signup.html', form=form)
        
        # Create new user
        new_user = User(
            id=str(uuid.uuid4()),
            name=form.name.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_user)
        
        # Create default portfolio
        default_portfolio = Portfolio(
            id=str(uuid.uuid4()),
            user_id=new_user.id,
            name="My Portfolio",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.session.add(default_portfolio)
        
        # Create default watchlist
        default_watchlist = Watchlist(
            id=str(uuid.uuid4()),
            user_id=new_user.id,
            name="My Watchlist",
            created_at=datetime.utcnow()
        )
        
        db.session.add(default_watchlist)
        
        # Add default symbols to watchlist
        default_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']
        for symbol in default_symbols:
            watchlist_symbol = WatchlistSymbol(
                id=str(uuid.uuid4()),
                watchlist_id=default_watchlist.id,
                symbol=symbol,
                added_at=datetime.utcnow()
            )
            db.session.add(watchlist_symbol)
        
        db.session.commit()
        
        flash('Account created successfully! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('signup.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/settings/enable-2fa', methods=['GET', 'POST'])
@login_required
def enable_2fa():
    # Check if 2FA is already enabled
    if current_user.two_factor_enabled:
        flash('Two-factor authentication is already enabled', 'info')
        return redirect(url_for('main.settings'))
    
    # Generate 2FA secret if not already set
    if not current_user.two_factor_secret:
        current_user.two_factor_secret = pyotp.random_base32()
        db.session.commit()
    
    # Generate QR code
    totp = pyotp.TOTP(current_user.two_factor_secret)
    provision_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Crypto Tracker"
    )
    
    if request.method == 'POST':
        # Verify code
        code = request.form.get('code')
        if totp.verify(code):
            # Enable 2FA
            current_user.two_factor_enabled = True
            db.session.commit()
            
            flash('Two-factor authentication enabled successfully', 'success')
            return redirect(url_for('main.settings'))
        else:
            flash('Invalid authentication code', 'danger')
    
    return render_template('enable_2fa.html', secret=current_user.two_factor_secret, qr_code_uri=provision_uri)

@auth_bp.route('/settings/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    # Check if 2FA is enabled
    if not current_user.two_factor_enabled:
        flash('Two-factor authentication is not enabled', 'info')
        return redirect(url_for('main.settings'))
    
    # Verify password
    password = request.form.get('password')
    if not check_password_hash(current_user.password_hash, password):
        flash('Invalid password', 'danger')
        return redirect(url_for('main.settings'))
    
    # Disable 2FA
    current_user.two_factor_enabled = False
    db.session.commit()
    
    flash('Two-factor authentication disabled successfully', 'success')
    return redirect(url_for('main.settings'))
