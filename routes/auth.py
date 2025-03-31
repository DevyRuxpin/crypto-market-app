from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime
import pyotp

from database import db
from models.user import User
from models import Portfolio, Watchlist, WatchlistSymbol
from forms import LoginForm, SignupForm, TwoFactorForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            id=str(uuid.uuid4()),
            name=form.name.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
