import json
import threading
import websocket
import time
from flask_socketio import SocketIO

class WebSocketService:
    def __init__(self, socketio):
        """Initialize with Flask-SocketIO for emitting to clients"""
        self.socketio = socketio
        self.connections = {}  # Store active connections
        
    def start_kline_stream(self, symbol, interval='1m'):
        """Start a kline/candlestick WebSocket stream"""
        stream_name = f"{symbol.lower()}@kline_{interval}"
        
        if stream_name in self.connections:
            return  # Already connected
            
        def on_message(ws, message):
            """Handle incoming WebSocket messages"""
            data = json.loads(message)
            # Emit to all clients subscribed to this stream
            self.socketio.emit(f'kline_update_{symbol.lower()}_{interval}', data)
            
        def on_error(ws, error):
            print(f"WebSocket error for {stream_name}: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket connection closed for {stream_name}")
            if stream_name in self.connections:
                del self.connections[stream_name]
                
        def on_open(ws):
            print(f"WebSocket connection opened for {stream_name}")
            
        # Create WebSocket connection
        ws_url = f"wss://data-stream.binance.vision/ws/{stream_name}"
        ws = websocket.WebSocketApp(ws_url,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close,
                                    on_open=on_open)
                                    
        # Start WebSocket connection in a separate thread
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # Store connection
        self.connections[stream_name] = ws
        return True
        
    def start_ticker_stream(self):
        """Start a WebSocket stream for all market tickers"""
        stream_name = "!ticker@arr"
        
        if stream_name in self.connections:
            return  # Already connected
            
        def on_message(ws, message):
            """Handle incoming WebSocket messages"""
            data = json.loads(message)
            # Emit to all clients subscribed to ticker updates
            self.socketio.emit('ticker_update', data)
            
        def on_error(ws, error):
            print(f"WebSocket error for {stream_name}: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket connection closed for {stream_name}")
            if stream_name in self.connections:
                del self.connections[stream_name]
                
        def on_open(ws):
            print(f"WebSocket connection opened for {stream_name}")
            
        # Create WebSocket connection
        ws_url = f"wss://data-stream.binance.vision/ws/{stream_name}"
        ws = websocket.WebSocketApp(ws_url,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close,
                                    on_open=on_open)
                                    
        # Start WebSocket connection in a separate thread
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # Store connection
        self.connections[stream_name] = ws
        return True
        
    def stop_stream(self, stream_name):
        """Stop a WebSocket stream"""
        if stream_name in self.connections:
            self.connections[stream_name].close()
            del self.connections[stream_name]
            return True
        return False
        
    def stop_all_streams(self):
        """Stop all WebSocket streams"""
        for stream_name in list(self.connections.keys()):
            self.stop_stream(stream_name)
