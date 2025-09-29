from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, default=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Denied
    collected = db.Column(db.Boolean, default=False)
    returned = db.Column(db.Boolean, default=False)
    vehicle = db.relationship('Vehicle')

def setup_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

        # Add default users
        if not User.query.filter_by(username='user123').first():
            user = User(username='user123', password='pass123', is_admin=False)
            admin = User(username='admin', password='adminpass', is_admin=True)
            db.session.add_all([user, admin])

        db.session.commit()