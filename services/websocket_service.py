import json
import threading
import time
from flask_socketio import emit
from services.binance_service import BinanceService

class WebSocketService:
    """Service for handling WebSocket connections and real-time updates"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.active_symbols = set()
        self.running = False
        self.price_thread = None
        
        # Start price update thread
        self.start_price_updates()
    
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
                
                if all_prices:
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

