import uuid
from flask_login import UserMixin

class User(UserMixin):
    # In-memory storage for users (in a real app, this would be a database)
    users = {}
    
    def __init__(self, name, email, password_hash):
        self.id = str(uuid.uuid4())
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.settings = {
            'theme': 'light',
            'currency': 'USD',
            'notification_enabled': True,
            'default_crypto_list': ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE']
        }
        
        # Save to in-memory storage
        User.users[self.id] = self
    
    @classmethod
    def find_by_email(cls, email):
        for user in cls.users.values():
            if user.email == email:
                return user
        return None
    
    def update_settings(self, new_settings):
        for key, value in new_settings.items():
            if key in self.settings:
                self.settings[key] = value
        return self.settings
