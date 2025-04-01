import os
from flask import Flask, render_template, redirect, url_for, flash, request, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime
import logging
import pyotp
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use absolute imports
from database import db
from models import User, Portfolio, PortfolioItem, Watchlist, WatchlistSymbol, Alert
from routes.api import api_bp, limiter  # Import limiter
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

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Attach Limiter to app
limiter.init_app(app)

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',  # Use Render's DATABASE_URL environment variable
    'sqlite:///crypto_market_app.db'  # Fallback to SQLite for local development
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Register Blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp, url_prefix='/')

@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200

# Ensure app runs with gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
