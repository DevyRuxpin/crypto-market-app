from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import pyotp
import secrets

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(16))
    recovery_codes = db.Column(db.String(200))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                           algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def enable_two_factor(self):
        self.two_factor_enabled = True
        self.two_factor_secret = pyotp.random_base32()
        self.recovery_codes = ','.join(secrets.token_hex(4) for _ in range(10))
        db.session.commit()

    def disable_two_factor(self):
        self.two_factor_enabled = False
        self.two_factor_secret = None
        self.recovery_codes = None
        db.session.commit()

    def verify_totp(self, code):
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(code)

    def verify_recovery_code(self, code):
        if self.recovery_codes:
            codes = self.recovery_codes.split(',')
            if code in codes:
                codes.remove(code)
                self.recovery_codes = ','.join(codes)
                db.session.commit()
                return True
        return False

    def save(self):
        db.session.add(self)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
