import json
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)

    experiments = db.relationship('Experiment', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Experiment(db.Model):
    __tablename__ = 'experiments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.String(20), nullable=False)  # 'predict', 'attack', 'defend'
    image_name = db.Column(db.String(255), nullable=False)
    parameters = db.Column(db.Text, nullable=True)  # Stocké en JSON
    original_prediction = db.Column(db.String(50), nullable=True)
    final_prediction = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='success', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "action_type": self.action_type,
            "image_name": self.image_name,
            "parameters": json.loads(self.parameters) if self.parameters else {},
            "original_prediction": self.original_prediction,
            "final_prediction": self.final_prediction,
            "confidence": self.confidence,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }