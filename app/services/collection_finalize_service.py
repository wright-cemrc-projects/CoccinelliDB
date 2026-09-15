"""Apply reviewed counts to a Collection and lock it (editable=False).

Shared by the /api/collection/bulk_finalize route (for a future UI upload) and
scripts/finalize_collections.py (for a CSV run from the command line), so the
two can't drift on what "finalize a row" means.

A row whose collection is already finalized is deliberately left alone rather
than silently re-locked with new values — a batch finalize run should never
be able to overwrite an existing lock; that still requires the explicit,
Admin-only unlock in the main app (see update_collection).

None of this commits; the caller controls the transaction.
"""
from __future__ import annotations

from app import db
from app.models import Collection


class AlreadyFinalized(ValueError):
    """Raised when a row's collection is already locked (editable=False)."""

    def __init__(self, collection_id: int):
        self.collection_id = collection_id
        super().__init__(f"Collection {collection_id} is already finalized; left unchanged.")


def resolve_collection(collection_id=None, data_location=None) -> Collection:
    """Look up a Collection by id or data_location. Exactly one should be given."""
    if collection_id is not None:
        collection = db.session.get(Collection, int(collection_id))
        if not collection:
            raise ValueError(f"No collection with id {collection_id}.")
        return collection

    if data_location:
        collection = db.session.execute(
            db.select(Collection).filter_by(data_location=data_location)
        ).scalar_one_or_none()
        if not collection:
            raise ValueError(f"No collection with data_location '{data_location}'.")
        return collection

    raise ValueError("Provide either id or data_location to identify the collection.")


def _parse_optional_int(value, field_name: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{value}' is not a valid integer for {field_name}.")


def finalize_collection(
    collection_id=None,
    data_location=None,
    total_image_count=None,
    lamella_count=None,
) -> Collection:
    """Set the given counts on a Collection and lock it. Raises on failure.

    Raises ValueError if the collection can't be found or a count isn't a
    valid integer, and AlreadyFinalized (a ValueError subclass) if it's
    already locked. Both counts are validated before either is assigned, so a
    bad value in one field can't leave the other staged on the session for a
    row that's ultimately reported as an error.
    """
    collection = resolve_collection(collection_id, data_location)
    if not collection.editable:
        raise AlreadyFinalized(collection.id)

    parsed_image_count = _parse_optional_int(total_image_count, "total_image_count")
    parsed_lamella_count = _parse_optional_int(lamella_count, "lamella_count")

    if parsed_image_count is not None:
        collection.total_image_count = parsed_image_count
    if parsed_lamella_count is not None:
        collection.lamella_count = parsed_lamella_count
    collection.editable = False

    db.session.flush()
    return collection
