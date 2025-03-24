import os
import json
import websocket
import threading
import time

class WebSocketService:
    def __init__(self, socketio):
        self.socketio = socketio
        self.active_streams = {}
        self.ws_base_url = os.environ.get('BINANCE_WS_BASE_URL', 'wss://data-stream.binance.vision')
        print(f"WebSocketService initialized with base URL: {self.ws_base_url}")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            # Emit the data to all connected clients
            if 'k' in data:  # kline data
                symbol = data['s']
                interval = data['k']['i']
                self.socketio.emit(f'kline_{symbol.lower()}_{interval}', data)
            elif 'e' in data and data['e'] == '24hrTicker':  # individual ticker
                self.socketio.emit(f'ticker_{data["s"].lower()}', data)
            elif isinstance(data, list):  # all market tickers
                self.socketio.emit('all_tickers', data)
            else:
                # Generic data emission
                stream_name = ws.stream_name if hasattr(ws, 'stream_name') else 'unknown'
                self.socketio.emit(f'stream_{stream_name}', data)
        except Exception as e:
            print(f"Error in WebSocket _on_message: {e}")

    def _on_error(self, ws, error):
        stream_name = ws.stream_name if hasattr(ws, 'stream_name') else 'unknown'
        print(f"WebSocket error for {stream_name}: {error}")
        # Try to reconnect after a delay
        if stream_name in self.active_streams:
            threading.Timer(5.0, self._reconnect, args=[stream_name]).start()

    def _on_close(self, ws, close_status_code, close_msg):
        stream_name = ws.stream_name if hasattr(ws, 'stream_name') else 'unknown'
        print(f"WebSocket closed for {stream_name}: {close_status_code} - {close_msg}")
        # Remove from active streams if it was intentionally closed
        if hasattr(ws, 'intentional_close') and ws.intentional_close:
            if stream_name in self.active_streams:
                del self.active_streams[stream_name]
        else:
            # Try to reconnect after a delay
            if stream_name in self.active_streams:
                threading.Timer(5.0, self._reconnect, args=[stream_name]).start()

    def _on_open(self, ws):
        stream_name = ws.stream_name if hasattr(ws, 'stream_name') else 'unknown'
        print(f"WebSocket opened for {stream_name}")

    def _reconnect(self, stream_name):
        print(f"Attempting to reconnect to {stream_name}")
        if stream_name in self.active_streams:
            old_ws = self.active_streams[stream_name]
            # Create a new connection
            if stream_name == "!ticker@arr":
                self.start_ticker_stream()
            elif '@kline_' in stream_name:
                parts = stream_name.split('@kline_')
                if len(parts) == 2:
                    symbol = parts[0].upper()
                    interval = parts[1]
                    self.start_kline_stream(symbol, interval)

    def start_kline_stream(self, symbol, interval='1m'):
        """Start a WebSocket stream for a specific symbol and interval"""
        try:
            stream_name = f"{symbol.lower()}@kline_{interval}"
            
            # Check if this stream is already active
            if stream_name in self.active_streams:
                print(f"Stream {stream_name} is already active")
                return True
                
            # Create a new WebSocket connection
            ws_url = f"{self.ws_base_url}/ws/{stream_name}"
            print(f"Starting kline stream: {ws_url}")
            
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # Store the stream name for reference in callbacks
            ws.stream_name = stream_name
            ws.intentional_close = False
            
            # Start the WebSocket connection in a new thread
            wst = threading.Thread(target=ws.run_forever)
            wst.daemon = True
            wst.start()
            
            # Store the WebSocket connection
            self.active_streams[stream_name] = ws
            
            return True
        except Exception as e:
            print(f"Error starting kline stream: {e}")
            return False

    def start_ticker_stream(self):
        """Start a WebSocket stream for all market tickers"""
        try:
            stream_name = "!ticker@arr"
            
            # Check if this stream is already active
            if stream_name in self.active_streams:
                print(f"Stream {stream_name} is already active")
                return True
                
            # Create a new WebSocket connection
            ws_url = f"{self.ws_base_url}/ws/{stream_name}"
            print(f"Starting ticker stream: {ws_url}")
            
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # Store the stream name for reference in callbacks
            ws.stream_name = stream_name
            ws.intentional_close = False
            
            # Start the WebSocket connection in a new thread
            wst = threading.Thread(target=ws.run_forever)
            wst.daemon = True
            wst.start()
            
            # Store the WebSocket connection
            self.active_streams[stream_name] = ws
            
            return True
        except Exception as e:
            print(f"Error starting ticker stream: {e}")
            return False

    def stop_stream(self, stream_name):
        """Stop a specific WebSocket stream"""
        try:
            if stream_name in self.active_streams:
                ws = self.active_streams[stream_name]
                ws.intentional_close = True  # Mark as intentionally closed
                ws.close()
                return True
            else:
                print(f"Stream {stream_name} is not active")
                return False
        except Exception as e:
            print(f"Error stopping stream {stream_name}: {e}")
            return False

    def stop_all_streams(self):
        """Stop all active WebSocket streams"""
        try:
            for stream_name, ws in list(self.active_streams.items()):
                ws.intentional_close = True
                ws.close()
            self.active_streams.clear()
            return True
        except Exception as e:
            print(f"Error stopping all streams: {e}")
            return False

