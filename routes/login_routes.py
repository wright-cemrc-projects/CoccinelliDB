from flask import Blueprint, render_template, jsonify, request, session, redirect
from flask_cors import CORS
from app import oidc, db
import os
from app.models import Person

config = os.getenv('FLASK_ENV', 'development')
login_bp = Blueprint('login', __name__)
CORS(login_bp, supports_credentials=True) 



@login_bp.route("/login")
def login():
    # the name of this method shouldn't be the same as the blueprint name
    if config == "development":
        session["user"] = {
            "id": 1,
            "first_name": "demo",
            "last_name": "refine",
            "email": "demo@refine.dev"
        }
        return redirect("/authorize")
    elif config == "production":
        return oidc.redirect_to_auth_server(request.url) # Redirect to campus login page

@login_bp.route("/authorize")
def auth_callback():
    if config == "development":
        return redirect("http://localhost:5173/")
    elif conig == "production":
        if oidc.user_loggedin:
            return redirect("http://localhost:5173/")  # Redirect to frontend

    return "Login failed", 401

@login_bp.route("/logout", methods=["POST"])
def logout():
    if config == "production":
        oidc.logout()
    session.clear()  # Clear session data
    return jsonify({"message": "Logged out"}), 200

# User Info Route
@login_bp.route("/me")
def me():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(session["user"])
