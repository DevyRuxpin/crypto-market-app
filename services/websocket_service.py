# services/websocket_service.py
import json
import threading
import time
from flask_socketio import SocketIO, emit, join_room, leave_room
from services.api_service import BinanceService

class WebSocketService:
    """Unified service for handling WebSocket connections"""
    
    def __init__(self, app=None):
        self.socketio = None
        self.active_symbols = set()
        self.running = False
        self.price_thread = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
        self.register_handlers()
        self.start_price_updates()
    
    def register_handlers(self):
        """Register Socket.IO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            print("Client connected")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print("Client disconnected")
        
        @self.socketio.on('subscribe_price')
        def handle_subscribe_price(data):
            symbol = data.get('symbol')
            if symbol:
                self.add_symbol(symbol)
                join_room(f'price_{symbol}')
                print(f"Client subscribed to price updates for {symbol}")
        
        @self.socketio.on('unsubscribe_price')
        def handle_unsubscribe_price(data):
            symbol = data.get('symbol')
            if symbol:
                self.remove_symbol(symbol)
                leave_room(f'price_{symbol}')
                print(f"Client unsubscribed from price updates for {symbol}")
    
    def start_price_updates(self):
        """Start the price update thread"""
        if not self.running:
            self.running = True
            self.price_thread = threading.Thread(target=self._price_update_loop)
            self.price_thread.daemon = True
            self.price_thread.start()
    
    def stop_price_updates(self):
        """Stop the price update thread"""
        self.running = False
        if self.price_thread:
            self.price_thread.join(timeout=1.0)
    
    def add_symbol(self, symbol):
        """Add a symbol to track for price updates"""
        self.active_symbols.add(symbol)
    
    def remove_symbol(self, symbol):
        """Remove a symbol from price tracking"""
        if symbol in self.active_symbols:
            self.active_symbols.remove(symbol)
    
    def _price_update_loop(self):
        """Background thread that emits price updates"""
        while self.running:
            try:
                # Get all ticker prices
                all_prices = BinanceService.get_ticker_prices()
                
                if all_prices and self.socketio:
                    # Filter to active symbols and emit updates
                    for price_data in all_prices:
                        symbol = price_data.get('symbol')
                        if symbol in self.active_symbols:
                            self.socketio.emit('price_update', price_data, room=f'price_{symbol}')
                
                # Sleep before next update
                time.sleep(5)
                
            except Exception as e:
                print(f"Error in price update loop: {e}")
                time.sleep(10)  # Sleep longer on error

# Create singleton instance
websocket_service = WebSocketService()
