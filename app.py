import os
from flask import Flask, render_template, redirect, url_for, flash, request, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime
import logging
import pyotp

# Use absolute imports
from database import db
from models import User, Portfolio, PortfolioItem, Watchlist, WatchlistSymbol, Alert
from routes.api import api_bp
from routes.auth import auth_bp
from routes.main import main_bp
from services.websocket_service import websocket_service

# Import forms
from forms import LoginForm, SignupForm, TwoFactorForm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
