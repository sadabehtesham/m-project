"""
SQLAlchemy User model for the login system.
Passwords are NEVER stored in plain text -- only a bcrypt/werkzeug hash.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Basic brute-force protection
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    # Password reset (forgot password flow)
    reset_token_hash = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # Email verification
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token_hash = db.Column(db.String(255), nullable=True)
    verification_token_expiry = db.Column(db.DateTime, nullable=True)

    def set_password(self, plain_password):
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        return check_password_hash(self.password_hash, plain_password)

    def __repr__(self):
        return f"<User {self.email}>"


class PredictionHistory(db.Model):
    """
    Optional: stores a record of each prediction a user makes,
    so they can look back at past results.
    """
    __tablename__ = "prediction_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Risk scores stored as a JSON string, e.g.
    # {"diabetes": 0.78, "heart_disease": 0.34, "ckd": 0.12, ...}
    results_json = db.Column(db.Text, nullable=False)
