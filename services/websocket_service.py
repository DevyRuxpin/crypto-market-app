import socketio
from services.binance_service import BinanceService

sio = socketio.Server()

@sio.event
def connect(sid, environ):
    print('Client connected')

@sio.event
def disconnect(sid):
    print('Client disconnected')

@sio.on('subscribe')
def handle_subscribe(sid, data):
    symbol = data['symbol']
    binance_service = BinanceService()
    binance_service.subscribe_to_symbol(symbol, sid)

@sio.on('unsubscribe')
def handle_unsubscribe(sid, data):
    symbol = data['symbol']
    binance_service = BinanceService()
    binance_service.unsubscribe_from_symbol(symbol, sid)

def init_websocket(app):
    sio.init_app(app)
