from flask import Blueprint, render_template, jsonify, request, session, redirect
from app import oidc, db
import os
from app.models import Person
from flask_oidc import OpenIDConnect
from functools import wraps

login_bp = Blueprint('login', __name__)


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
    """
    Perform login logic. Store user info in session on development mode
    Redirect to auth server of oidc provider on production mode
    :return: Response
    """
    return oidc.redirect_to_auth_server(request.url)

@login_bp.route("/authorize")
def auth_callback():
    """
    Receive response from auth server. Resource access control happens here
    :return: Response
    """
    if oidc.user_loggedin:
        return redirect("http://localhost:5173/")  # Redirect to frontend
    return "Login failed", 401

@login_bp.route("/logout", methods=["GET"])
def logout():
    """
    Clear all login info from browser
    :return:
    """
    session.clear()  # Clear session data
    oidc.logout()
    return redirect("http://localhost:5173/login")

# User Info Route
@login_bp.route("/me")
def me():
    """
    :return: User info
    """
    if "oidc_auth_profile" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(session["oidc_auth_profile"])


@login_bp.route("/test_redirect")
def test():
    return redirect("http://localhost:5173/")
