import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room
from models.user import User
from models.portfolio import Portfolio, PortfolioItem
from models.alert import Alert
from services.binance_service import BinanceService
from services.coinmarketcap_service import CoinMarketCapService
from services.websocket_service import WebSocketService

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key-for-testing')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")
ws_service = WebSocketService(socketio)

# Initialize services
coinmarketcap_service = CoinMarketCapService(api_key=os.environ.get('CMC_API_KEY', 'bda79d78-5f5c-41c3-892e-3584b698e234'))

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # In a real app, you would load the user from a database
    if user_id in User.users:
        return User.users[user_id]
    return None

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
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.find_by_email(email)
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash('Login successful!')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if User.find_by_email(email):
            flash('Email already registered')
            return render_template('signup.html')
            
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('signup.html')
            
        password_hash = generate_password_hash(password)
        user = User(name=name, email=email, password_hash=password_hash)
        login_user(user)
        flash('Account created successfully!')
        return redirect(url_for('dashboard'))
        
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
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
        print("Fetching prices from Binance API...")
        all_prices = BinanceService.get_ticker_prices()
        print(f"Received {len(all_prices) if all_prices else 0} ticker prices from Binance")
        
        # Filter to only show USD pairs and major currencies
        major_coins = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'LINK', 'MATIC', 'UNI', 'LTC']
        
        if all_prices:
            # Filter to only show USDT pairs and major coins
            filtered_prices = [p for p in all_prices if p['symbol'].endswith('USDT') and any(p['symbol'].startswith(coin) for coin in major_coins)]
            
            # Sort by market cap (using symbol as proxy for now)
            filtered_prices.sort(key=lambda x: major_coins.index(next((coin for coin in major_coins if x['symbol'].startswith(coin)), 'ZZZ')) if any(x['symbol'].startswith(coin) for coin in major_coins) else 999)
            
            print(f"Filtered to {len(filtered_prices)} major USD pairs")
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
        # Return mock data in case of any error
        return jsonify([
            {"symbol": "BTCUSDT", "price": "50000.00"},
            {"symbol": "ETHUSDT", "price": "3000.00"},
            {"symbol": "BNBUSDT", "price": "400.00"},
            {"symbol": "XRPUSDT", "price": "0.75"},
            {"symbol": "ADAUSDT", "price": "1.20"},
            {"symbol": "SOLUSDT", "price": "150.00"},
            {"symbol": "DOTUSDT", "price": "20.00"},
            {"symbol": "DOGEUSDT", "price": "0.15"}
        ])

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
    portfolio = Portfolio.get_by_user_id(user_id)
    
    if not portfolio:
        # Create empty portfolio if it doesn't exist
        portfolio = Portfolio(user_id=user_id)
    
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
    purchase_date = data.get('purchase_date', datetime.now().isoformat())
    
    if not symbol or quantity <= 0 or purchase_price <= 0:
        return jsonify({"error": "Invalid input data"}), 400
    
    user_id = current_user.id
    portfolio = Portfolio.get_by_user_id(user_id)
    
    if not portfolio:
        portfolio = Portfolio(user_id=user_id)
    
    # Add new item
    invested = quantity * purchase_price
    item = PortfolioItem(
        symbol=symbol,
        quantity=quantity,
        purchase_price=purchase_price,
        purchase_date=purchase_date,
        invested=invested
    )
    
    portfolio.add_item(item)
    
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
    portfolio = Portfolio.get_by_user_id(user_id)
    
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
    portfolio = Portfolio.get_by_user_id(user_id)
    
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
    alerts = Alert.get_by_user_id(user_id)
    
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
                    alert.triggered = True
                    alert.triggered_at = datetime.now().iso

