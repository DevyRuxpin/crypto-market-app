from flask import current_app
from flask_mail import Mail, Message

mail = Mail()

def init_email(app):
    mail.init_app(app)

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    msg = Message('Password Reset Request',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_password', token=token, _external=True)}
If you did not make this request, please ignore this email.
'''
    mail.send(msg)
