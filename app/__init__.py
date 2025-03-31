from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from datetime import datetime
import os

# Initialize extensions before creating any app
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure required directories exist
    os.makedirs(os.path.join(app.static_folder, 'designs'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'backgrounds'), exist_ok=True)
    
    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Set up login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Add template context processor for common variables
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    # Register blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Create auth blueprint
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Create database tables from scratch
    with app.app_context():
        # This will drop existing tables and create new ones
        db.drop_all()
        db.create_all()
    
    # Allow ngrok domain
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    @app.before_request
    def handle_ngrok():
        if 'X-Forwarded-Proto' in request.headers:
            if request.headers['X-Forwarded-Proto'] == 'https':
                request.environ['wsgi.url_scheme'] = 'https'

    return app 

# Important: Do circular imports AFTER creating db
from app import models 