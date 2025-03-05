from flask import Blueprint, render_template, jsonify, request, session, redirect
from datetime import datetime
from app.services.session_service import is_session_booked

remote_api_bp = Blueprint('remoteapi', __name__)

## Query to get a list of allowed users for an instrument.
@remote_api_bp.route('/api/remote/sessions/get_session_persons', methods=['GET'])
def get_session_persons():
    """Check if a session is booked."""
    instrument_id = request.args.get('instrument_id')
    if not instrument_id:
        return jsonify({"error": "Missing instrument_id"}), 400
    
    access_time = request.args.get('access_time')
    if not access_time:
        return jsonify({"error": "Missing access_time"}), 400
    
    # TODO: this should do a database query with a call from services to get a list of matching session_person_link records.
    persons = []
    return jsonify({"instrument_id": instrument_id, "datetime": datetime, "persons": persons})

## Query to get ask if a particular user is currently authorized.
@remote_api_bp.route('/api/remote/sessions/get_remote_session_allowed', methods=['GET'])
def get_remote_allowed():
    """Check if a session is booked."""
    instrument_id = request.args.get('instrument_id')
    if not instrument_id:
        return jsonify({"error": "Missing instrument_id"}), 400
    
    access_time = request.args.get('access_time')
    if not access_time:
        return jsonify({"error": "Missing access_time"}), 400
    
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Missing username"}), 400
    
    # TODO: this should do a database query with a call from services to check find a matching session_person_link record.
    authorized = False
    return jsonify({"instrument_id": instrument_id, "datetime": datetime, "username": username, "authorized": authorized})

@remote_api_bp.route('/api/remote/sessions/log_remote_access_connect', methods=['GET'])
def log_remote_access_connect():
    """ Create a log entry that an instrument was connected """
    instrument_id = request.args.get('instrument_id')
    if not instrument_id:
        return jsonify({"error": "Missing instrument_id"}), 400
    
    access_time = request.args.get('access_time')
    if not access_time:
        return jsonify({"error": "Missing access_time"}), 400
    
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Missing username"}), 400
    
    # TODO: this api endpoint should make a new log record via a services call.

    return jsonify({"instrument_id": instrument_id, "datetime": datetime, "username": username})