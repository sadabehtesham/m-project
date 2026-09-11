"""
Flask-WTF forms for authentication.
CSRF protection is automatic (CSRFProtect is enabled in app.py).
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Regexp, ValidationError
)


class SignupForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=120)]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)]
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters."),
            Regexp(
                r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$",
                message="Password must contain an uppercase letter, a lowercase letter, a number, and a special character."
            ),
        ]
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords do not match.")
        ]
    )
    submit = SubmitField("Create account")

    def validate_email(self, field):
        # Strip whitespace, normalize case, to avoid duplicate accounts
        # that differ only by casing/whitespace
        field.data = field.data.strip().lower()


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log in")


class OTPForm(FlaskForm):
    otp = StringField(
        "Verification code",
        validators=[
            DataRequired(),
            Length(min=6, max=6, message="Enter the 6-digit code."),
            Regexp(r"^\d{6}$", message="Code must be 6 digits.")
        ]
    )
    submit = SubmitField("Verify")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send reset link")


class HealthForm(FlaskForm):
    """
    Only provides the CSRF token for the unified health form.
    The ~40 patient data fields are read manually via request.form
    in the /predict route (Step 9), since they map to 5 different
    models rather than one set of WTForms fields.
    """
    submit = SubmitField("Check my risk")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters."),
            Regexp(
                r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$",
                message="Password must contain an uppercase letter, a lowercase letter, a number, and a special character."
            ),
        ]
    )
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("password", message="Passwords do not match.")]
    )
    submit = SubmitField("Reset password")
