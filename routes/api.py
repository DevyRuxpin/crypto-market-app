# routes/api.py
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from ..models import User, Portfolio, PortfolioItem, Alert, Watchlist, WatchlistSymbol  # Updated to use relative imports
from ..database import db  # Updated to use relative import
from services.api_service import BinanceService, CoinMarketCapService, TechnicalAnalysisService, NewsService
import uuid
from datetime import datetime
import logging

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)



@api_bp.route('/prices', methods=['GET'])
def get_prices():
    """Get all cryptocurrency prices"""
    try:
        prices = BinanceService.get_ticker_prices()
        changes_data = BinanceService.get_ticker_24hr()
        
        # Create a mapping of symbol to price change percentage
        changes = {}
        if changes_data:
            for item in changes_data:
                changes[item['symbol']] = float(item['priceChangePercent'])
        
        # Combine prices with change data
        result = []
        for price_item in prices:
            symbol = price_item['symbol']
            if symbol.endswith('USDT'):
                result.append({
                    'symbol': symbol,
                    'price': float(price_item['price']),
                    'price_change_24h': changes.get(symbol, 0)
                })
        
        # Sort by market cap (approximated by price * volume)
        result.sort(key=lambda x: x['price_change_24h'], reverse=True)
        
        return jsonify(result[:100])  # Limit to top 100 for performance
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        return jsonify({'error': 'Failed to fetch prices'}), 500




@api_bp.route('/klines/<symbol>', methods=['GET'])
def get_klines(symbol):
    """Get candlestick data for a symbol"""
    try:
        interval = request.args.get('interval', '1d')
        limit = int(request.args.get('limit', 100))
        
        klines = BinanceService.get_klines(symbol, interval=interval, limit=limit)
        
        return jsonify(klines)
    except Exception as e:
        logger.error(f"Error fetching klines for {symbol}: {e}")
        return jsonify({'error': f'Failed to fetch klines for {symbol}'}), 500

@api_bp.route('/depth/<symbol>', methods=['GET'])
def get_depth(symbol):
    """Get order book data for a symbol"""
    try:
        limit = int(request.args.get('limit', 100))
        
        depth = BinanceService.get_depth(symbol, limit=limit)
        
        return jsonify(depth)
    except Exception as e:
        logger.error(f"Error fetching depth for {symbol}: {e}")
        return jsonify({'error': f'Failed to fetch depth for {symbol}'}), 500

@api_bp.route('/indicators/<symbol>', methods=['GET'])
def get_indicators(symbol):
    """Get technical indicators for a symbol"""
    try:
        interval = request.args.get('interval', '1d')
        
        indicators = TechnicalAnalysisService.get_technical_indicators(symbol, interval=interval)
        
        return jsonify(indicators)
    except Exception as e:
        logger.error(f"Error calculating indicators for {symbol}: {e}")
        return jsonify({'error': f'Failed to calculate indicators for {symbol}'}), 500

@api_bp.route('/news', methods=['GET'])
def get_news():
    """Get cryptocurrency news"""
    try:
        limit = int(request.args.get('limit', 10))
        
        news = NewsService.get_crypto_news(limit=limit)
        
        return jsonify(news)
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return jsonify({'error': 'Failed to fetch news'}), 500

@api_bp.route('/news/<coin>', methods=['GET'])
def get_coin_news(coin):
    """Get news for a specific cryptocurrency"""
    try:
        limit = int(request.args.get('limit', 10))
        
        news = NewsService.get_coin_specific_news(coin, limit=limit)
        
        return jsonify(news)
    except Exception as e:
        logger.error(f"Error fetching news for {coin}: {e}")
        return jsonify({'error': f'Failed to fetch news for {coin}'}), 500

@api_bp.route('/portfolio', methods=['GET'])
@login_required
def get_portfolio():
    """Get user's portfolio"""
    try:
        # Get user's active portfolio
        portfolio = Portfolio.query.filter_by(user_id=current_user.id, is_active=True).first()
        
        if not portfolio:
            # Create a new portfolio if none exists
            portfolio = Portfolio(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                name="My Portfolio",
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(portfolio)
            db.session.commit()
            
            return jsonify({
                'id': portfolio.id,
                'name': portfolio.name,
                'items': [],
                'total_invested': 0,
                'total_current_value': 0,
                'total_profit_loss': 0,
                'total_profit_loss_percent': 0
            })
        
        # Get current prices for all assets
        all_prices = {item['symbol']: float(item['price']) for item in BinanceService.get_ticker_prices()}
        
        # Calculate portfolio values
        items = []
        total_invested = 0
        total_current_value = 0
        
        for item in portfolio.items:
            # Skip deleted items
            if item.is_deleted:
                continue
                
            symbol = item.symbol
            quantity = item.quantity
            purchase_price = item.purchase_price
            
            # Get current price
            current_price = all_prices.get(symbol, 0)
            
            # Calculate values
            invested = quantity * purchase_price
            current_value = quantity * current_price
            
            # Add to totals
            total_invested += invested
            total_current_value += current_value
            
            # Add item data
            items.append({
                'id': item.id,
                'symbol': symbol,
                'quantity': quantity,
                'purchase_price': purchase_price,
                'purchase_date': item.purchase_date.isoformat(),
                'current_price': current_price,
                'invested': invested,
                'current_value': current_value
            })
        
        # Calculate profit/loss
        total_profit_loss = total_current_value - total_invested
        total_profit_loss_percent = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        return jsonify({
            'id': portfolio.id,
            'name': portfolio.name,
            'items': items,
            'total_invested': total_invested,
            'total_current_value': total_current_value,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_percent': total_profit_loss_percent
        })
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        return jsonify({'error': 'Failed to fetch portfolio'}), 500

@api_bp.route('/portfolio/add', methods=['POST'])
@login_required
def add_portfolio_item():
    """Add item to portfolio"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['symbol', 'quantity', 'purchase_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get user's active portfolio
        portfolio = Portfolio.query.filter_by(user_id=current_user.id, is_active=True).first()
        
        if not portfolio:
            # Create a new portfolio if none exists
            portfolio = Portfolio(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                name="My Portfolio",
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(portfolio)
            db.session.commit()
        
        # Create new portfolio item
        purchase_date = datetime.fromisoformat(data.get('purchase_date', datetime.utcnow().isoformat()))
        
        item = PortfolioItem(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio.id,
            symbol=data['symbol'],
            quantity=data['quantity'],
            purchase_price=data['purchase_price'],
            purchase_date=purchase_date,
            created_at=datetime.utcnow()
        )
        
        db.session.add(item)
        db.session.commit()
        
        return jsonify({'success': True, 'id': item.id})
    except Exception as e:
        logger.error(f"Error adding portfolio item: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to add portfolio item'}), 500

@api_bp.route('/portfolio/item/<item_id>', methods=['GET'])
@login_required
def get_portfolio_item(item_id):
    """Get portfolio item details"""
    try:
        # Get portfolio item
        item = PortfolioItem.query.filter_by(id=item_id).first()
        
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        # Check ownership
        portfolio = Portfolio.query.filter_by(id=item.portfolio_id).first()
        if not portfolio or portfolio.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'id': item.id,
            'symbol': item.symbol,
            'quantity': item.quantity,
            'purchase_price': item.purchase_price,
            'purchase_date': item.purchase_date.isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching portfolio item: {e}")
        return jsonify({'error': 'Failed to fetch portfolio item'}), 500

@api_bp.route('/portfolio/update/<item_id>', methods=['PUT'])
@login_required
def update_portfolio_item(item_id):
    """Update portfolio item"""
    try:
        data = request.json
        
        # Get portfolio item
        item = PortfolioItem.query.filter_by(id=item_id).first()
        
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        # Check ownership
        portfolio = Portfolio.query.filter_by(id=item.portfolio_id).first()
        if not portfolio or portfolio.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Update fields
        if 'quantity' in data:
            item.quantity = data['quantity']
        
        if 'purchase_price' in data:
            item.purchase_price = data['purchase_price']
        
        if 'purchase_date' in data:
            item.purchase_date = datetime.fromisoformat(data['purchase_date'])
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating portfolio item: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update portfolio item'}), 500

@api_bp.route('/portfolio/delete/<item_id>', methods=['DELETE'])
@login_required
def delete_portfolio_item(item_id):
    """Delete portfolio item"""
    try:
        # Get portfolio item
        item = PortfolioItem.query.filter_by(id=item_id).first()
        
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        # Check ownership
        portfolio = Portfolio.query.filter_by(id=item.portfolio_id).first()
        if not portfolio or portfolio.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Soft delete
        item.is_deleted = True
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting portfolio item: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete portfolio item'}), 500

@api_bp.route('/alerts', methods=['GET'])
@login_required
def get_alerts():
    """Get user's price alerts"""
    try:
        alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).all()
        
        result = []
        for alert in alerts:
            result.append({
                'id': alert.id,
                'symbol': alert.symbol,
                'alert_type': alert.alert_type,
                'target_price': alert.target_price,
                'triggered': alert.triggered,
                'created_at': alert.created_at.isoformat(),
                'triggered_at': alert.triggered_at.isoformat() if alert.triggered_at else None
            })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return jsonify({'error': 'Failed to fetch alerts'}), 500

@api_bp.route('/alerts/add', methods=['POST'])
@login_required
def add_alert():
    """Add price alert"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['symbol', 'alert_type', 'target_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate alert type
        if data['alert_type'] not in ['above', 'below']:
            return jsonify({'error': 'Invalid alert type. Must be "above" or "below"'}), 400
        
        # Create new alert
        alert = Alert(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            symbol=data['symbol'],
            alert_type=data['alert_type'],
            target_price=data['target_price'],
            created_at=datetime.utcnow()
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({'success': True, 'id': alert.id})
    except Exception as e:
        logger.error(f"Error adding alert: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to add alert'}), 500

@api_bp.route('/alerts/reset/<alert_id>', methods=['PUT'])
@login_required
def reset_alert(alert_id):
    """Reset triggered alert"""
    try:
        # Get alert
        alert = Alert.query.filter_by(id=alert_id).first()
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        # Check ownership
        if alert.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Reset alert
        alert.triggered = False
        alert.triggered_at = None
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error resetting alert: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to reset alert'}), 500

@api_bp.route('/alerts/delete/<alert_id>', methods=['DELETE'])
@login_required
def delete_alert(alert_id):
    """Delete price alert"""
    try:
        # Get alert
        alert = Alert.query.filter_by(id=alert_id).first()
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        # Check ownership
        if alert.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Delete alert
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete alert'}), 500

@api_bp.route('/watchlists', methods=['GET'])
@login_required
def get_watchlists():
    """Get user's watchlists"""
    try:
        watchlists = Watchlist.query.filter_by(user_id=current_user.id).all()
        
        result = []
        for watchlist in watchlists:
            result.append({
                'id': watchlist.id,
                'name': watchlist.name,
                'created_at': watchlist.created_at.isoformat(),
                'symbol_count': WatchlistSymbol.query.filter_by(watchlist_id=watchlist.id).count()
            })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching watchlists: {e}")
        return jsonify({'error': 'Failed to fetch watchlists'}), 500

@api_bp.route('/watchlists/<watchlist_id>', methods=['GET'])
@login_required
def get_watchlist(watchlist_id):
    """Get watchlist details"""
    try:
        # Get watchlist
        watchlist = Watchlist.query.filter_by(id=watchlist_id).first()
        
        if not watchlist:
            return jsonify({'error': 'Watchlist not found'}), 404
        
        # Check ownership
        if watchlist.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get symbols
        symbols_data = WatchlistSymbol.query.filter_by(watchlist_id=watchlist_id).all()
        symbols = [symbol.symbol for symbol in symbols_data]
        
        # Get current prices and 24hr changes
        all_prices = {}
        all_changes = {}
        
        prices_data = BinanceService.get_ticker_prices()
        changes_data = BinanceService.get_ticker_24hr()
        
        if prices_data:
            for item in prices_data:
                all_prices[item['symbol']] = float(item['price'])
        
        if changes_data:
            for item in changes_data:
                all_changes[item['symbol']] = float(item['priceChangePercent'])
        
        # Prepare result
        symbols_result = []
        for symbol in symbols:
            symbols_result.append({
                'symbol': symbol,
                'price': all_prices.get(symbol, 0),
                'price_change_24h': all_changes.get(symbol, 0)
            })
        
        return jsonify({
            'id': watchlist.id,
            'name': watchlist.name,
            'created_at': watchlist.created_at.isoformat(),
            'symbols': symbols_result
        })
    except Exception as e:
        logger.error(f"Error fetching watchlist: {e}")
        return jsonify({'error': 'Failed to fetch watchlist'}), 500

@api_bp.route('/watchlists/create', methods=['POST'])
@login_required
def create_watchlist():
    """Create new watchlist"""
    try:
        data = request.json
        
        # Validate required fields
        if 'name' not in data:
            return jsonify({'error': 'Missing required field: name'}), 400
        
        # Create watchlist
        watchlist = Watchlist(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            name=data['name'],
            created_at=datetime.utcnow()
        )
        
        db.session.add(watchlist)
        db.session.commit()
        
        return jsonify({'success': True, 'id': watchlist.id})
    except Exception as e:
        logger.error(f"Error creating watchlist: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create watchlist'}), 500

@api_bp.route('/watchlists/add-symbol', methods=['POST'])
@login_required
def add_symbol_to_watchlist():
    """Add symbol to watchlist"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['watchlist_id', 'symbol']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get watchlist
        watchlist = Watchlist.query.filter_by(id=data['watchlist_id']).first()
        
        if not watchlist:
            return jsonify({'error': 'Watchlist not found'}), 404
        
        # Check ownership
        if watchlist.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if symbol already exists in watchlist
        existing_symbol = WatchlistSymbol.query.filter_by(
            watchlist_id=data['watchlist_id'],
            symbol=data['symbol']
        ).first()
        
        if existing_symbol:
            return jsonify({'success': True, 'message': 'Symbol already in watchlist'})
        
        # Add symbol to watchlist
        watchlist_symbol = WatchlistSymbol(
            id=str(uuid.uuid4()),
            watchlist_id=data['watchlist_id'],
            symbol=data['symbol'],
            added_at=datetime.utcnow()
        )
        
        db.session.add(watchlist_symbol)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error adding symbol to watchlist: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to add symbol to watchlist'}), 500

@api_bp.route('/watchlists/remove-symbol', methods=['DELETE'])
@login_required
def remove_symbol_from_watchlist():
    """Remove symbol from watchlist"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['watchlist_id', 'symbol']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get watchlist
        watchlist = Watchlist.query.filter_by(id=data['watchlist_id']).first()
        
        if not watchlist:
            return jsonify({'error': 'Watchlist not found'}), 404
        
        # Check ownership
        if watchlist.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Remove symbol from watchlist
        watchlist_symbol = WatchlistSymbol.query.filter_by(
            watchlist_id=data['watchlist_id'],
            symbol=data['symbol']
        ).first()
        
        if watchlist_symbol:
            db.session.delete(watchlist_symbol)
            db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error removing symbol from watchlist: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to remove symbol from watchlist'}), 500

@api_bp.route('/settings', methods=['GET'])
@login_required
def get_settings():
    """Get user settings"""
    try:
        return jsonify(current_user.settings)
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return jsonify({'error': 'Failed to fetch settings'}), 500

@api_bp.route('/settings', methods=['PUT'])
@login_required
def update_settings():
    """Update user settings"""
    try:
        data = request.json
        
        # Update settings
        updated_settings = current_user.update_settings(data)
        db.session.commit()
        
        return jsonify(updated_settings)
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update settings'}), 500
