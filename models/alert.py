from app import db
from models.user import User

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('alerts', lazy='dynamic'))
    symbol = db.Column(db.String(10), nullable=False)
    price_threshold = db.Column(db.Float, nullable=False)
    is_above = db.Column(db.Boolean, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def toggle_active(self):
        self.is_active = not self.is_active
        db.session.commit()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
