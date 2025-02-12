from flask import Blueprint, render_template, jsonify, request, session, redirect
from flask_cors import CORS
from app import oidc, db
import os
from app.models import Person
from flask_oidc import OpenIDConnect
from functools import wraps

login_bp = Blueprint('login', __name__)
CORS(login_bp, supports_credentials=True)


def oidc_login_required(oidc: OpenIDConnect):
    """
    Custom decorator: Uses OIDC authentication in production,
    session-based authentication in development.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Development Mode: Check session["user"]
            if os.getenv("FLASK_ENV") == "development":
                if "user" in session:
                    return f(*args, **kwargs)  # Proceed if user is in session
                return jsonify({"error": "Unauthorized"}), 401  # Deny access if not logged in

            # Production Mode: Use OIDC's built-in require_login
            return oidc.require_login(f)(*args, **kwargs)

        return wrapped
    return decorator

@login_bp.route("/login")
def login():
    # the name of this method shouldn't be the same as the blueprint name
    if os.getenv("FLASK_ENV") == "development":
        session["user"] = {
            "id": 1,
            "first_name": "demo",
            "last_name": "refine",
            "email": "demo@refine.dev"
        }
        return redirect("/authorize")
    elif os.getenv("FLASK_ENV")  == "production":
        return oidc.redirect_to_auth_server(request.url) # Redirect to campus login page

@login_bp.route("/authorize")
def auth_callback():
    if os.getenv("FLASK_ENV") == "development":
        return redirect("http://localhost:5173/")
    elif os.getenv("FLASK_ENV") == "production":
        if oidc.user_loggedin:
            return redirect("http://localhost:5173/")  # Redirect to frontend

    return "Login failed", 401

@login_bp.route("/logout", methods=["POST"])
def logout():
    if os.getenv("FLASK_ENV") == "production":
        oidc.logout()
    session.clear()  # Clear session data
    return jsonify({"message": "Logged out"}), 200

# User Info Route
@login_bp.route("/me")
def me():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(session["user"])
