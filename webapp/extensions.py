"""
Shared extension instances.

Kept in their own module (separate from app.py and models_db.py) so
both app.py and auth.py can import the same `mail` object without
creating a circular import between them.
"""

from flask_mail import Mail

mail = Mail()
