from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from config import Config
from forms import LoginForm, SignupForm, PasswordResetRequestForm, PasswordResetForm, TwoFactorForm, RecoveryCodeForm
from models.user import User
from models.portfolio import Portfolio, PortfolioItem
from models.watchlist import Watchlist, WatchlistSymbol
from models.alert import Alert
from services.api_service import CryptoAPIService
from services.binance_service import BinanceService
from services.websocket_service import WebSocketService
import os

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

from routes.main import main as main_blueprint
from routes.auth import auth as auth_blueprint
from routes.api import api as api_blueprint

app.register_blueprint(main_blueprint)
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(api_blueprint, url_prefix='/api')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
