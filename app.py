import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Import services
from services.binance_service import BinanceService
from services.websocket_service import WebSocketService
from services.coinmarketcap_service import CoinMarketCapService

# Import models
from models.user import User
from models.portfolio import Portfolio
from models.alert import Alert
from models.watchlist import Watchlist

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-for-testing')
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")
ws_service = WebSocketService(socketio)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Major cryptocurrencies to display by default
DEFAULT_CRYPTOS = [
    "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOT", "DOGE", "MATIC", "LINK", 
    "LTC", "UNI", "ATOM", "AVAX", "SHIB"
]

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Helper function to check if dark mode is enabled
def is_dark_mode():
    return session.get('dark_mode', False)

@app.context_processor
def inject_dark_mode():
    return {'dark_mode': is_dark_mode()}

@app.route('/')
def index():
    """Homepage route"""
    # Get top cryptocurrencies from CoinMarketCap
    try:
        top_cryptos = CoinMarketCapService.get_top_cryptocurrencies(limit=15)
    except Exception as e:
        logger.error(f"Error fetching top cryptocurrencies: {e}")
        top_cryptos = []
    
    # Get global market metrics
    try:
        global_metrics = CoinMarketCapService.get_global_metrics()
    except Exception as e:
        logger.error(f"Error fetching global metrics: {e}")
        global_metrics = None
        
    return render_template('index.html', 
                          top_cryptos=top_cryptos,
                          global_metrics=global_metrics,
                          default_cryptos=DEFAULT_CRYPTOS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.authenticate(email, password)
        if user:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup route"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
            
        if User.get_by_email(email):
            flash('Email already registered', 'danger')
            return render_template('signup.html')
            
        user = User(name, email, password)
        
        # Create default portfolio and watchlist
        Portfolio(user.id, "Default Portfolio")
        Watchlist(user.id, "Default Watchlist")
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route"""
    # Get user portfolios
    portfolios = Portfolio.get_user_portfolios(current_user.id)
    
    # Get user watchlists
    watchlists = Watchlist.get_user_watchlists(current_user.id)
    
    # Get user alerts
    alerts = Alert.get_user_alerts(current_user.id)
    
    # Get top cryptocurrencies
    try:
        top_cryptos = CoinMarketCapService.get_top_cryptocurrencies(limit=10)
    except Exception as e:
        logger.error(f"Error fetching top cryptocurrencies: {e}")
        top_cryptos = []
    
    # Get global market metrics
    try:
        global_metrics = CoinMarketCapService.get_global_metrics()
    except Exception as e:
        logger.error(f"Error fetching global metrics: {e}")
        global_metrics = None
    
    return render_template('dashboard.html',
                          portfolios=portfolios,
                          watchlists=watchlists,
                          alerts=alerts,
                          top_cryptos=top_cryptos,
                          global_metrics=global_metrics)

@app.route('/crypto/<symbol>')
def crypto_detail(symbol):
    """Cryptocurrency detail page"""
    try:
        # Get detailed info about the cryptocurrency
        crypto_info = CoinMarketCapService.get_cryptocurrency_details(symbol=symbol)
        
        # Check if user is logged in to show watchlists
        watchlists = []
        if current_user.is_authenticated:
            watchlists = Watchlist.get_user_watchlists(current_user.id)
        
        return render_template('crypto_detail.html', 
                              symbol=symbol,
                              crypto_info=crypto_info,
                              watchlists=watchlists)
    except Exception as e:
        logger.error(f"Error fetching cryptocurrency details: {e}")
        flash('Error loading cryptocurrency details', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/portfolio')
@login_required
def portfolio():
    """Portfolio management page"""
    portfolios = Portfolio.get_user_portfolios(current_user.id)
    
    # Get cryptocurrency map for adding new holdings
    try:
        crypto_map = CoinMarketCapService.get_cryptocurrency_map()
    except Exception as e:
        logger.error(f"Error fetching cryptocurrency map: {e}")
        crypto_map = []
    
    return render_template('portfolio.html', 
                          portfolios=portfolios,
                          crypto_map=crypto_map)

@app.route('/alerts')
@login_required
def alerts():
    """Price alerts management page"""
    user_alerts = Alert.get_user_alerts(current_user.id)
    
    # Get cryptocurrency map for adding new alerts
    try:
        crypto_map = CoinMarketCapService.get_cryptocurrency_map()
    except Exception as e:
        logger.error(f"Error fetching cryptocurrency map: {e}")
        crypto_map = []
    
    return render_template('alerts.html', 
                          alerts=user_alerts,
                          crypto_map=crypto_map)

@app.route('/watchlist')
@login_required
def watchlist():
    """Watchlist management page"""
    watchlists = Watchlist.get_user_watchlists(current_user.id)
    
    # Get cryptocurrency map for adding new symbols
    try:
        crypto_map = CoinMarketCapService.get_cryptocurrency_map()
    except Exception as e:
        logger.error(f"Error fetching cryptocurrency map: {e}")
        crypto_map = []
    
    return render_template('watchlist.html', 
                          watchlists=watchlists,
                          crypto_map=crypto_map)

@app.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('settings.html')

# API Routes
@app.route('/api/prices')
def get_prices():
    """Get all cryptocurrency prices - public endpoint that doesn't require login"""
    try:
        # First try to get prices from Binance
        prices = BinanceService.get_ticker_prices()
        
        # If no data from Binance, try CoinMarketCap
        if not prices or len(prices) == 0:
            cmc_data = CoinMarketCapService.get_top_cryptocurrencies(limit=100)
            prices = []
            for crypto in cmc_data:
                symbol = crypto['symbol'] + 'USDT'  # Format for compatibility
                price = crypto['quote']['USD']['price']
                prices.append({"symbol": symbol, "price": str(price)})
        
        # If still no data, return mock data
        if not prices or len(prices) == 0:
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
        
        # Filter to only show USD pairs by default
        filtered_prices = [p for p in prices if p['symbol'].endswith('USDT')]
        
        return jsonify(filtered_prices)
    except Exception as e:
        logger.error(f"Error in get_prices: {e}")
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

@app.route('/api/portfolio', methods=['GET', 'POST'])
@login_required
def api_portfolio():
    """API endpoint for portfolio management"""
    if request.method == 'GET':
        # Get all user portfolios
        portfolios = Portfolio.get_user_portfolios(current_user.id)
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'created_at': p.created_at.isoformat(),
            'updated_at': p.updated_at.isoformat(),
            'holdings_count': len(p.holdings),
            'performance': p.calculate_performance()
        } for p in portfolios])
    
    elif request.method == 'POST':
        # Create a new portfolio
        data = request.get_json()
        name = data.get('name', 'New Portfolio')
        
        portfolio = Portfolio(current_user.id, name)
        
        return jsonify({
            'id': portfolio.id,
            'name': portfolio.name,
            'created_at': portfolio.created_at.isoformat(),
            'updated_at': portfolio.updated_at.isoformat(),
            'holdings_count': 0,
            'performance': portfolio.calculate_performance()
        }), 201

@app.route('/api/portfolio/<portfolio_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_portfolio_detail(portfolio_id):
    """API endpoint for specific portfolio operations"""
    portfolio = Portfolio.get_portfolio(portfolio_id)
    
    if not portfolio or portfolio.user_id != current_user.id:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    if request.method == 'GET':
        # Get portfolio details
        return jsonify({
            'id': portfolio.id,
            'name': portfolio.name,
            'created_at': portfolio.created_at.isoformat(),
            'updated_at': portfolio.updated_at.isoformat(),
            'holdings': portfolio.holdings,
            'performance': portfolio.calculate_performance()
        })
    
    elif request.method == 'PUT':
        # Update portfolio details
        data = request.get_json()
        if 'name' in data:
            portfolio.name = data['name']
            portfolio.updated_at = datetime.now()
        
        return jsonify({
            'id': portfolio.id,
            'name': portfolio.name,
            'updated_at': portfolio.updated_at.isoformat()
        })
    
    elif request.method == 'DELETE':
        #Delete the portfolio
        if current_user.id in Portfolio.portfolios:
            portfolios = Portfolio.portfolios[current_user.id]
            for i, p in enumerate(portfolios):
                if p.id == portfolio_id:
                    del portfolios[i]
                    return jsonify({'success': True}), 200
        
        return jsonify({'error': 'Portfolio not found'}), 404

@app.route('/api/portfolio/<portfolio_id>/holdings', methods=['GET', 'POST'])
@login_required
def api_portfolio_holdings(portfolio_id):
    """API endpoint for portfolio holdings"""
    portfolio = Portfolio.get_portfolio(portfolio_id)
    
    if not portfolio or portfolio.user_id != current_user.id:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    if request.method == 'GET':
        # Get all holdings in the portfolio
        return jsonify(portfolio.holdings)
    
    elif request.method == 'POST':
        # Add a new holding to the portfolio
        data = request.get_json()
        symbol = data.get('symbol')
        amount = data.get('amount')
        price_per_unit = data.get('price_per_unit')
        date = data.get('date')
        
        if not all([symbol, amount, price_per_unit]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            # Convert date string to datetime if provided
            if date:
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            
            holding = portfolio.add_holding(symbol, amount, price_per_unit, date)
            return jsonify(holding), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/portfolio/<portfolio_id>/holdings/<holding_id>', methods=['PUT', 'DELETE'])
@login_required
def api_portfolio_holding_detail(portfolio_id, holding_id):
    """API endpoint for specific holding operations"""
    portfolio = Portfolio.get_portfolio(portfolio_id)
    
    if not portfolio or portfolio.user_id != current_user.id:
        return jsonify({'error': 'Portfolio not found'}), 404
    
    if request.method == 'PUT':
        # Update a holding
        data = request.get_json()
        amount = data.get('amount')
        price_per_unit = data.get('price_per_unit')
        
        holding = portfolio.update_holding(holding_id, amount, price_per_unit)
        
        if holding:
            return jsonify(holding)
        else:
            return jsonify({'error': 'Holding not found'}), 404
    
    elif request.method == 'DELETE':
        # Remove a holding
        holding = portfolio.remove_holding(holding_id)
        
        if holding:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Holding not found'}), 404

@app.route('/api/alerts', methods=['GET', 'POST'])
@login_required
def api_alerts():
    """API endpoint for alert management"""
    if request.method == 'GET':
        # Get all user alerts
        status = request.args.get('status')
        alerts = Alert.get_user_alerts(current_user.id, status)
        return jsonify([a.to_dict() for a in alerts])
    
    elif request.method == 'POST':
        # Create a new alert
        data = request.get_json()
        symbol = data.get('symbol')
        alert_type = data.get('alert_type')
        target_value = data.get('target_value')
        name = data.get('name')
        
        if not all([symbol, alert_type, target_value]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            alert = Alert(current_user.id, symbol, alert_type, target_value, name)
            return jsonify(alert.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/alerts/<alert_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_alert_detail(alert_id):
    """API endpoint for specific alert operations"""
    alert = Alert.get_alert(alert_id)
    
    if not alert or alert.user_id != current_user.id:
        return jsonify({'error': 'Alert not found'}), 404
    
    if request.method == 'GET':
        # Get alert details
        return jsonify(alert.to_dict())
    
    elif request.method == 'PUT':
        # Update alert details
        data = request.get_json()
        
        if 'status' in data:
            if data['status'] == 'active':
                alert.reactivate()
            elif data['status'] == 'dismissed':
                alert.dismiss()
        
        if 'name' in data:
            alert.name = data['name']
            alert.updated_at = datetime.now()
        
        if 'target_value' in data:
            alert.target_value = float(data['target_value'])
            alert.updated_at = datetime.now()
        
        return jsonify(alert.to_dict())
    
    elif request.method == 'DELETE':
        # Delete the alert
        if current_user.id in Alert.alerts:
            alerts = Alert.alerts[current_user.id]
            for i, a in enumerate(alerts):
                if a.id == alert_id:
                    del alerts[i]
                    return jsonify({'success': True}), 200
        
        return jsonify({'error': 'Alert not found'}), 404

@app.route('/api/watchlists', methods=['GET', 'POST'])
@login_required
def api_watchlists():
    """API endpoint for watchlist management"""
    if request.method == 'GET':
        # Get all user watchlists
        watchlists = Watchlist.get_user_watchlists(current_user.id)
        return jsonify([w.to_dict() for w in watchlists])
    
    elif request.method == 'POST':
        # Create a new watchlist
        data = request.get_json()
        name = data.get('name', 'New Watchlist')
        
        watchlist = Watchlist(current_user.id, name)
        
        return jsonify(watchlist.to_dict()), 201

@app.route('/api/watchlists/<watchlist_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_watchlist_detail(watchlist_id):
    """API endpoint for specific watchlist operations"""
    watchlist = Watchlist.get_watchlist(watchlist_id)
    
    if not watchlist or watchlist.user_id != current_user.id:
        return jsonify({'error': 'Watchlist not found'}), 404
    
    if request.method == 'GET':
        # Get watchlist details
        return jsonify(watchlist.to_dict())
    
    elif request.method == 'PUT':
        # Update watchlist details
        data = request.get_json()
        if 'name' in data:
            watchlist.name = data['name']
            watchlist.updated_at = datetime.now()
        
        return jsonify(watchlist.to_dict())
    
    elif request.method == 'DELETE':
        # Delete the watchlist
        if current_user.id in Watchlist.watchlists:
            watchlists = Watchlist.watchlists[current_user.id]
            for i, w in enumerate(watchlists):
                if w.id == watchlist_id:
                    del watchlists[i]
                    return jsonify({'success': True}), 200
        
        return jsonify({'error': 'Watchlist not found'}), 404

@app.route('/api/watchlists/<watchlist_id>/symbols', methods=['POST', 'DELETE'])
@login_required
def api_watchlist_symbols(watchlist_id):
    """API endpoint for managing symbols in a watchlist"""
    watchlist = Watchlist.get_watchlist(watchlist_id)
    
    if not watchlist or watchlist.user_id != current_user.id:
        return jsonify({'error': 'Watchlist not found'}), 404
    
    if request.method == 'POST':
        # Add a symbol to the watchlist
        data = request.get_json()
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        success = watchlist.add_symbol(symbol)
        
        if success:
            return jsonify(watchlist.to_dict())
        else:
            return jsonify({'error': 'Symbol already in watchlist'}), 400
    
    elif request.method == 'DELETE':
        # Remove a symbol from the watchlist
        data = request.get_json()
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        success = watchlist.remove_symbol(symbol)
        
        if success:
            return jsonify(watchlist.to_dict())
        else:
            return jsonify({'error': 'Symbol not in watchlist'}), 404

@app.route('/api/theme/toggle', methods=['POST'])
def toggle_theme():
    """Toggle between light and dark mode"""
    current = session.get('dark_mode', False)
    session['dark_mode'] = not current
    return jsonify({'dark_mode': session['dark_mode']})

@app.route('/api/coinmarketcap/cryptocurrencies')
def api_cmc_cryptocurrencies():
    """Get cryptocurrency data from CoinMarketCap API"""
    limit = request.args.get('limit', 100, type=int)
    convert = request.args.get('convert', 'USD')
    
    try:
        data = CoinMarketCapService.get_top_cryptocurrencies(limit=limit, convert=convert)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching CoinMarketCap data: {e}")
        return jsonify({'error': 'Failed to fetch cryptocurrency data'}), 500

@app.route('/api/coinmarketcap/global-metrics')
def api_cmc_global_metrics():
    """Get global market metrics from CoinMarketCap API"""
    convert = request.args.get('convert', 'USD')
    
    try:
        data = CoinMarketCapService.get_global_metrics(convert=convert)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching global metrics: {e}")
        return jsonify({'error': 'Failed to fetch global metrics'}), 500

@app.route('/api/coinmarketcap/cryptocurrency/<symbol>')
def api_cmc_cryptocurrency_detail(symbol):
    """Get detailed information about a cryptocurrency from CoinMarketCap API"""
    convert = request.args.get('convert', 'USD')
    
    try:
        data = CoinMarketCapService.get_cryptocurrency_details(symbol=symbol, convert=convert)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching cryptocurrency details: {e}")
        return jsonify({'error': 'Failed to fetch cryptocurrency details'}), 500

@app.route('/api/exchanges')
def api_exchanges():
    """Get cryptocurrency exchanges data"""
    try:
        # Try to get exchanges from Binance first
        exchanges = BinanceService.get_exchange_info()
        
        # If no data, use mock data
        if not exchanges:
            exchanges = [
                {"name": "Binance", "volume_24h": 12500000000},
                {"name": "Coinbase", "volume_24h": 5200000000},
                {"name": "Kraken", "volume_24h": 2800000000},
                {"name": "FTX", "volume_24h": 2100000000},
                {"name": "Huobi", "volume_24h": 1900000000}
            ]
        
        return jsonify(exchanges)
    except Exception as e:
        logger.error(f"Error in get_exchanges: {e}")
        # Return mock data in case of any error
        return jsonify([
            {"name": "Binance", "volume_24h": 12500000000},
            {"name": "Coinbase", "volume_24h": 5200000000},
            {"name": "Kraken", "volume_24h": 2800000000},
            {"name": "FTX", "volume_24h": 2100000000},
            {"name": "Huobi", "volume_24h": 1900000000}
        ])

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection to WebSocket"""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection from WebSocket"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle subscription to cryptocurrency updates"""
    symbol = data.get('symbol')
    interval = data.get('interval', '1m')
    
    if symbol:
        ws_service.subscribe_to_klines(symbol, interval)

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """Handle unsubscription from cryptocurrency updates"""
    symbol = data.get('symbol')
    interval = data.get('interval', '1m')
    
    if symbol:
        ws_service.unsubscribe_from_klines(symbol, interval)

@socketio.on('subscribe_ticker')
def handle_subscribe_ticker():
    """Handle subscription to all market tickers"""
    ws_service.subscribe_to_ticker()

@socketio.on('unsubscribe_ticker')
def handle_unsubscribe_ticker():
    """Handle unsubscription from all market tickers"""
    ws_service.unsubscribe_from_ticker()

# Background task to check price alerts
def check_price_alerts():
    """Background task to check if any price alerts should be triggered"""
    # Get all active alerts
    all_alerts = []
    for user_alerts in Alert.alerts.values():
        all_alerts.extend([a for a in user_alerts if a.status == Alert.STATUS_ACTIVE])
    
    if not all_alerts:
        return
    
    # Get current prices for all symbols in alerts
    symbols = set(alert.symbol for alert in all_alerts)
    
    try:
        # Try to get prices from Binance first
        prices = BinanceService.get_ticker_prices()
        price_dict = {p['symbol']: float(p['price']) for p in prices}
        
        # If symbol not in Binance prices, try CoinMarketCap
        missing_symbols = symbols - set(price_dict.keys())
        if missing_symbols:
            for symbol in missing_symbols:
                try:
                    crypto_data = CoinMarketCapService.get_cryptocurrency_details(symbol=symbol)
                    if crypto_data and symbol in crypto_data:
                        price = crypto_data[symbol][0]['quote']['USD']['price']
                        price_dict[symbol] = float(price)
                except Exception as e:
                    logger.error(f"Error getting price for {symbol}: {e}")
        
        # Check each alert
        triggered_alerts = []
        for alert in all_alerts:
            if alert.symbol in price_dict:
                current_price = price_dict[alert.symbol]
                if alert.check_condition(current_price):
                    triggered_alerts.append(alert)
        
            # Emit notifications for triggered alerts
    for alert in triggered_alerts:
        socketio.emit('alert_triggered', alert.to_dict(), room=f"user_{alert.user_id}")
    
    except Exception as e:
        logger.error(f"Error checking price alerts: {e}")

# Schedule the alert checking task to run periodically
def start_background_tasks():
    """Start background tasks"""
    import threading
    import time
    
    def alert_checker():
        while True:
            check_price_alerts()
            time.sleep(60)  # Check alerts every minute
    
    alert_thread = threading.Thread(target=alert_checker)
    alert_thread.daemon = True
    alert_thread.start()

# Join user-specific rooms for real-time notifications
@socketio.on('join_user_room')
def on_join_user_room():
    """Join a room specific to the current user for private notifications"""
    if current_user.is_authenticated:
        room = f"user_{current_user.id}"
        socketio.join_room(room)
        logger.info(f"User {current_user.id} joined room {room}")

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {e}")
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    # Start background tasks
    start_background_tasks()
    
    # Start the Socket.IO server
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)

