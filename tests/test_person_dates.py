"""Regression tests for a report that creating/editing persons was broken.

Root causes found:

1. create_person and update_person parsed start_date/end_date with
   `datetime.fromisoformat(request.json["start_date"])` whenever the key was
   present at all — but the client always sends the key, as `null` when the
   date picker is left blank (see persons/create.tsx and persons/edit.tsx).
   `fromisoformat(None)` raises TypeError, so creating or editing a person
   without filling in both optional dates failed outright.

2. update_person's except block had no db.session.rollback() and no error
   HTTP status code, so a failed update (including the date crash above)
   returned HTTP 200 with an unchecked "err" key — the UI showed success
   while nothing was actually saved. Same bug shape already found and fixed
   in delete_session; delete_person had it too.

3. update_person silently ignored the "roles" field entirely — editing a
   person's roles from the Edit form had no effect on the saved record.

4. persons/edit.tsx never converted the DatePicker's dayjs value to an ISO
   string before submitting (persons/create.tsx does); touching a date field
   while editing would send a raw dayjs-shaped object instead of a string.
   Covered here only insofar as the backend must reject non-ISO strings
   cleanly rather than 500ing; the client-side fix has no direct test here.
"""
import json

import pytest

from app import db
from app.models import Person, Role


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})


def patch_json(client, url, payload):
    return client.patch(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})


def test_create_person_with_blank_dates_succeeds(client):
    resp = post_json(client, "/api/persons", {
        "first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu", "net_id": "908",
        "start_date": None, "end_date": None,
    })
    assert resp.status_code == 200

    person_list = json.loads(client.get("/api/persons").data)
    created = next(p for p in person_list if p["email"] == "yzhuang63@wisc.edu")
    assert created["start_date"] is None
    assert created["end_date"] is None


def test_create_person_with_dates_omitted_entirely_still_succeeds(client):
    # No start_date/end_date keys at all (a stricter client, or a script).
    resp = post_json(client, "/api/persons", {
        "first_name": "Jamie", "last_name": "Lee", "email": "jlee@wisc.edu", "net_id": "909",
    })
    assert resp.status_code == 200


def test_create_person_with_real_dates_still_works(client):
    resp = post_json(client, "/api/persons", {
        "first_name": "Al", "last_name": "Ex", "email": "alex@wisc.edu", "net_id": "910",
        "start_date": "2026-01-01T00:00:00", "end_date": "2026-06-01T00:00:00",
    })
    assert resp.status_code == 200
    person_list = json.loads(client.get("/api/persons").data)
    created = next(p for p in person_list if p["email"] == "alex@wisc.edu")
    assert created["start_date"] == "2026-01-01T00:00:00"
    assert created["end_date"] == "2026-06-01T00:00:00"


@pytest.fixture()
def person_id(app, client):
    with app.app_context():
        person = Person("Yan", "Zhuang", "yzhuang63@wisc.edu", "908")
        db.session.add(person)
        db.session.commit()
        return person.id


def test_update_person_with_blank_dates_succeeds_and_actually_saves(app, client, person_id):
    resp = patch_json(client, f"/api/persons/{person_id}", {
        "organization": "UW Madison", "start_date": None, "end_date": None,
    })
    assert resp.status_code == 200

    with app.app_context():
        updated = db.session.get(Person, person_id)
        # The bug: this used to come back 200 while silently saving nothing.
        assert updated.organization == "UW Madison"
        assert updated.start_date is None


def test_update_person_failure_is_not_reported_as_success(app, client, person_id):
    # An unparseable, non-null date should fail loudly, not with a 200.
    resp = patch_json(client, f"/api/persons/{person_id}", {"start_date": "not-a-date"})
    assert resp.status_code == 400
    body = json.loads(resp.data)
    assert "error" in body

    with app.app_context():
        # Nothing should have been committed.
        assert db.session.get(Person, person_id).start_date is None


def test_update_person_with_real_dates_still_works(app, client, person_id):
    resp = patch_json(client, f"/api/persons/{person_id}", {
        "start_date": "2026-01-01T00:00:00", "end_date": "2026-06-01T00:00:00",
    })
    assert resp.status_code == 200
    with app.app_context():
        updated = db.session.get(Person, person_id)
        assert updated.start_date.isoformat() == "2026-01-01T00:00:00"
        assert updated.end_date.isoformat() == "2026-06-01T00:00:00"


def test_update_person_roles_are_actually_saved(app, client, person_id):
    with app.app_context():
        role = Role(name="Trainee")
        db.session.add(role)
        db.session.commit()
        role_id = role.id

    resp = patch_json(client, f"/api/persons/{person_id}", {"roles": [role_id]})
    assert resp.status_code == 200

    with app.app_context():
        updated = db.session.get(Person, person_id)
        # The bug: update_person didn't look at "roles" at all.
        assert [r.name for r in updated.roles] == ["Trainee"]


def test_update_person_roles_can_be_cleared(app, client, person_id):
    with app.app_context():
        role = Role(name="Trainee")
        db.session.add(role)
        person = db.session.get(Person, person_id)
        person.roles.append(role)
        db.session.commit()

    resp = patch_json(client, f"/api/persons/{person_id}", {"roles": []})
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(Person, person_id).roles == []


def test_delete_person_failure_is_not_reported_as_success(client):
    resp = client.delete("/api/persons/999999")
    assert resp.status_code == 400
    assert "error" in json.loads(resp.data)
