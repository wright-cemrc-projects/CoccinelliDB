from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, abort, g
from app import oidc, db
import os
from app.models import Person
from flask_oidc import OpenIDConnect, signals
from functools import wraps
import requests
import sys
import hashlib

login_bp = Blueprint('login', __name__)

@signals.before_authorize.connect
def before_auth_handler(sender, **kwargs):
    email = session.get("oidc_auth_profile", {}).get("email")
    if email:
        try:
            # Check if user exists
            Person.query.filter_by(email=email).first_or_404(description="User not found")
            # session["next"] = "http://localhost:5173/"
        except Exception:
            print("User is not registered")
            session["next"] = url_for("login.logout")


@login_bp.route("/api/custom-logout", methods=["GET"])
def logout():
    """
    Clear all login info from browser
    :return:
    """

    # TODO: remove these FQDN from the code
    callbackURL = "http://localhost:5173"
    environment = os.getenv('FLASK_ENV', 'development')
    if environment == 'production':
       callbackURL = "https://cryo-db.biochem.wisc.edu"
       oidc.logout()
       return redirect(callbackURL)

    # For Auth0, but not CILogon
    domain = "dev-flo54hw1p0ohwfvo.us.auth0.com"
    idToken = session["oidc_auth_token"]["id_token"]
    session.clear()

    return redirect(f"https://{domain}/oidc/logout?id_token_hint={idToken}&post_logout_redirect_uri={callbackURL}")

# User Info Route
@login_bp.route("/api/me", methods=["GET"])
def me():
    """
    :return: User info
    """

    # user_info = oidc.user_getinfo(['email', 'sub', 'name'])
    # print(user_info, file=sys.stderr)
    # person = Person.query.filter_by(email=user_info["email"]).first()
    # if not person:
    #     print(f"{user_info['name']} with {user_info['email']} not registered", file=sys.stderr)
    #     return jsonify({"error": "Person not found"}), 404
    # roles = [role.name for role in person.roles]
    # user_dict = {
    #     "email": user_info['email'],
    #     "emailmd5": hashlib.md5(user_info['email'].encode('utf-8')).hexdigest(),
    #     "roles": roles
    # }
    #
    # return jsonify(user_dict)
    return jsonify({"email": "zhyan0096@gmail.com", "roles": ["Admin"]})

