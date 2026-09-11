"""
Flask entry point.

Registers the auth blueprint (login/signup/logout/reset) and the
database + login manager. The unified health form and prediction
route get added in later steps.
"""

import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

from models_db import db, User
from extensions import mail
from auth import auth_bp

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///users.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Email (Gmail SMTP) ---
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get(
        "MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME")
    )

    db.init_app(app)
    mail.init_app(app)
    CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "error"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()

    from flask_login import login_required
    from forms import HealthForm

    @app.route("/")
    @login_required
    def index():
        form = HealthForm()
        return render_template("index.html", form=form)

    @app.route("/predict", methods=["POST"])
    @login_required
    def predict():
        # Placeholder for now — the real prediction logic
        # (loading all 5 models, running inference, showing result.html)
        # gets built in Step 9.
        return "Form submitted. (Prediction logic comes in the next step.)"

    @app.route("/health")
    def health_check():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
