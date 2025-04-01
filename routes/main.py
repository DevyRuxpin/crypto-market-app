from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.portfolio import Portfolio, PortfolioItem
from models.watchlist import Watchlist, WatchlistSymbol
from models.alert import Alert
from services.api_service import CryptoAPIService
from services.binance_service import BinanceService
from services.websocket_service import WebSocketService

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    crypto_api = CryptoAPIService()
    binance_service = BinanceService()
    websocket_service = WebSocketService()

    market_data = crypto_api.get_market_data()
    watchlist = Watchlist.query.filter_by(user_id=current_user.id).first()
    watchlist_symbols = []
    if watchlist:
        watchlist_symbols = [symbol.symbol for symbol in watchlist.symbols]

    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    portfolio_items = []
    if portfolio:
        portfolio_items = PortfolioItem.query.filter_by(portfolio_id=portfolio.id).all()

    alerts = Alert.query.filter_by(user_id=current_user.id).all()

    return render_template('dashboard.html',
                           market_data=market_data,
                           watchlist_symbols=watchlist_symbols,
                           portfolio_items=portfolio_items,
                           alerts=alerts)

@main.route('/portfolio')
@login_required
def portfolio():
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    portfolio_items = []
    if portfolio:
        portfolio_items = PortfolioItem.query.filter_by(portfolio_id=portfolio.id).all()
    return render_template('portfolio.html', portfolio_items=portfolio_items)

@main.route('/watchlist')
@login_required
def watchlist():
    watchlist = Watchlist.query.filter_by(user_id=current_user.id).first()
    watchlist_symbols = []
    if watchlist:
        watchlist_symbols = [symbol.symbol for symbol in watchlist.symbols]
    return render_template('watchlist.html', watchlist_symbols=watchlist_symbols)

@main.route('/alerts')
@login_required
def alerts():
    alerts = Alert.query.filter_by(user_id=current_user.id).all()
    return render_template('alerts.html', alerts=alerts)

@main.route('/crypto/<symbol>')
@login_required
def crypto_detail(symbol):
    crypto_api = CryptoAPIService()
    binance_service = BinanceService()

    coin_data = crypto_api.get_coin_data(symbol)
    ticker_data = binance_service.get_ticker_data(symbol)

    return render_template('crypto_detail.html', coin_data=coin_data, ticker_data=ticker_data)

@main.route('/api/binance/ticker')
def binance_ticker():
    symbol = request.args.get('symbol')
    binance_service = BinanceService()
    ticker_data = binance_service.get_ticker_data(symbol)
    return jsonify(ticker_data)

@main.route('/api/coinmarketcap/coins')
def coinmarketcap_coins():
    crypto_api = CryptoAPIService()
    coin_data = crypto_api.get_coin_data()
    return jsonify(coin_data)
