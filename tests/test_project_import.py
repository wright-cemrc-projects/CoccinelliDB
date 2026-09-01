import json

import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Facility, Person, Project, project_person_link
from app.services.project_import_service import (
    find_or_create_person,
    find_or_create_project,
    link_person_to_project,
)


@pytest.fixture()
def facility(app):
    with app.app_context():
        f = Facility(name="MCCET")
        db.session.add(f)
        db.session.commit()
        yield f.id


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})


# --- service layer -----------------------------------------------------


def test_find_or_create_project_creates_then_matches(app, facility):
    with app.app_context():
        first = find_or_create_project("P-100", facility)
        assert first.created is True
        db.session.commit()

        second = find_or_create_project("P-100", facility)
        assert second.created is False
        assert second.record.id == first.record.id


def test_find_or_create_project_rejects_blank_id(app, facility):
    with app.app_context():
        with pytest.raises(ValueError, match="project_id is required"):
            find_or_create_project("  ", facility)


def test_find_or_create_project_rejects_unknown_facility(app):
    with app.app_context():
        with pytest.raises(ValueError, match="No facility"):
            find_or_create_project("P-100", 999)


def test_project_id_is_globally_unique_at_the_db_level(app, facility):
    with app.app_context():
        p1 = Project("P-100")
        p1.facility_id = facility
        db.session.add(p1)
        db.session.commit()

        p2 = Project("P-100")
        p2.facility_id = facility
        db.session.add(p2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_find_or_create_person_matches_by_email(app):
    with app.app_context():
        first = find_or_create_person("Yan", "Zhuang", "yzhuang63@wisc.edu", "9081234567")
        assert first.created is True
        db.session.commit()

        second = find_or_create_person("Different", "Name", "yzhuang63@wisc.edu", None)
        assert second.created is False
        assert second.record.id == first.record.id


def test_find_or_create_person_matches_by_net_id_when_email_differs(app):
    with app.app_context():
        first = find_or_create_person("Yan", "Zhuang", "yzhuang63@wisc.edu", "9081234567")
        db.session.commit()

        # A re-import with a corrected email but the same net_id should still
        # match the existing person rather than creating a duplicate.
        second = find_or_create_person("Yan", "Zhuang", "y.zhuang@newdomain.edu", "9081234567")
        assert second.created is False
        assert second.record.id == first.record.id


def test_find_or_create_person_allows_no_net_id(app):
    with app.app_context():
        result = find_or_create_person("Outside", "Collaborator", "outside.collaborator@gmail.com", None)
        assert result.created is True
        assert result.record.net_id is None
        db.session.commit()


def test_find_or_create_person_requires_email(app):
    with app.app_context():
        with pytest.raises(ValueError, match="email is required"):
            find_or_create_person("A", "B", "", None)


def test_find_or_create_person_requires_name_to_create(app):
    with app.app_context():
        with pytest.raises(ValueError, match="first_name and last_name"):
            find_or_create_person("", "", "new-person@example.com", None)


def test_link_person_to_project_upserts_role(app, facility):
    with app.app_context():
        project = find_or_create_project("P-100", facility).record
        person = find_or_create_person("Yan", "Zhuang", "yzhuang63@wisc.edu", "9081234567").record
        db.session.flush()

        assert link_person_to_project(project, person, "PI") is True
        db.session.commit()

        # Re-linking the same pair updates the role instead of erroring or duplicating.
        assert link_person_to_project(project, person, "Co-PI") is False
        db.session.commit()

        rows = db.session.execute(
            db.select(project_person_link).filter_by(project_id=project.id, person_id=person.id)
        ).fetchall()
        assert len(rows) == 1
        assert rows[0].role == "Co-PI"


# --- API routes ----------------------------------------------------------


def test_create_project_rejects_duplicate_project_id(client, facility):
    first = post_json(client, "/api/projects", {"project_id": "P-100", "facility_id": facility})
    assert first.status_code == 200

    dup = post_json(client, "/api/projects", {"project_id": "P-100", "facility_id": facility})
    assert dup.status_code == 409
    assert "already in use" in json.loads(dup.data)["error"]


def test_find_or_create_project_route_is_idempotent(client, facility):
    first = post_json(client, "/api/projects/find_or_create", {"project_id": "P-100", "facility_id": facility})
    assert first.status_code == 200
    body1 = json.loads(first.data)
    assert body1["created"] is True

    second = post_json(client, "/api/projects/find_or_create", {"project_id": "P-100", "facility_id": facility})
    body2 = json.loads(second.data)
    assert body2["created"] is False
    assert body2["id"] == body1["id"]


def test_find_or_create_person_route_is_idempotent(client):
    first = post_json(
        client,
        "/api/persons/find_or_create",
        {"first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu", "net_id": "9081234567"},
    )
    assert first.status_code == 200
    body1 = json.loads(first.data)
    assert body1["created"] is True

    second = post_json(
        client,
        "/api/persons/find_or_create",
        {"first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu"},
    )
    body2 = json.loads(second.data)
    assert body2["created"] is False
    assert body2["id"] == body1["id"]


def test_link_and_unlink_project_person_routes(app, client, facility):
    project_id = json.loads(
        post_json(client, "/api/projects/find_or_create", {"project_id": "P-100", "facility_id": facility}).data
    )["id"]
    person_id = json.loads(
        post_json(
            client,
            "/api/persons/find_or_create",
            {"first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu", "net_id": "908"},
        ).data
    )["id"]

    link_resp = post_json(
        client, f"/api/projects/{project_id}/persons", {"person_id": person_id, "role": "PI"}
    )
    assert link_resp.status_code == 200

    get_resp = client.get(f"/api/projects/{project_id}")
    persons = json.loads(get_resp.data)["persons"]
    assert persons == [
        {"person_id": person_id, "first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu", "role": "PI"}
    ]

    unlink_resp = client.delete(f"/api/projects/{project_id}/persons/{person_id}")
    assert unlink_resp.status_code == 200
    assert json.loads(client.get(f"/api/projects/{project_id}").data)["persons"] == []
