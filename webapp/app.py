"""
Flask entry point.

Registers the auth blueprint (login/signup/logout/reset), the database,
login manager, email, and the health form + prediction routes.
"""

import os
import sys
import json
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_required, current_user
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

from models_db import db, User, PredictionHistory
from extensions import mail
from auth import auth_bp
from forms import HealthForm
from suggestions import get_suggestion

load_dotenv()

# Make src/ (project root level, alongside webapp/) importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from predict import predict_all  # noqa: E402

# Every field on the health form -- used to safely parse request.form
# (which arrives as strings) into floats for the model. This covers
# both true numeric fields (age, glucose, ...) and categorical/binary
# fields, since radio/select values also arrive as numeric strings
# ("0"/"1"/etc) and get parsed the same way.
NUMERIC_FIELDS = [
    "age", "resting_bp_systolic", "resting_bp_diastolic", "resting_heart_rate",
    "max_heart_rate", "bmi", "pregnancies", "cigs_per_day", "family_diabetes_score",
    "glucose", "total_cholesterol", "insulin", "skin_thickness", "blood_urea",
    "serum_creatinine", "sodium", "potassium", "hemoglobin", "pcv", "wbc_count",
    "rbc_count", "total_bilirubin", "direct_bilirubin", "alkaline_phosphotase",
    "sgpt_alt", "sgot_ast", "total_proteins", "serum_albumin",
    "albumin_globulin_ratio", "urine_specific_gravity", "urine_albumin",
    "urine_sugar", "st_depression", "major_vessels",
    "gender", "current_smoker", "education_level", "bp_meds", "prevalent_stroke",
    "existing_diabetes", "existing_hypertension", "existing_cad",
    "fasting_blood_sugar_high", "rbc_in_urine", "pus_cell", "pus_cell_clumps",
    "bacteria", "chest_pain_type", "resting_ecg", "exercise_angina", "st_slope",
    "thalassemia", "appetite", "pedal_edema", "anemia",
]


DISEASE_THEME = {
    "heart_disease": {"icon": "fa-heart-pulse", "color": "#C4453A", "bg": "#FBEAE8"},
    "diabetes": {"icon": "fa-droplet", "color": "#D98E2F", "bg": "#FBF1E2"},
    "ckd": {"icon": "fa-water", "color": "#2E7D8C", "bg": "#E7F1F2"},
    "hypertension": {"icon": "fa-gauge-high", "color": "#7C5CBF", "bg": "#F0EBFA"},
    "liver_disease": {"icon": "fa-leaf", "color": "#4A8B5C", "bg": "#EAF3EC"},
}


def _parse_health_form(form_data):
    """Converts request.form (all strings) into a dict of floats.
    Missing/blank fields fall back to 0 rather than raising an error --
    the form's HTML defaults mean this should rarely trigger, but it's
    a safety net against a field being unexpectedly empty."""
    patient_data = {}
    for field in NUMERIC_FIELDS:
        raw_value = form_data.get(field, "")
        try:
            patient_data[field] = float(raw_value)
        except (TypeError, ValueError):
            patient_data[field] = 0.0
    return patient_data


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

    @app.route("/")
    @login_required
    def index():
        form = HealthForm()
        return render_template("index.html", form=form)

    @app.route("/predict", methods=["POST"])
    @login_required
    def predict():
        form = HealthForm()

        if not form.validate_on_submit():
            # CSRF token missing/invalid -- reject and send back to the form
            flash("Your session expired. Please fill in the form again.", "error")
            return redirect(url_for("index"))

        patient_data = _parse_health_form(request.form)

        try:
            raw_results = predict_all(patient_data)
        except FileNotFoundError as e:
            # A model .pkl is missing -- tell the developer exactly which one
            return f"Prediction error: {e}", 500

        # Attach next-step advice, sort by risk (highest first)
        results = []
        for disease_key, r in raw_results.items():
            theme = DISEASE_THEME.get(
                disease_key, {"icon": "fa-notes-medical", "color": "#5B6470", "bg": "#EEEEEE"}
            )
            results.append({
                "disease_key": disease_key,
                "display_name": r["display_name"],
                "probability": r["probability"],
                "probability_pct": round(r["probability"] * 100, 1),
                "risk_level": r["risk_level"],
                "advice": get_suggestion(disease_key, r["risk_level"]),
                "icon": theme["icon"],
                "color": theme["color"],
                "bg": theme["bg"],
            })
        results.sort(key=lambda r: r["probability"], reverse=True)

        # Save to prediction history for this user
        history_entry = PredictionHistory(
            user_id=current_user.id,
            results_json=json.dumps(results),
        )
        db.session.add(history_entry)
        db.session.commit()

        return render_template("result.html", results=results)

    @app.route("/health")
    def health_check():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
