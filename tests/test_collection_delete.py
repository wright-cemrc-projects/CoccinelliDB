import json

import pytest

from app import db
from app.models import Collection, Facility, Instrument, InstrumentSession, Person, Project, Role


@pytest.fixture()
def collection_id(app):
    """A minimal Collection row to delete, plus its InstrumentSession/Instrument/Facility."""
    with app.app_context():
        facility = Facility(name="MCCET")
        db.session.add(facility)
        db.session.flush()

        instrument = Instrument(name="Krios", facility_id=facility.id)
        db.session.add(instrument)
        db.session.flush()

        session = InstrumentSession(facility_id=facility.id, instrument_id=instrument.id)
        db.session.add(session)
        db.session.flush()

        collection = Collection(data_location="/data/one", instrument_session_id=session.id)
        db.session.add(collection)
        db.session.commit()
        return collection.id


def login_as(app, email):
    """Point the test/dev auth bypass at a different seeded person for this request.

    There's no real OIDC session to drive in tests, so DEV_USER_EMAIL (see
    config.TestingConfig and app.attach_current_user) is the only lever for
    switching which user a request runs as.
    """
    app.config["DEV_USER_EMAIL"] = email


def make_editor(app):
    with app.app_context():
        editor_role = Role.query.filter_by(name="Editor").first()
        if not editor_role:
            editor_role = Role(name="Editor")
            db.session.add(editor_role)
        editor = Person("Ed", "Itor", "editor-only@gmail.com", "editor-net-id")
        editor.roles.append(editor_role)
        db.session.add(editor)
        db.session.commit()
        return editor.email


def test_admin_can_delete_a_collection(app, client, collection_id):
    resp = client.delete(f"/api/collection/{collection_id}")
    assert resp.status_code == 200
    assert json.loads(resp.data)["message"] == f"Collection {collection_id} got deleted."

    with app.app_context():
        assert db.session.get(Collection, collection_id) is None


def test_editor_cannot_delete_a_collection(app, client, collection_id):
    editor_email = make_editor(app)
    login_as(app, editor_email)

    resp = client.delete(f"/api/collection/{collection_id}")
    assert resp.status_code == 403

    with app.app_context():
        # Rejected, not just error-messaged: the collection must still be there.
        assert db.session.get(Collection, collection_id) is not None


def test_editor_can_still_read_and_update_collections(app, client, collection_id):
    """Deleting is Admin-only, but Editor's existing GET/PATCH access is untouched."""
    editor_email = make_editor(app)
    login_as(app, editor_email)

    get_resp = client.get(f"/api/collection/{collection_id}")
    assert get_resp.status_code == 200

    patch_resp = client.patch(
        f"/api/collection/{collection_id}",
        data=json.dumps({"collection_type": "SPA"}),
        headers={"Content-Type": "application/json"},
    )
    assert patch_resp.status_code == 200
