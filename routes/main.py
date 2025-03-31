from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/crypto/<symbol>')
def crypto_detail(symbol):
    return render_template('crypto_detail.html', symbol=symbol)

@main_bp.route('/portfolio')
@login_required
def portfolio():
    return render_template('portfolio.html')

@main_bp.route('/alerts')
@login_required
def alerts():
    return render_template('alerts.html')

@main_bp.route('/watchlist')
@login_required
def watchlist():
    return render_template('watchlist.html')

@main_bp.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user)

@main_bp.route('/news')
def news():
    return render_template('news.html')

@main_bp.context_processor
def inject_now():
    return {'now': datetime.utcnow()}
