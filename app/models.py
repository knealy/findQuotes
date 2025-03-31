from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Import the db instance, don't recreate it
from app import db

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'author': self.author,
            'source': self.source
        }

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Cloudinary account info
    cloudinary_cloud_name = db.Column(db.String(120))
    cloudinary_api_key = db.Column(db.String(120))
    cloudinary_api_secret = db.Column(db.String(120))
    cloudinary_connected = db.Column(db.Boolean, default=False)
    
    # User's designs
    designs = db.relationship('Design', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Design(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    design_id = db.Column(db.String(64), index=True)
    cloudinary_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    title = db.Column(db.String(100), default="Untitled Design")
    
    def to_dict(self):
        return {
            'id': self.id,
            'design_id': self.design_id,
            'cloudinary_url': self.cloudinary_url,
            'created_at': self.created_at.isoformat(),
            'title': self.title
        } 