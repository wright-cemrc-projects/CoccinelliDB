from flask import Blueprint, render_template, jsonify, request, session, redirect
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
    email = session["oidc_auth_profile"]["email"]
    try:
        Person.query.filter_by(email=email).first_or_404(description="User not found")
        return redirect("http://localhost:5173")
    except Exception as err:
        print({"err": f"{err=}"})
        print("user is not registered")
        session.clear()
        return redirect("/custom-logout")

@login_bp.route("/custom-logout", methods=["GET"])
def logout():
    """
    Clear all login info from browser
    :return:
    """
    domain = "dev-flo54hw1p0ohwfvo.us.auth0.com"
    idToken = session["oidc_auth_token"]["id_token"]
    callbackURL = "http://localhost:5173/login"
    session.clear()
    return redirect(f"https://{domain}/oidc/logout?id_token_hint={idToken}&post_logout_redirect_uri={callbackURL}")

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
    return jsonify({"message": "hello"})


# https://dev-flo54hw1p0ohwfvo.us.auth0.com/oidc/logout?id_token_hint=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Im55Wnd0MmJTQnQzbmc0UjJleTVLaiJ9.eyJlbWFpbCI6InpoeWFuMDA5NkBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6Ly9kZXYtZmxvNTRodzFwMG9od2Z2by51cy5hdXRoMC5jb20vIiwiYXVkIjoieGRtSldtZFFXcTd6d0VOalBORnZmMHZYVXdHT3hiR00iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDEwODc1NjQzMTk4ODYyNDU2MjY5OSIsImlhdCI6MTc0MDA4MjY5MywiZXhwIjoxNzQwMTE4NjkzLCJzaWQiOiJYeUpJWnMtWXZkT1Y5c25MXzB0eUJIVHpVNkpWUkhOZiIsIm5vbmNlIjoiZXJGWkRqY1ZJRHFKSmxtOFh2aWYifQ.JtRn8UvwRCkAjPDCOAfnsaw2UohFLPglRvTCJflWMZgOvU_rwrTMKBAx09-jb2v7qfJFQL-wCMTbT0HLsZrMOm81A2JHXKJhyQEoNrW43q6KwJ6sna5Cs9bvx-l1FV9t3riImVUFaGm4nPtWG4qzo96qW4DFl8Deoow6g2EJ-gnCuEHY0pzSkjp1KesHd-dk_lajT2lFgdyqGtxXwz6DZgdlYMg4jm64bjUqjUmb5s1QSBqsJYqBAt8IFJhHW76RCn4l8Xtmm5NJXvfmW-QeGVELd23PowyzmK3s9sU_-QWXKBi2TVQQfWGAD-l0J_-TsVBkO6wJrAFSL9edkGLm7g&post_logout_redirect_uri=http://localhost:5173