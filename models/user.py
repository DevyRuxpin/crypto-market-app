from flask_login import UserMixin
import uuid

class User(UserMixin):
    # In-memory user storage for this demo
    # In a real app, you would use a database
    users = {}
    
    def __init__(self, name, email, password_hash):
        self.id = str(uuid.uuid4())
        self.name = name
        self.email = email
        self.password_hash = password_hash
        
        # Save user to in-memory storage
        User.users[self.id] = self
    
    @staticmethod
    def find_by_email(email):
        """Find a user by email address"""
        for user in User.users.values():
            if user.email == email:
                return user
        return None
