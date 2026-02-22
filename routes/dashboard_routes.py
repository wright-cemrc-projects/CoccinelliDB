import os
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, send_from_directory, abort, g
from app import oidc, db
from app.models import InstrumentSession, Collection, session_person_link

dashboard_bp = Blueprint('dashboard', __name__)


def _get_accessible_collections():
    """
    Return all Collection objects from active/recent sessions
    that the current person (g.person) is linked to.

    'Active/recent' = sessions where end_date IS NULL or end_date >= 30 days ago.
    """
    cutoff = datetime.utcnow() - timedelta(days=30)

    # Find session IDs this person is linked to
    linked_session_ids = db.session.execute(
        db.select(session_person_link.c.session_id).where(
            session_person_link.c.person_id == g.person.id
        )
    ).scalars().all()

    if not linked_session_ids:
        return []

    # Load recent/active sessions from that set
    sessions = db.session.execute(
        db.select(InstrumentSession).where(
            InstrumentSession.id.in_(linked_session_ids),
            db.or_(
                InstrumentSession.end_date.is_(None),
                InstrumentSession.end_date >= cutoff
            )
        )
    ).scalars().all()

    collections = []
    for session in sessions:
        collections.extend(session.collections)
    return collections


@dashboard_bp.route('/api/dashboard/collections', methods=['GET'])
@oidc.require_login
def get_dashboard_collections():
    """
    Returns active/recent collections visible to the current person,
    including a list of up to 20 thumbnail filenames found at data_location.
    """
    if not hasattr(g, 'person') or g.person is None:
        return jsonify({"error": "Not authenticated"}), 401

    collections = _get_accessible_collections()

    result = []
    for collection in collections:
        thumbnails = []
        if collection.data_location and os.path.isdir(collection.data_location):
            try:
                all_files = os.listdir(collection.data_location)
                jpg_files = sorted(
                    f for f in all_files
                    if f.lower().endswith('.jpg')
                )
                # Most recent 20 thumbnails (last alphabetically, which typically == newest)
                thumbnails = jpg_files[-20:]
            except OSError:
                thumbnails = []

        result.append({
            "id": collection.id,
            "collection_type": collection.collection_type,
            "start_date": collection.start_date.isoformat() if collection.start_date else None,
            "end_date": collection.end_date.isoformat() if collection.end_date else None,
            "session_id": collection.instrument_session_id,
            "instrument_id": collection.instrument_session.instrument_id if collection.instrument_session else None,
            "image_count": len(thumbnails),
            "thumbnails": thumbnails,
        })

    return jsonify({"collections": result})


@dashboard_bp.route('/api/dashboard/images/<int:collection_id>/<path:filename>', methods=['GET'])
@oidc.require_login
def serve_collection_image(collection_id, filename):
    """
    Serves a JPG thumbnail from a collection's data_location.
    Validates that the current person has access to the collection
    and that the filename does not escape the data_location directory.
    """
    if not hasattr(g, 'person') or g.person is None:
        abort(401)

    # Load the collection and verify it's accessible to this user
    accessible_ids = {c.id for c in _get_accessible_collections()}
    if collection_id not in accessible_ids:
        abort(403)

    collection = db.session.get(Collection, collection_id)
    if not collection or not collection.data_location:
        abort(404)

    # Resolve the real paths to guard against traversal
    base_dir = os.path.realpath(collection.data_location)
    requested = os.path.realpath(os.path.join(base_dir, filename))
    if not requested.startswith(base_dir + os.sep):
        abort(403)

    return send_from_directory(base_dir, os.path.basename(requested))
