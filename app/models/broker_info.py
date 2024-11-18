# app/models/broker_info.py
from app.extensions import db

class BrokerInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_key = db.Column(db.String(150), nullable=False)
    dob = db.Column(db.String(20), nullable=False)  # Date of Birth or PAN number
    password = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    broker_user_id = db.Column(db.String(150), nullable=False)
    user = db.relationship('User', backref=db.backref('broker_info', uselist=False))
