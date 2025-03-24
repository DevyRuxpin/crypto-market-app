import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room
from models.user import User
from services.binance_service import BinanceService
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

# API Routes
@app.route('/api/prices')
def get_prices():
    """Get all cryptocurrency prices - public endpoint that doesn't require login"""
    try:
        print("Fetching prices from Binance API...")
        prices = BinanceService.get_ticker_prices()
        print(f"Received {len(prices) if prices else 0} ticker prices from Binance")
        
        # If you want to filter to just show a few for debugging
        if prices and len(prices) > 10:
            print("First 5 prices:", prices[:5])
        
        # If no data from API, return mock data
        if not prices or len(prices) == 0:
            print("Using mock data for prices")
            prices = [
                {"symbol": "BTCUSDT", "price": "50000.00"},
                {"symbol": "ETHUSDT", "price": "3000.00"},
                {"symbol": "BNBUSDT", "price": "400.00"},
                {"symbol": "ADAUSDT", "price": "1.20"},
                {"symbol": "SOLUSDT", "price": "150.00"},
                {"symbol": "XRPUSDT", "price": "0.75"},
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
            {"symbol": "ADAUSDT", "price": "1.20"},
            {"symbol": "SOLUSDT", "price": "150.00"},
            {"symbol": "XRPUSDT", "price": "0.75"},
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

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(stream_name):
    print(f"Client {request.sid} subscribing to {stream_name}")
    join_room(stream_name)
    
    # Start appropriate WebSocket stream if needed
    if 'kline_' in stream_name:
        parts = stream_name.split('_')
        if len(parts) == 3:
            symbol = parts[1].upper()
            interval = parts[2]
            ws_service.start_kline_stream(symbol, interval)
    elif stream_name == 'all_tickers':
        ws_service.start_ticker_stream()

@socketio.on('unsubscribe')
def handle_unsubscribe(stream_name):
    print(f"Client {request.sid} unsubscribing from {stream_name}")
    leave_room(stream_name)

# Start the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
