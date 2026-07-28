import os
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, send_from_directory, abort, g
from app import oidc, db
from app.models import InstrumentSession, Collection, session_person_link
from app.services.collection_scan_service import scan_tilt_series, resolve_safe_path

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
    Returns active/recent collections visible to the current person, including a
    filmstrip of tilt-series thumbnails (most recent first, capped at 20) and a
    tilt-series count found at data_location.
    """
    if not hasattr(g, 'person') or g.person is None:
        return jsonify({"error": "Not authenticated"}), 401

    collections = _get_accessible_collections()

    result = []
    for collection in collections:
        tilt_series = scan_tilt_series(collection.data_location) if collection.data_location else []

        newest_first = sorted(tilt_series, key=lambda ts: ts.mtime, reverse=True)
        thumbnails = [
            ts.tomogram_image or ts.align_image
            for ts in newest_first
            if ts.tomogram_image or ts.align_image
        ][:20]

        result.append({
            "id": collection.id,
            "collection_type": collection.collection_type,
            "start_date": collection.start_date.isoformat() if collection.start_date else None,
            "end_date": collection.end_date.isoformat() if collection.end_date else None,
            "session_id": collection.instrument_session_id,
            "instrument_id": collection.instrument_session.instrument_id if collection.instrument_session else None,
            "tilt_series_count": len(tilt_series),
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

    requested = resolve_safe_path(collection.data_location, filename)
    if requested is None:
        abort(403)

    return send_from_directory(os.path.dirname(requested), os.path.basename(requested))
