import json

import pytest

from app import db
from app.models import Collection, Facility, Instrument, InstrumentSession, Person, Role
from app.services.collection_finalize_service import AlreadyFinalized, finalize_collection


@pytest.fixture()
def session_id(app):
    with app.app_context():
        facility = Facility(name="MCCET")
        db.session.add(facility)
        db.session.flush()
        instrument = Instrument(name="Krios", facility_id=facility.id)
        db.session.add(instrument)
        db.session.flush()
        session = InstrumentSession(facility_id=facility.id, instrument_id=instrument.id)
        db.session.add(session)
        db.session.commit()
        return session.id


def make_collection(session_id, data_location, editable=True):
    collection = Collection(data_location=data_location, instrument_session_id=session_id)
    collection.editable = editable
    db.session.add(collection)
    db.session.flush()
    return collection


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})


# --- service layer -----------------------------------------------------


def test_finalize_collection_sets_counts_and_locks(app, session_id):
    with app.app_context():
        collection = make_collection(session_id, "/data/one")
        db.session.commit()
        cid = collection.id

        finalize_collection(collection_id=cid, total_image_count=120, lamella_count=3)
        db.session.commit()

        updated = db.session.get(Collection, cid)
        assert updated.total_image_count == 120
        assert updated.lamella_count == 3
        assert updated.editable is False


def test_finalize_collection_by_data_location(app, session_id):
    with app.app_context():
        make_collection(session_id, "/data/by-location")
        db.session.commit()

        finalize_collection(data_location="/data/by-location", lamella_count=2)
        db.session.commit()

        updated = db.session.execute(
            db.select(Collection).filter_by(data_location="/data/by-location")
        ).scalar_one()
        assert updated.lamella_count == 2
        assert updated.editable is False


def test_finalize_collection_leaves_counts_unset_when_omitted(app, session_id):
    with app.app_context():
        collection = make_collection(session_id, "/data/no-counts")
        db.session.commit()
        cid = collection.id

        finalize_collection(collection_id=cid)
        db.session.commit()

        updated = db.session.get(Collection, cid)
        assert updated.total_image_count is None
        assert updated.lamella_count is None
        assert updated.editable is False


def test_finalize_collection_raises_already_finalized(app, session_id):
    with app.app_context():
        collection = make_collection(session_id, "/data/already", editable=False)
        db.session.commit()
        cid = collection.id

        with pytest.raises(AlreadyFinalized):
            finalize_collection(collection_id=cid, lamella_count=9)
        db.session.rollback()

        # Nothing changed — including no accidental re-lock side effects.
        assert db.session.get(Collection, cid).lamella_count is None


def test_finalize_collection_rejects_unknown_id(app):
    with app.app_context():
        with pytest.raises(ValueError, match="No collection"):
            finalize_collection(collection_id=999999)


def test_finalize_collection_rejects_bad_int(app, session_id):
    with app.app_context():
        collection = make_collection(session_id, "/data/bad-int")
        db.session.commit()
        cid = collection.id

        with pytest.raises(ValueError, match="not a valid integer"):
            finalize_collection(collection_id=cid, lamella_count="not-a-number")
        db.session.rollback()

        # The row is untouched, including editable — a bad count shouldn't
        # still lock the record.
        updated = db.session.get(Collection, cid)
        assert updated.editable is True


def test_finalize_collection_does_not_lock_when_only_one_count_is_bad(app, session_id):
    """total_image_count and lamella_count are both validated before either is assigned."""
    with app.app_context():
        collection = make_collection(session_id, "/data/partial-bad")
        db.session.commit()
        cid = collection.id

        with pytest.raises(ValueError):
            finalize_collection(collection_id=cid, total_image_count=50, lamella_count="oops")
        db.session.rollback()

        updated = db.session.get(Collection, cid)
        assert updated.total_image_count is None
        assert updated.editable is True


# --- API route -----------------------------------------------------------


def test_bulk_finalize_route_mixed_batch(app, client, session_id):
    with app.app_context():
        ok = make_collection(session_id, "/data/ok")
        already = make_collection(session_id, "/data/already-locked", editable=False)
        db.session.commit()
        ok_id, already_id = ok.id, already.id

    resp = post_json(client, "/api/collection/bulk_finalize", {
        "rows": [
            {"id": ok_id, "total_image_count": 42, "lamella_count": 1},
            {"id": already_id, "lamella_count": 5},
            {"id": 999999},
            {"data_location": "/data/does-not-exist"},
        ]
    })
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["finalized_ids"] == [ok_id]
    assert body["already_finalized_ids"] == [already_id]
    assert len(body["errors"]) == 2

    with app.app_context():
        assert db.session.get(Collection, ok_id).total_image_count == 42
        assert db.session.get(Collection, ok_id).editable is False
        # Untouched — the already-locked row's values weren't overwritten.
        assert db.session.get(Collection, already_id).lamella_count is None


def test_bulk_finalize_route_allows_editor(app, client, session_id):
    """Locking is allowed for Editor too, matching update_collection's own rule."""
    with app.app_context():
        collection = make_collection(session_id, "/data/editor-owned")
        db.session.commit()
        cid = collection.id

        editor_role = Role(name="Editor")
        db.session.add(editor_role)
        editor = Person("Ed", "Itor", "editor-only@gmail.com", "editor-net-id")
        editor.roles.append(editor_role)
        db.session.add(editor)
        db.session.commit()

    app.config["DEV_USER_EMAIL"] = "editor-only@gmail.com"

    resp = post_json(client, "/api/collection/bulk_finalize", {
        "rows": [{"id": cid, "lamella_count": 4}]
    })
    assert resp.status_code == 200
    assert json.loads(resp.data)["finalized_ids"] == [cid]
