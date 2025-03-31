import os
from app import create_app

# Get environment from environment variable or default to production
env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

if __name__ == '__main__':
    app.run()
