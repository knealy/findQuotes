from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app import routes, models
    app.register_blueprint(routes.bp)

    with app.app_context():
        db.create_all()

    # Allow ngrok domain
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    @app.before_request
    def handle_ngrok():
        if 'X-Forwarded-Proto' in request.headers:
            if request.headers['X-Forwarded-Proto'] == 'https':
                request.environ['wsgi.url_scheme'] = 'https'

    return app 