from flask import Blueprint, jsonify, request, current_app
from functools import wraps
from datetime import datetime

from app import db
from app.models import Collection, Instrument, InstrumentSession, Project
from app.schema import collectionSchema, collectionsSchema, instrumentSessionSchema, instrumentSessionsSchema, projectSchema

import sys

instrument_client_bp = Blueprint('instrument_client', __name__)


def resolve_project_id(payload):
    """Resolve the integer Project.id from request data.

    Accepts either `project_id` (the integer Project.id) or
    `project_string_id` (the Project.project_id string identifier), looking
    the latter up to find the corresponding Project.id.
    Returns (project_id, error_response). error_response is None on success.
    """
    if 'project_string_id' in payload:
        project_string_id = payload['project_string_id']
        project = Project.query.filter(Project.project_id.ilike(project_string_id)).first()
        if not project:
            return None, (jsonify({"error": f"Project with project_id '{project_string_id}' not found"}), 404)
        return project.id, None

    if 'project_id' in payload:
        return int(payload['project_id']), None

    return None, None


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if not key or key != current_app.config.get('INSTRUMENT_API_KEY'):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@instrument_client_bp.route('/api/client/collections', methods=['POST'])
@require_api_key
def create_collection():
    try:
        instrument_session_id = request.json.get('instrument_session_id')
        if not instrument_session_id:
            return jsonify({"error": "instrument_session_id is required"}), 400

        instrument_session = db.session.get(InstrumentSession, int(instrument_session_id))
        if not instrument_session:
            return jsonify({"error": f"InstrumentSession {instrument_session_id} not found"}), 404

        data_location = request.json.get('data_location')
        if data_location:
            existing = Collection.query.filter_by(data_location=data_location).first()
            if existing:
                return collectionSchema.jsonify(existing), 409

        collection = Collection()
        collection.instrument_session_id = int(instrument_session_id)

        if data_location:
            collection.data_location = data_location
        if 'start_date' in request.json:
            collection.start_date = datetime.fromisoformat(request.json['start_date'])
        if 'end_date' in request.json:
            collection.end_date = datetime.fromisoformat(request.json['end_date'])
        if 'total_image_count' in request.json:
            collection.total_image_count = int(request.json['total_image_count'])
        if 'collection_type' in request.json:
            collection.collection_type = request.json['collection_type']

        db.session.add(collection)
        db.session.commit()
        return collectionSchema.jsonify(collection), 201
    except Exception as err:
        print(err, file=sys.stderr)
        db.session.rollback()
        return jsonify({"error": str(err)}), 400


@instrument_client_bp.route('/api/client/collections/<int:id>', methods=['GET'])
@require_api_key
def get_collection(id):
    try:
        collection = db.get_or_404(Collection, id)
        return collectionSchema.jsonify(collection)
    except Exception as err:
        return jsonify({"error": str(err)}), 404


@instrument_client_bp.route('/api/client/collections/<int:id>', methods=['PATCH'])
@require_api_key
def update_collection(id):
    """Update an existing Collection (e.g. to extend end_date/total_image_count for an ongoing scan)."""
    try:
        collection = db.session.get(Collection, id)
        if not collection:
            return jsonify({"error": f"Collection {id} not found"}), 404

        if 'start_date' in request.json:
            collection.start_date = datetime.fromisoformat(request.json['start_date'])
        if 'end_date' in request.json:
            collection.end_date = datetime.fromisoformat(request.json['end_date'])
        if 'total_image_count' in request.json:
            collection.total_image_count = int(request.json['total_image_count'])
        if 'collection_type' in request.json:
            collection.collection_type = request.json['collection_type']

        db.session.commit()
        return collectionSchema.jsonify(collection)
    except Exception as err:
        print(err, file=sys.stderr)
        db.session.rollback()
        return jsonify({"error": str(err)}), 400


@instrument_client_bp.route('/api/client/collections', methods=['GET'])
@require_api_key
def list_collections():
    try:
        data_location = request.args.get('data_location')
        if data_location:
            existing = Collection.query.filter_by(data_location=data_location).first()
            if existing:
                return collectionSchema.jsonify(existing)
            return jsonify(None), 404

        session_id = request.args.get('instrument_session_id')
        if session_id:
            results = Collection.query.filter_by(instrument_session_id=int(session_id)).all()
        else:
            results = Collection.query.all()
        return collectionsSchema.jsonify(results)
    except Exception as err:
        return jsonify({"error": str(err)}), 400


@instrument_client_bp.route('/api/client/projects', methods=['GET'])
@require_api_key
def get_project_by_string_id():
    """Look up a Project by its string project_id, returning its integer id."""
    try:
        project_string_id = request.args.get('project_id')
        if not project_string_id:
            return jsonify({"error": "project_id is required"}), 400

        project = Project.query.filter(Project.project_id.ilike(project_string_id)).first()
        if not project:
            return jsonify(None), 404

        return projectSchema.jsonify(project)
    except Exception as err:
        print(err, file=sys.stderr)
        return jsonify({"error": str(err)}), 400


@instrument_client_bp.route('/api/client/instrumentsessions', methods=['GET'])
@require_api_key
def list_sessions():
    """Find InstrumentSessions by instrument name and/or a datetime that falls within the session window."""
    try:
        instrument_name = request.args.get('instrument_name')
        dt_str = request.args.get('datetime')

        query = InstrumentSession.query.join(InstrumentSession.instrument)

        if instrument_name:
            query = query.filter(Instrument.name == instrument_name)

        if dt_str:
            dt = datetime.fromisoformat(dt_str)
            query = query.filter(
                InstrumentSession.start_date <= dt,
                InstrumentSession.end_date >= dt,
            )

        results = query.all()
        if not results:
            return jsonify(None), 404

        if instrument_name and dt_str:
            return instrumentSessionSchema.jsonify(results[0])

        return instrumentSessionsSchema.jsonify(results)
    except Exception as err:
        print(err, file=sys.stderr)
        return jsonify({"error": str(err)}), 400


@instrument_client_bp.route('/api/client/instrumentsessions', methods=['POST'])
@require_api_key
def create_session():
    """Create an InstrumentSession from a client script (no user login required)."""
    try:
        instrument_id = request.json.get('instrument_id')
        facility_id = request.json.get('facility_id')
        if not instrument_id or not facility_id:
            return jsonify({"error": "instrument_id and facility_id are required"}), 400

        start_date = None
        if 'start_date' in request.json:
            start_date = datetime.fromisoformat(request.json['start_date'])
        end_date = None
        if 'end_date' in request.json:
            end_date = datetime.fromisoformat(request.json['end_date'])

        project_id, error = resolve_project_id(request.json)
        if error:
            return error

        instrument_session = InstrumentSession(
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
            facility_id=int(facility_id),
            instrument_id=int(instrument_id),
        )
        db.session.add(instrument_session)
        db.session.commit()
        return instrumentSessionSchema.jsonify(instrument_session), 201
    except Exception as err:
        print(err, file=sys.stderr)
        db.session.rollback()
        return jsonify({"error": str(err)}), 400


@instrument_client_bp.route('/api/client/instrumentsessions/<int:id>', methods=['PATCH'])
@require_api_key
def update_session(id):
    """Update an existing InstrumentSession (e.g. to set end_date when collection finishes)."""
    try:
        session = db.session.get(InstrumentSession, id)
        if not session:
            return jsonify({"error": f"InstrumentSession {id} not found"}), 404

        if 'start_date' in request.json:
            session.start_date = datetime.fromisoformat(request.json['start_date'])
        if 'end_date' in request.json:
            session.end_date = datetime.fromisoformat(request.json['end_date'])

        project_id, error = resolve_project_id(request.json)
        if error:
            return error
        if project_id is not None:
            session.project_id = project_id

        db.session.commit()
        return instrumentSessionSchema.jsonify(session)
    except Exception as err:
        print(err, file=sys.stderr)
        db.session.rollback()
        return jsonify({"error": str(err)}), 400
