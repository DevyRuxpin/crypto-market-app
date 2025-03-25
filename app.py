import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import uuid
from forms import LoginForm  # Ensure you import your form class
from models import User, db  # Ensure this matches the updated models module
from flask_caching import Cache

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Add caching configuration
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)

# Fix PostgreSQL connection string if needed (for Render)
database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
if (database_url and database_url.startswith('postgres://')):
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)

# Initialize SQLAlchemy
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Template context processor
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('signup.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
            
        password_hash = generate_password_hash(password)
        user = User(
            id=str(uuid.uuid4()),
            name=name, 
            email=email, 
            password_hash=password_hash
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create default portfolio and watchlist
        default_portfolio = Portfolio(user_id=user.id)
        default_watchlist = Watchlist(user_id=user.id)
        
        db.session.add(default_portfolio)
        db.session.add(default_watchlist)
        db.session.commit()
        
        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/crypto/<symbol>')
@login_required
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

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# API Routes
@app.route('/api/prices')
def get_prices():
    try:
        # Check cache first
        cached_prices = cache.get('prices')
        if cached_prices:
            return jsonify(cached_prices)

        print("Fetching prices from Binance API...")
        all_prices = BinanceService.get_ticker_prices()
        print(f"Received {len(all_prices) if all_prices else 0} ticker prices from Binance")
        
        # Filter to only show USD pairs and major currencies
        major_coins = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'LINK', 'MATIC', 'UNI', 'LTC']
        
        if all_prices:
            filtered_prices = filter_and_sort_prices(all_prices, major_coins)
            cache.set('prices', filtered_prices)  # Cache the filtered prices
            return jsonify(filtered_prices)
        
        # If no data from API, return mock data
        print("Using mock data for prices")
        prices = [
            {"symbol": "BTCUSDT", "price": "50000.00"},
            {"symbol": "ETHUSDT", "price": "3000.00"},
            {"symbol": "BNBUSDT", "price": "400.00"},
            {"symbol": "XRPUSDT", "price": "0.75"},
            {"symbol": "ADAUSDT", "price": "1.20"},
            {"symbol": "SOLUSDT", "price": "150.00"},
            {"symbol": "DOTUSDT", "price": "20.00"},
            {"symbol": "DOGEUSDT", "price": "0.15"}
        ]
        
        return jsonify(prices)
    except Exception as e:
        print(f"Error in get_prices: {e}")
        return jsonify({"error": "Failed to fetch prices"}), 500

def filter_and_sort_prices(prices, major_coins):
    # Abstracted filtering and sorting logic
    filtered = [p for p in prices if p['symbol'].endswith('USDT') and any(p['symbol'].startswith(coin) for coin in major_coins)]
    filtered.sort(key=lambda x: major_coins.index(next((coin for coin in major_coins if x['symbol'].startswith(coin)), 'ZZZ')))
    return filtered

@app.route('/api/klines/<symbol>')
@login_required
def get_klines(symbol):
    interval = request.args.get('interval', '1d')
    limit = int(request.args.get('limit', '100'))
    
    klines = BinanceService.get_klines(symbol, interval, limit)
    return jsonify(klines)

@app.route('/api/ticker/<symbol>')
@login_required
def get_ticker(symbol):
    ticker = BinanceService.get_ticker_24hr(symbol)
    return jsonify(ticker)

@app.route('/api/symbol-info/<symbol>')
@login_required
def get_symbol_info(symbol):
    info = BinanceService.get_exchange_info(symbol)
    return jsonify(info)

@app.route('/api/depth/<symbol>')
@login_required
def get_market_depth(symbol):
    limit = int(request.args.get('limit', '100'))
    depth = BinanceService.get_market_depth(symbol, limit)
    return jsonify(depth)

@app.route('/api/technical/rsi/<symbol>')
@login_required
def get_rsi(symbol):
    period = int(request.args.get('period', '14'))
    interval = request.args.get('interval', '1d')
    
    klines = BinanceService.get_klines(symbol, interval, period * 2 + 1)
    if not klines:
        return jsonify({"rsi": None})
        
    prices = [k['close'] for k in klines]
    rsi = BinanceService.calculate_rsi(prices, period)
    
    return jsonify({"rsi": rsi})

@app.route('/api/technical/ma/<symbol>')
@login_required
def get_moving_averages(symbol):
    interval = request.args.get('interval', '1d')
    
    klines = BinanceService.get_klines(symbol, interval, 100)
    if not klines:
        return jsonify({
            "sma20": None,
            "sma50": None,
            "ema12": None,
            "ema26": None
        })
        
    prices = [k['close'] for k in klines]
    
    sma20 = BinanceService.calculate_moving_average(prices, 20)
    sma50 = BinanceService.calculate_moving_average(prices, 50)
    ema12 = BinanceService.calculate_ema(prices, 12)
    ema26 = BinanceService.calculate_ema(prices, 26)
    
    return jsonify({
        "sma20": sma20,
        "sma50": sma50,
        "ema12": ema12,
        "ema26": ema26
    })

# Portfolio API endpoints
@app.route('/api/portfolio', methods=['GET'])
@login_required
def get_portfolio():
    user_id = current_user.id
    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    
    if not portfolio:
        # Create empty portfolio if it doesn't exist
        portfolio = Portfolio(user_id=user_id)
        db.session.add(portfolio)
        db.session.commit()
    
    # Get current prices for portfolio items
    portfolio_data = portfolio.to_dict()
    
    # Calculate total value and performance metrics
    if portfolio_data["items"]:
        current_prices = {}
        for item in portfolio_data["items"]:
            symbol = f"{item['symbol']}USDT"
            price_data = BinanceService.get_ticker_price(symbol)
            if price_data:
                current_prices[item['symbol']] = float(price_data['price'])
            else:
                current_prices[item['symbol']] = 0
                
            # Update current price and calculate values
            item['current_price'] = current_prices[item['symbol']]
            item['current_value'] = item['current_price'] * item['quantity']
            item['profit_loss'] = item['current_value'] - item['invested']
            item['profit_loss_percent'] = (item['profit_loss'] / item['invested'] * 100) if item['invested'] > 0 else 0
            
        # Calculate portfolio totals
        portfolio_data['total_invested'] = sum(item['invested'] for item in portfolio_data['items'])
        portfolio_data['total_current_value'] = sum(item['current_value'] for item in portfolio_data['items'])
        portfolio_data['total_profit_loss'] = portfolio_data['total_current_value'] - portfolio_data['total_invested']
        portfolio_data['total_profit_loss_percent'] = (portfolio_data['total_profit_loss'] / portfolio_data['total_invested'] * 100) if portfolio_data['total_invested'] > 0 else 0
    
    return jsonify(portfolio_data)

@app.route('/api/portfolio/add', methods=['POST'])
@login_required
def add_portfolio_item():
    data = request.json
    symbol = data.get('symbol', '').upper()
    quantity = float(data.get('quantity', 0))
    purchase_price = float(data.get('purchase_price', 0))
    purchase_date_str = data.get('purchase_date', datetime.now().isoformat())
    
    # Parse purchase date
    try:
        purchase_date = datetime.fromisoformat(purchase_date_str)
    except ValueError:
        purchase_date = datetime.now()
    
    if not symbol or quantity <= 0 or purchase_price <= 0:
        return jsonify({"error": "Invalid input data"}), 400
    
    user_id = current_user.id
    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    
    if not portfolio:
        portfolio = Portfolio(user_id=user_id)
        db.session.add(portfolio)
        db.session.commit()
    
    # Add new item
    invested = quantity * purchase_price
    item = PortfolioItem(
        portfolio_id=portfolio.id,
        symbol=symbol,
        quantity=quantity,
        purchase_price=purchase_price,
        purchase_date=purchase_date,
        invested=invested
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Portfolio item added successfully"})

@app.route('/api/portfolio/update/<item_id>', methods=['PUT'])
@login_required
def update_portfolio_item(item_id):
    data = request.json
    quantity = float(data.get('quantity', 0))
    purchase_price = float(data.get('purchase_price', 0))
    
    if quantity <= 0 or purchase_price <= 0:
        return jsonify({"error": "Invalid input data"}), 400
    
    user_id = current_user.id
    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404
    
    # Update the item
    invested = quantity * purchase_price
    success = portfolio.update_item(item_id, quantity, purchase_price, invested)
    
    if not success:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify({"success": True, "message": "Portfolio item updated successfully"})

@app.route('/api/portfolio/delete/<item_id>', methods=['DELETE'])
@login_required
def delete_portfolio_item(item_id):
    user_id = current_user.id
    portfolio = Portfolio.query.filter_by(user_id=user_id).first()
    
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404
    
    success = portfolio.remove_item(item_id)
    
    if not success:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify({"success": True, "message": "Portfolio item deleted successfully"})

# Price alerts API endpoints
@app.route('/api/alerts', methods=['GET'])
@login_required
def get_alerts():
    user_id = current_user.id
    alerts = Alert.query.filter_by(user_id=user_id).all()
    
    # Check if any alerts have been triggered
    if alerts:
        for alert in alerts:
            symbol = f"{alert.symbol}USDT"
            price_data = BinanceService.get_ticker_price(symbol)
            
            if price_data:
                current_price = float(price_data['price'])
                
                # Check if alert conditions are met
                if (alert.alert_type == 'above' and current_price >= alert.target_price) or \
                   (alert.alert_type == 'below' and current_price <= alert.target_price):
                    if not alert.triggered:
                        alert.triggered = True
                        alert.triggered_at = datetime.now()
                        db.session.commit()
    
    return jsonify([alert.to_dict() for alert in alerts])

@app.route('/api/alerts/add', methods=['POST'])
@login_required
def add_alert():
    data = request.json
    symbol = data.get('symbol', '').upper()
    alert_type = data.get('alert_type')  # 'above' or 'below'
    target_price = float(data.get('target_price', 0))
    
    if not symbol or not alert_type or target_price <= 0:
        return jsonify({"error": "Invalid input data"}), 400
    
    user_id = current_user.id
    
    alert = Alert(
        user_id=user_id,
        symbol=symbol,
        alert_type=alert_type,
        target_price=target_price,
        created_at=datetime.now(),
        triggered=False
    )
    
    db.session.add(alert)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Alert added successfully", "alert": alert.to_dict()})

@app.route('/api/alerts/delete/<alert_id>', methods=['DELETE'])
@login_required
def delete_alert(alert_id):
    user_id = current_user.id
    success = Alert.delete(alert_id, user_id)
    
    if not success:
        return jsonify({"error": "Alert not found"}), 404
    
    return jsonify({"success": True, "message": "Alert deleted successfully"})

@app.route('/api/alerts/reset/<alert_id>', methods=['PUT'])
@login_required
def reset_alert(alert_id):
    user_id = current_user.id
    success = Alert.reset(alert_id, user_id)
    
    if not success:
        return jsonify({"error": "Alert not found"}), 404
    
    return jsonify({"success": True, "message": "Alert reset successfully"})

# Watchlist API endpoints
@app.route('/api/watchlists', methods=['GET'])
@login_required
def get_watchlists():
    user_id = current_user.id
    watchlists = Watchlist.query.filter_by(user_id=user_id).all()
    return jsonify([watchlist.to_dict() for watchlist in watchlists])

@app.route('/api/watchlists/<watchlist_id>', methods=['GET'])
@login_required
def get_watchlist(watchlist_id):
    watchlist = Watchlist.query.get(watchlist_id)
    
    if not watchlist or watchlist.user_id != current_user.id:
        return jsonify({"error": "Watchlist not found"}), 404
        
    return jsonify(watchlist.to_dict())

@app.route('/api/watchlists', methods=['POST'])
@login_required
def create_watchlist():
    data = request.json
    name = data.get('name', 'New Watchlist')
    
    watchlist = Watchlist(
        user_id=current_user.id,
        name=name
    )
    
    db.session.add(watchlist)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Watchlist created", "watchlist": watchlist.to_dict()})

@app.route('/api/watchlists/<watchlist_id>/symbols', methods=['POST'])
@login_required
def add_to_watchlist(watchlist_id):
    data = request.json
    symbol = data.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400
        
    watchlist = Watchlist.query.get(watchlist_id)
    
    if not watchlist or watchlist.user_id != current_user.id:
        return jsonify({"error": "Watchlist not found"}), 404
        
    success = watchlist.add_symbol(symbol)
    
    if success:
        return jsonify({"success": True, "message": "Symbol added to watchlist"})
    else:
        return jsonify({"error": "Symbol already in watchlist"}), 400

@app.route('/api/watchlists/<watchlist_id>/symbols', methods=['DELETE'])
@login_required
def remove_from_watchlist(watchlist_id):
    data = request.json
    symbol = data.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400
        
    watchlist = Watchlist.query.get(watchlist_id)
    
    if not watchlist or watchlist.user_id != current_user.id:
        return jsonify({"error": "Watchlist not found"}), 404
        
    success = watchlist.remove_symbol(symbol)
    
    if success:
        return jsonify({"success": True, "message": "Symbol removed from watchlist"})
    else:
        return jsonify({"error": "Symbol not found in watchlist"}), 404

# CoinMarketCap API endpoints
@app.route('/api/coinmarketcap/listings')
@login_required
def get_cmc_listings():
    limit = int(request.args.get('limit', '20'))
    sort = request.args.get('sort', 'market_cap')
    sort_dir = request.args.get('sort_dir', 'desc')
    
    try:
        data = CoinMarketCapService.get_latest_listings(limit=limit, sort=sort, sort_dir=sort_dir)
        return jsonify(data)
    except Exception as e:
        print(f"Error in CoinMarketCap API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/coinmarketcap/info')
@login_required
def get_cmc_info():
    symbol = request.args.get('symbol', 'BTC')
    
    try:
        data = CoinMarketCapService.get_metadata(symbol)
        return jsonify(data)
    except Exception as e:
        print(f"Error in CoinMarketCap API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/coinmarketcap/quotes')
@login_required
def get_cmc_quotes():
    symbols = request.args.get('symbols', 'BTC,ETH').split(',')
    
    try:
        data = CoinMarketCapService.get_quotes(symbols)
        return jsonify(data)
    except Exception as e:
        print(f"Error in CoinMarketCap API: {e}")
        return jsonify({"error": str(e)}), 500

# User settings API
@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    return jsonify(current_user.settings)

@app.route('/api/settings', methods=['PUT'])
@login_required
def update_settings():
    data = request.json
    updated_settings = current_user.update_settings(data)
    db.session.commit()
    return jsonify(updated_settings)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if socketio is not None:
    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            print(f"User {current_user.id} connected to WebSocket")
        else:
            print("Anonymous user connected to WebSocket")

    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            print(f"User {current_user.id} disconnected from WebSocket")
        else:
            print("Anonymous user disconnected from WebSocket")

    @socketio.on('subscribe_price')
    def handle_price_subscribe(data):
        symbol = data.get('symbol')
        if symbol:
            join_room(f'price_{symbol}')
            print(f"User subscribed to price updates for {symbol}")

    @socketio.on('unsubscribe_price')
    def handle_price_unsubscribe(data):
        symbol = data.get('symbol')
        if symbol:
            leave_room(f'price_{symbol}')
            print(f"User unsubscribed from price updates for {symbol}")

if __name__ == '__main__':
    if os.environ.get('FLASK_ENV') == 'development' and socketio:
        # In development, use socketio.run
        socketio.run(app, debug=True, host='0.0.0.0')
    else:
        # In production, use regular app.run (gunicorn will handle this)
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
