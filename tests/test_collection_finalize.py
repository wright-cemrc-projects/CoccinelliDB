import json

import pytest

from app import db
from app.models import Collection, Facility, Instrument, InstrumentSession, Person, Role


@pytest.fixture()
def collection_id(app):
    """A minimal Collection row, plus its InstrumentSession/Instrument/Facility."""
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


def patch_json(client, url, payload):
    return client.patch(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})


def test_new_collection_defaults_to_editable(app, collection_id):
    with app.app_context():
        assert db.session.get(Collection, collection_id).editable is True


def test_lamella_count_can_be_set(client, collection_id):
    resp = patch_json(client, f"/api/collection/{collection_id}", {"lamella_count": 12})
    assert resp.status_code == 200
    assert json.loads(client.get(f"/api/collection/{collection_id}").data)["lamella_count"] == 12


def test_editor_can_finalize_a_collection(app, client, collection_id):
    editor_email = make_editor(app)
    login_as(app, editor_email)

    resp = patch_json(client, f"/api/collection/{collection_id}", {"editable": False})
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(Collection, collection_id).editable is False


def test_finalizing_alongside_other_field_changes_is_allowed(client, collection_id):
    # Locking is only special-cased on the "currently locked" side; a normal
    # edit that also finalizes the record in one request is fine.
    resp = patch_json(client, f"/api/collection/{collection_id}", {
        "lamella_count": 7, "editable": False,
    })
    assert resp.status_code == 200
    body = json.loads(client.get(f"/api/collection/{collection_id}").data)
    assert body["lamella_count"] == 7
    assert body["editable"] is False


def test_finalized_collection_rejects_other_field_edits(app, client, collection_id):
    patch_json(client, f"/api/collection/{collection_id}", {"editable": False})

    resp = patch_json(client, f"/api/collection/{collection_id}", {"lamella_count": 99})
    assert resp.status_code == 400
    assert "finalized" in json.loads(resp.data)["error"].lower()

    with app.app_context():
        assert db.session.get(Collection, collection_id).lamella_count is None


def test_editor_cannot_unlock_a_finalized_collection(app, client, collection_id):
    patch_json(client, f"/api/collection/{collection_id}", {"editable": False})

    editor_email = make_editor(app)
    login_as(app, editor_email)

    resp = patch_json(client, f"/api/collection/{collection_id}", {"editable": True})
    assert resp.status_code == 403
    with app.app_context():
        assert db.session.get(Collection, collection_id).editable is False


def test_admin_can_unlock_then_edit_in_two_requests(app, client, collection_id):
    patch_json(client, f"/api/collection/{collection_id}", {"editable": False})

    unlock_resp = patch_json(client, f"/api/collection/{collection_id}", {"editable": True})
    assert unlock_resp.status_code == 200
    with app.app_context():
        assert db.session.get(Collection, collection_id).editable is True

    edit_resp = patch_json(client, f"/api/collection/{collection_id}", {"lamella_count": 5})
    assert edit_resp.status_code == 200
    with app.app_context():
        assert db.session.get(Collection, collection_id).lamella_count == 5


def test_admin_cannot_unlock_and_edit_in_one_request(app, client, collection_id):
    """Unlocking must be its own request, even for an Admin."""
    patch_json(client, f"/api/collection/{collection_id}", {"editable": False})

    resp = patch_json(client, f"/api/collection/{collection_id}", {
        "editable": True, "lamella_count": 5,
    })
    assert resp.status_code == 400
    with app.app_context():
        record = db.session.get(Collection, collection_id)
        assert record.editable is False
        assert record.lamella_count is None


def test_delete_blocked_while_finalized(app, client, collection_id):
    patch_json(client, f"/api/collection/{collection_id}", {"editable": False})

    resp = client.delete(f"/api/collection/{collection_id}")
    assert resp.status_code == 400
    with app.app_context():
        assert db.session.get(Collection, collection_id) is not None


def test_delete_allowed_once_unlocked(app, client, collection_id):
    patch_json(client, f"/api/collection/{collection_id}", {"editable": False})
    patch_json(client, f"/api/collection/{collection_id}", {"editable": True})

    resp = client.delete(f"/api/collection/{collection_id}")
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(Collection, collection_id) is None


def test_instrument_client_api_blocked_while_finalized(client, collection_id):
    patch_json(client, f"/api/collection/{collection_id}", {"editable": False})

    resp = client.patch(
        f"/api/client/collections/{collection_id}",
        data=json.dumps({"total_image_count": 500}),
        headers={"Content-Type": "application/json", "X-API-Key": "dev-instrument-api-key"},
    )
    assert resp.status_code == 400
    assert "finalized" in json.loads(resp.data)["error"].lower()


def test_instrument_client_api_still_works_while_editable(app, client, collection_id):
    resp = client.patch(
        f"/api/client/collections/{collection_id}",
        data=json.dumps({"total_image_count": 500}),
        headers={"Content-Type": "application/json", "X-API-Key": "dev-instrument-api-key"},
    )
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(Collection, collection_id).total_image_count == 500
