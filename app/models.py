from datetime import datetime
from app import db

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(200))
    source = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    designs = db.relationship('Design', backref='quote', lazy=True)

class Design(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    font_style = db.Column(db.String(100))
    font_size = db.Column(db.Integer)
    background_color = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 