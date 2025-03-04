from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from app import oidc, db
import os
from app.models import Person
from flask_oidc import OpenIDConnect, signals
from functools import wraps
import requests

login_bp = Blueprint('login', __name__)

@signals.after_authorize.connect
def after_auth_handler(sender, **kwargs):
    """Triggered when the user is authenticated. Check if user is already registered"""
    kwargs["return_to"] = "http://127.0.0.1:8080/api/home"
    email = session["oidc_auth_profile"]["email"]
    try:
        Person.query.filter_by(email=email).first_or_404(description="User not found")
        return redirect("http://localhost:5173")
    except Exception as err:
        print({"err": f"{err=}"})
        print("user is not registered")
        session["return_to"] = url_for("login.logout", _external=True)
        return

@login_bp.route("/api/custom-logout", methods=["GET"])
def logout():
    """
    Clear all login info from browser
    :return:
    """
    domain = "dev-flo54hw1p0ohwfvo.us.auth0.com"
    idToken = session["oidc_auth_token"]["id_token"]

    # TODO: remove these FQDN from the code
    callbackURL = "http://localhost:5173"
    environment = os.getenv('FLASK_ENV', 'development')
    if environment == 'production':
       callbackURL = "https://cryo-db.biochem.wisc.edu"

    session.clear()
    return redirect(f"https://{domain}/oidc/logout?id_token_hint={idToken}&post_logout_redirect_uri={callbackURL}")

# User Info Route
@login_bp.route("/api/me")
def me():
    """
    :return: User info
    """
    if "oidc_auth_profile" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(session["oidc_auth_profile"])

