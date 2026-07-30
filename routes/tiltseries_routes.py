import os

from flask import Blueprint, jsonify, send_from_directory, abort
from flask_security import roles_accepted

from app import db
from app.models import Collection
from app.services.collection_scan_service import scan_tilt_series, resolve_safe_path

tiltseries_bp = Blueprint('tiltseries', __name__)


def _serialize(ts):
    return {
        "name": ts.name,
        "align_image": ts.align_image,
        "tomogram_image": ts.tomogram_image,
        "tomogram_projxy_image": ts.tomogram_projxy_image,
        "tomogram_projxz_image": ts.tomogram_projxz_image,
        "tilt_count": ts.tilt_count,
        "min_angle": ts.min_angle,
        "max_angle": ts.max_angle,
    }


@tiltseries_bp.route('/api/collection/<int:id>/tiltseries', methods=['GET'])
@roles_accepted('Admin', 'Editor')
def list_tilt_series(id):
    collection = db.get_or_404(Collection, id)
    thumbnail_root = collection.thumbnail_location or collection.data_location
    if not thumbnail_root:
        return jsonify({"tilt_series": []})

    tilt_series = scan_tilt_series(thumbnail_root)
    return jsonify({"tilt_series": [_serialize(ts) for ts in tilt_series]})


@tiltseries_bp.route('/api/collection/<int:id>/tiltseries/<name>', methods=['GET'])
@roles_accepted('Admin', 'Editor')
def get_tilt_series(id, name):
    collection = db.get_or_404(Collection, id)
    thumbnail_root = collection.thumbnail_location or collection.data_location
    if not thumbnail_root:
        abort(404)

    tilt_series = scan_tilt_series(thumbnail_root)
    match = next((ts for ts in tilt_series if ts.name == name), None)
    if match is None:
        abort(404)

    return jsonify(_serialize(match))


@tiltseries_bp.route('/api/collection/<int:id>/images/<path:filename>', methods=['GET'])
@roles_accepted('Admin', 'Editor')
def serve_tilt_series_image(id, filename):
    collection = db.session.get(Collection, id)
    thumbnail_root = collection.thumbnail_location or collection.data_location if collection else None
    if not collection or not thumbnail_root:
        abort(404)

    requested = resolve_safe_path(thumbnail_root, filename)
    if requested is None:
        abort(403)

    return send_from_directory(os.path.dirname(requested), os.path.basename(requested))
