"""
Authentication: signup (with OTP email verification), login, logout,
forgot/reset password.

Signup flow (OTP-based):
1. User submits the signup form. We do NOT create the account yet.
2. Their name/email/hashed-password are stashed in the session
   (server-side signed cookie -- the password is already hashed by
   this point, never stored in plain text even temporarily).
3. A random 6-digit OTP is generated, hashed, and stored in the
   session with a 10-minute expiry. The raw OTP is "emailed" (see
   NOTE below) to the user.
4. User enters the OTP on /verify-otp. If it matches (and hasn't
   expired, and hasn't been guessed wrong too many times), the real
   User row is finally created in the database, already verified.
5. If they never complete the OTP step, no account was ever created
   -- no orphaned unverified users sitting in the database.

Security measures:
- Passwords hashed via werkzeug (never stored/compared in plain text,
  not even in the temporary session during OTP verification)
- CSRF protection (via Flask-WTF forms, enabled globally in app.py)
- Account lockout after 5 failed login attempts (15 minute cooldown)
- Generic "invalid email or password" login message
- OTP is hashed before storing in the session, expires after 10
  minutes, and locks out after 5 wrong guesses (prevents brute-forcing
  a 6-digit code, which only has 1,000,000 combinations)
- Password reset tokens are hashed before storage and expire after 1 hour

NOTE on email delivery:
- The OTP IS actually emailed now, via Gmail SMTP (Flask-Mail),
  configured through MAIL_USERNAME / MAIL_PASSWORD / MAIL_DEFAULT_SENDER
  in .env. See README.md for how to generate a Gmail App Password.
- If sending fails for any reason (bad credentials, no internet),
  the code falls back to printing to the console so testing/demo
  isn't completely blocked -- watch for a [WARN]/[FALLBACK] line.
- The password-reset link (forgot password flow) still only prints
  to the console for now -- ask if you'd like that emailed too.
"""

import secrets
import hashlib
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message

from models_db import db, User
from forms import SignupForm, LoginForm, OTPForm, ForgotPasswordForm, ResetPasswordForm
from extensions import mail

auth_bp = Blueprint("auth", __name__)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
RESET_TOKEN_EXPIRY_MINUTES = 60
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


def _hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()


def _generate_and_store_otp(email):
    """Creates a random 6-digit OTP, stores only its hash + expiry in
    the session, resets the attempt counter, and returns the raw OTP
    (only place the raw value ever exists outside the recipient's inbox)."""
    otp = f"{secrets.randbelow(1_000_000):06d}"
    session["otp_hash"] = _hash_otp(otp)
    session["otp_expiry"] = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
    session["otp_attempts"] = 0
    session["otp_email"] = email
    return otp


def _send_otp_email(email, otp):
    """
    Sends the OTP as a real email via Gmail SMTP (Flask-Mail).
    Falls back to printing to the console if sending fails (e.g. Gmail
    credentials not configured yet) so testing isn't completely blocked.
    """
    try:
        msg = Message(
            subject="Your CDSS verification code",
            recipients=[email],
            body=(
                f"Your verification code is: {otp}\n\n"
                f"This code expires in {OTP_EXPIRY_MINUTES} minutes.\n\n"
                "If you didn't request this, you can ignore this email."
            ),
        )
        mail.send(msg)
        print(f"[INFO] OTP email sent to {email}")
    except Exception as e:
        # Common causes: MAIL_USERNAME/MAIL_PASSWORD missing or wrong,
        # 2-Step Verification not enabled, or using the real Gmail
        # password instead of an App Password.
        print(f"\n[WARN] Could not send OTP email ({e}).")
        print(f"[FALLBACK] Verification code for {email}: {otp}\n")


# ---------- Signup (step 1: collect details, send OTP) ----------

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = SignupForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("An account with this email already exists. Try logging in.", "error")
            return render_template("signup.html", form=form)

        # Stash pending signup data in the session -- NOT the database yet.
        # Password is hashed immediately, never kept in plain text.
        session["pending_signup"] = {
            "name": form.name.data.strip(),
            "email": form.email.data,
            "password_hash": generate_password_hash_for_pending(form.password.data),
        }

        otp = _generate_and_store_otp(form.email.data)
        _send_otp_email(form.email.data, otp)

        flash("We sent a 6-digit verification code to your email.", "success")
        return redirect(url_for("auth.verify_otp"))

    return render_template("signup.html", form=form)


def generate_password_hash_for_pending(plain_password):
    # Small wrapper so the hashing method stays consistent with User.set_password
    from werkzeug.security import generate_password_hash
    return generate_password_hash(plain_password)


# ---------- Signup (step 2: verify OTP, THEN create the account) ----------

@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    pending = session.get("pending_signup")
    if not pending:
        flash("Your signup session expired. Please sign up again.", "error")
        return redirect(url_for("auth.signup"))

    form = OTPForm()

    if form.validate_on_submit():
        expiry = session.get("otp_expiry")
        attempts = session.get("otp_attempts", 0)

        if not expiry or datetime.fromisoformat(expiry) < datetime.utcnow():
            flash("That code has expired. We've sent a new one.", "error")
            otp = _generate_and_store_otp(pending["email"])
            _send_otp_email(pending["email"], otp)
            return render_template("verify_otp.html", form=form, email=pending["email"])

        if attempts >= MAX_OTP_ATTEMPTS:
            flash("Too many incorrect attempts. Request a new code below.", "error")
            return render_template("verify_otp.html", form=form, email=pending["email"], locked=True)

        if _hash_otp(form.otp.data) == session.get("otp_hash"):
            # Correct code -- NOW we actually create the account.
            user = User(
                name=pending["name"],
                email=pending["email"],
                is_verified=True,
            )
            user.password_hash = pending["password_hash"]
            db.session.add(user)
            db.session.commit()

            session.pop("pending_signup", None)
            session.pop("otp_hash", None)
            session.pop("otp_expiry", None)
            session.pop("otp_attempts", None)
            session.pop("otp_email", None)

            flash("Email verified! Your account has been created. You can now log in.", "success")
            return redirect(url_for("auth.login"))

        session["otp_attempts"] = attempts + 1
        remaining = MAX_OTP_ATTEMPTS - session["otp_attempts"]
        if remaining > 0:
            flash(f"Incorrect code. {remaining} attempt(s) left.", "error")
        else:
            flash("Too many incorrect attempts. Request a new code below.", "error")

    return render_template("verify_otp.html", form=form, email=pending["email"])


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    pending = session.get("pending_signup")
    if not pending:
        flash("Your signup session expired. Please sign up again.", "error")
        return redirect(url_for("auth.signup"))

    otp = _generate_and_store_otp(pending["email"])
    _send_otp_email(pending["email"], otp)
    flash("A new verification code has been sent.", "success")
    return redirect(url_for("auth.verify_otp"))


# ---------- Login ----------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    generic_error = "Invalid email or password."

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.locked_until and user.locked_until > datetime.utcnow():
            minutes_left = int((user.locked_until - datetime.utcnow()).total_seconds() // 60) + 1
            flash(f"Too many failed attempts. Try again in {minutes_left} minute(s).", "error")
            return render_template("login.html", form=form)

        if user and user.check_password(form.password.data):
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()

            login_user(user, remember=form.remember_me.data)
            return redirect(url_for("index"))

        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                db.session.commit()
                flash(f"Too many failed attempts. Try again in {LOCKOUT_MINUTES} minutes.", "error")
                return render_template("login.html", form=form)
            db.session.commit()

        flash(generic_error, "error")

    return render_template("login.html", form=form)


# ---------- Logout ----------

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


# ---------- Forgot password ----------

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        flash("If that email is registered, a reset link has been sent.", "success")

        if user:
            raw_token = secrets.token_urlsafe(32)
            user.reset_token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)
            db.session.commit()

            reset_link = url_for("auth.reset_password", token=raw_token, _external=True)
            print(f"\n[DEMO] Password reset link for {user.email}:\n{reset_link}\n")

        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = User.query.filter_by(reset_token_hash=token_hash).first()

    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash("That reset link is invalid or has expired. Request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token_hash = None
        user.reset_token_expiry = None
        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()

        flash("Password reset. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form, token=token)
