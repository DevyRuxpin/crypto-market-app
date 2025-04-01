from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from forms import LoginForm, SignupForm, PasswordResetRequestForm, PasswordResetForm, TwoFactorForm, RecoveryCodeForm
from services.email_service import send_password_reset_email
import pyotp
import os

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            if user.two_factor_enabled:
                return redirect(url_for('auth.two_factor'))
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        user.save()
        flash('You have successfully registered. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/signup.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))

@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('No account found with that email address.', 'danger')
    return render_template('auth/reset_password_request.html', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_password_token(token)
    if not user:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.reset_password_request'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.save()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/two_factor', methods=['GET', 'POST'])
def two_factor():
    form = TwoFactorForm()
    if form.validate_on_submit():
        user = current_user
        if user.verify_totp(form.code.data):
            login_user(user)
            flash('Two-factor authentication successful.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid authentication code.', 'danger')
    return render_template('auth/two_factor.html', form=form)

@auth.route('/recovery_code', methods=['GET', 'POST'])
def recovery_code():
    form = RecoveryCodeForm()
    if form.validate_on_submit():
        user = current_user
        if user.verify_recovery_code(form.recovery_code.data):
            login_user(user)
            flash('Recovery code verified. Two-factor authentication disabled.', 'success')
            user.disable_two_factor()
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid recovery code.', 'danger')
    return render_template('auth/recovery_code.html', form=form)
