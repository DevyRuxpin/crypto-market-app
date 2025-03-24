from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_migrate import Migrate
from flask_socketio import SocketIO

from models.user import db, User
from services.binance_service import BinanceService
from services.websocket_service import WebSocketService
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize WebSocket service
ws_service = WebSocketService(socketio)

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        'Confirm Password', 
        validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Sign Up')

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid email or password')
    
    return render_template('auth/login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = SignupForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered')
            return redirect(url_for('signup'))
        
        new_user = User(email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('auth/signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/crypto/<symbol>')
@login_required
def crypto_detail(symbol):
    return render_template('crypto_detail.html', symbol=symbol)

# API routes for frontend
@app.route('/api/prices')
@login_required
def get_prices():
    prices = BinanceService.get_ticker_prices()
    # Add logging here
    app.logger.info(f"API/prices returning {len(prices)} items")
    return jsonify(prices)

@app.route('/api/crypto/<symbol>/klines')
@login_required
def get_klines(symbol):
    interval = request.args.get('interval', '1d')
    limit = request.args.get('limit', 100)
    klines = BinanceService.get_klines(symbol, interval, limit)
    
    # Calculate indicators
    if klines:
        closes = [k['close'] for k in klines]
        
        # Calculate RSI
        rsi = BinanceService.calculate_rsi(closes)
        
        # Calculate simple moving averages
        sma_20 = BinanceService.calculate_moving_average(closes, 20)
        sma_50 = BinanceService.calculate_moving_average(closes, 50)
        
        # Calculate EMA
        ema_12 = BinanceService.calculate_ema(closes, 12)
        ema_26 = BinanceService.calculate_ema(closes, 26)
        
        return jsonify({
            'klines': klines,
            'indicators': {
                'rsi': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'ema_12': ema_12,
                'ema_26': ema_26
            }
        })
    
    return jsonify({'klines': [], 'indicators': {}})

@app.route('/api/market-stats')
@login_required
def get_market_stats():
    symbol = request.args.get('symbol')
    stats = BinanceService.get_ticker_24hr(symbol)
    return jsonify(stats)

@app.route('/api/exchange-info')
@login_required
def get_exchange_info():
    symbol = request.args.get('symbol')
    info = BinanceService.get_exchange_info(symbol)
    return jsonify(info)

@app.route('/api/depth')
@login_required
def get_market_depth():
    symbol = request.args.get('symbol')
    limit = request.args.get('limit', 100)
    depth = BinanceService.get_market_depth(symbol, limit)
    return jsonify(depth)

# WebSocket routes
@app.route('/api/stream/start/<symbol>')
@login_required
def start_symbol_stream(symbol):
    interval = request.args.get('interval', '1m')
    success = ws_service.start_kline_stream(symbol, interval)
    return jsonify({'success': success})

@app.route('/api/stream/stop/<symbol>')
@login_required
def stop_symbol_stream(symbol):
    interval = request.args.get('interval', '1m')
    stream_name = f"{symbol.lower()}@kline_{interval}"
    success = ws_service.stop_stream(stream_name)
    return jsonify({'success': success})

@app.route('/api/stream/start/tickers')
@login_required
def start_ticker_stream():
    success = ws_service.start_ticker_stream()
    return jsonify({'success': success})

@app.route('/api/stream/stop/tickers')
@login_required
def stop_ticker_stream():
    success = ws_service.stop_stream("!ticker@arr")
    return jsonify({'success': success})

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle client subscription to a specific symbol"""
    if 'symbol' in data and 'interval' in data:
        symbol = data['symbol']
        interval = data['interval']
        ws_service.start_kline_stream(symbol, interval)

# Create tables and run app
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Use socketio.run instead of app.run
    socketio.run(app, debug=True)
else:
    # For Render deployment
    # gunicorn will import the app and socketio objects
    # The render.yaml file uses: gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:$PORT app:socketio
    pass
