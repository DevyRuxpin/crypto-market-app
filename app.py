import os
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime
import logging
import pyotp

# Import database and models
from database import db
from models import User, Portfolio, PortfolioItem, Watchlist, WatchlistSymbol, Alert

# Import services
from services.websocket_service import websocket_service
from services.api_service import BinanceService, CoinMarketCapService

# Import forms
from forms import LoginForm, SignupForm, TwoFactorForm

# Import routes
from routes.api import api_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Load default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_for_development_only'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///cryptotracker.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
        SESSION_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
        REMEMBER_COOKIE_HTTPONLY=True
    )
    
    # Load test config if passed
    if test_config:
        app.config.update(test_config)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize database
    db.init_app(app)
    
    # Initialize migrations
    migrate = Migrate(app, db)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # Initialize WebSocket
    websocket_service.init_app(app)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')
   
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                # Check if 2FA is enabled
                if user.two_factor_enabled:
                    session['user_id'] = user.id  # Store user ID for 2FA verification
                    return redirect(url_for('two_factor'))
                
                # No 2FA, proceed with login
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid email or password', 'danger')
                
        return render_template('login.html', form=form)
    
    @app.route('/two-factor', methods=['GET', 'POST'])
    def two_factor():
        # Check if user ID is in session
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        form = TwoFactorForm()
        if form.validate_on_submit():
            user = User.query.get(session['user_id'])
            
            if not user:
                flash('User not found', 'danger')
                return redirect(url_for('login'))
            
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
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid authentication code', 'danger')
        
        return render_template('two_factor.html', form=form)
    
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
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
            return redirect(url_for('login'))
        
        return render_template('signup.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out', 'info')
        return redirect(url_for('login'))
    
    @app.route('/settings/enable-2fa', methods=['GET', 'POST'])
    @login_required
    def enable_2fa():
        # Check if 2FA is already enabled
        if current_user.two_factor_enabled:
            flash('Two-factor authentication is already enabled', 'info')
            return redirect(url_for('settings'))
        
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
                return redirect(url_for('settings'))
            else:
                flash('Invalid authentication code', 'danger')
        
        return render_template('enable_2fa.html', secret=current_user.two_factor_secret, qr_code_uri=provision_uri)
    
    @app.route('/settings/disable-2fa', methods=['POST'])
    @login_required
    def disable_2fa():
        # Check if 2FA is enabled
        if not current_user.two_factor_enabled:
            flash('Two-factor authentication is not enabled', 'info')
            return redirect(url_for('settings'))
        
        # Verify password
        password = request.form.get('password')
        if not check_password_hash(current_user.password_hash, password):
            flash('Invalid password', 'danger')
            return redirect(url_for('settings'))
        
        # Disable 2FA
        current_user.two_factor_enabled = False
        db.session.commit()
        
        flash('Two-factor authentication disabled successfully', 'success')
        return redirect(url_for('settings'))
    
    # Main routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')
    
    @app.route('/crypto/<symbol>')
    def crypto_detail(symbol):
        return render_template('crypto_detail.html', symbol=symbol)
    
    @app.route('/portfolio')
    @login_required
    def portfolio():
        return render_template('portfolio.html')
    
    @app.route('/alerts')
    @login_required
    def alerts():
        return render_template('alerts.html')
    
    @app.route('/watchlist')
    @login_required
    def watchlist():
        return render_template('watchlist.html')
    
    @app.route('/settings')
    @login_required
    def settings():
        return render_template('settings.html', user=current_user)
    
    @app.route('/news')
    def news():
        return render_template('news.html')
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal server error: {e}")
        return render_template('500.html'), 500
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=os.environ.get('FLASK_ENV') == 'development')
