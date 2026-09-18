import json
from datetime import datetime

import pytest

from app import db
from app.models import (
    Collection,
    Facility,
    Instrument,
    InstrumentSession,
    Person,
    Project,
    session_person_link,
)
from app.services.session_merge_service import find_merge_candidates, merge_sessions, plan_merge


@pytest.fixture()
def ids(app):
    with app.app_context():
        facility = Facility(name="MCCET")
        db.session.add(facility)
        db.session.flush()

        other_facility = Facility(name="Other Facility")
        db.session.add(other_facility)
        db.session.flush()

        instrument = Instrument(name="Krios", facility_id=facility.id)
        other_instrument = Instrument(name="Talos", facility_id=facility.id)
        project = Project(project_id="P-001")
        project.facility_id = facility.id
        other_project = Project(project_id="P-002")
        other_project.facility_id = facility.id
        person_a = Person("Yan", "Zhuang", "yzhuang63@wisc.edu", "908")
        person_b = Person("Jamie", "Lee", "jlee@wisc.edu", "909")
        db.session.add_all([instrument, other_instrument, project, other_project, person_a, person_b])
        db.session.commit()

        return {
            "facility_id": facility.id,
            "other_facility_id": other_facility.id,
            "instrument_id": instrument.id,
            "other_instrument_id": other_instrument.id,
            "project_id": project.id,
            "other_project_id": other_project.id,
            "person_a_id": person_a.id,
            "person_b_id": person_b.id,
        }


def make_session(ids, start, end, notes=None, facility_id=None, instrument_id=None, project_id=None):
    session = InstrumentSession(
        start_date=start,
        end_date=end,
        notes=notes,
        facility_id=facility_id or ids["facility_id"],
        instrument_id=instrument_id or ids["instrument_id"],
        project_id=project_id if project_id is not None else ids["project_id"],
    )
    db.session.add(session)
    db.session.flush()
    return session


def add_person(session, person_id, hours=0.0, onsite=True, role="operator", remote_access_level="remote view"):
    db.session.execute(session_person_link.insert().values(
        session_id=session.id,
        person_id=person_id,
        onsite=onsite,
        role=role,
        hours=hours,
        remote_access_level=remote_access_level,
    ))


def person_rows(session_id):
    return {
        r.person_id: r for r in db.session.execute(
            db.select(session_person_link).filter_by(session_id=session_id)
        ).fetchall()
    }


# --- service layer: happy path -------------------------------------------


def test_merge_widens_time_range_to_cover_both_sessions(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(ids, datetime(2026, 3, 1, 10, 30), datetime(2026, 3, 1, 13, 0))
        db.session.commit()

        plan = merge_sessions(primary.id, [other.id])
        db.session.commit()

        merged = db.session.get(InstrumentSession, primary.id)
        assert merged.start_date == datetime(2026, 3, 1, 9, 0)
        assert merged.end_date == datetime(2026, 3, 1, 13, 0)
        assert plan.start_date == merged.start_date


def test_merge_deletes_the_other_session(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0))
        db.session.commit()
        other_id = other.id

        merge_sessions(primary.id, [other_id])
        db.session.commit()

        assert db.session.get(InstrumentSession, other_id) is None


def test_merge_concatenates_notes_with_session_labels(app, ids):
    with app.app_context():
        primary = make_session(
            ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0), notes="Scope alignment was off."
        )
        other = make_session(
            ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0), notes="Continued after recalibration."
        )
        db.session.commit()

        plan = merge_sessions(primary.id, [other.id])
        db.session.commit()

        merged = db.session.get(InstrumentSession, primary.id)
        assert f"Session {primary.id}" in merged.notes
        assert "Scope alignment was off." in merged.notes
        assert f"Session {other.id}" in merged.notes
        assert "Continued after recalibration." in merged.notes
        assert merged.notes == plan.notes


def test_merge_skips_blank_notes(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0), notes=None)
        other = make_session(
            ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0), notes="  "
        )
        db.session.commit()

        merge_sessions(primary.id, [other.id])
        db.session.commit()

        assert db.session.get(InstrumentSession, primary.id).notes is None


def test_merge_sums_hours_for_a_person_on_both_sessions(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0))
        add_person(primary, ids["person_a_id"], hours=3.0, role="operator")
        add_person(other, ids["person_a_id"], hours=2.0, role="trainee")
        db.session.commit()

        merge_sessions(primary.id, [other.id])
        db.session.commit()

        rows = person_rows(primary.id)
        assert rows[ids["person_a_id"]].hours == 5.0
        # Non-hours fields come from whichever session lists the person first: primary.
        assert rows[ids["person_a_id"]].role == "operator"


def test_merge_unions_persons_unique_to_each_session(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0))
        add_person(primary, ids["person_a_id"], hours=3.0)
        add_person(other, ids["person_b_id"], hours=4.0)
        db.session.commit()

        merge_sessions(primary.id, [other.id])
        db.session.commit()

        rows = person_rows(primary.id)
        assert set(rows) == {ids["person_a_id"], ids["person_b_id"]}
        assert rows[ids["person_b_id"]].hours == 4.0


def test_merge_moves_collections_from_other_sessions(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0))
        collection = Collection(data_location="/data/dup", instrument_session_id=other.id)
        db.session.add(collection)
        db.session.commit()
        cid = collection.id

        merge_sessions(primary.id, [other.id])
        db.session.commit()

        assert db.session.get(Collection, cid).instrument_session_id == primary.id


def test_merge_of_three_sessions_at_once(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 10, 0))
        second = make_session(ids, datetime(2026, 3, 1, 9, 30), datetime(2026, 3, 1, 11, 0))
        third = make_session(ids, datetime(2026, 3, 1, 10, 30), datetime(2026, 3, 1, 12, 0))
        db.session.commit()
        second_id, third_id = second.id, third.id

        merge_sessions(primary.id, [second_id, third_id])
        db.session.commit()

        merged = db.session.get(InstrumentSession, primary.id)
        assert merged.start_date == datetime(2026, 3, 1, 9, 0)
        assert merged.end_date == datetime(2026, 3, 1, 12, 0)
        assert db.session.get(InstrumentSession, second_id) is None
        assert db.session.get(InstrumentSession, third_id) is None


# --- service layer: validation --------------------------------------------


def test_merge_requires_at_least_one_other_session(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        db.session.commit()
        with pytest.raises(ValueError, match="at least one"):
            plan_merge(primary.id, [])


def test_merge_rejects_primary_listed_as_its_own_other(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        db.session.commit()
        with pytest.raises(ValueError, match="merged with itself"):
            plan_merge(primary.id, [primary.id])


def test_merge_rejects_unknown_session_id(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        db.session.commit()
        with pytest.raises(ValueError, match="not found"):
            plan_merge(primary.id, [999999])


def test_merge_rejects_different_instrument(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(
            ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0),
            instrument_id=ids["other_instrument_id"],
        )
        db.session.commit()
        with pytest.raises(ValueError, match="different instrument"):
            plan_merge(primary.id, [other.id])


def test_merge_rejects_different_facility(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(
            ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0),
            facility_id=ids["other_facility_id"],
        )
        db.session.commit()
        with pytest.raises(ValueError, match="different facility"):
            plan_merge(primary.id, [other.id])


def test_merge_rejects_missing_dates(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(ids, None, None)
        db.session.commit()
        with pytest.raises(ValueError, match="missing a start or end date"):
            plan_merge(primary.id, [other.id])


def test_merge_blocked_by_a_finalized_collection_on_the_other_session(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0))
        locked = Collection(data_location="/data/locked", instrument_session_id=other.id, editable=False)
        db.session.add(locked)
        db.session.commit()
        other_id, locked_id = other.id, locked.id

        with pytest.raises(ValueError, match="finalized"):
            merge_sessions(primary.id, [other_id])
        db.session.rollback()

        # Nothing changed — the blocked session and its collection are untouched.
        assert db.session.get(InstrumentSession, other_id) is not None
        assert db.session.get(Collection, locked_id).instrument_session_id == other_id


def test_project_mismatch_is_a_warning_not_a_block(app, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(
            ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0),
            project_id=ids["other_project_id"],
        )
        db.session.commit()

        plan = merge_sessions(primary.id, [other.id])
        db.session.commit()

        assert any("different projects" in w for w in plan.warnings)
        # Primary's own project_id wins.
        assert db.session.get(InstrumentSession, primary.id).project_id == ids["project_id"]


# --- find_merge_candidates -------------------------------------------------


def test_candidates_include_same_day_and_overlap(app, ids):
    with app.app_context():
        session = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        same_day = make_session(ids, datetime(2026, 3, 1, 14, 0), datetime(2026, 3, 1, 16, 0))
        overlapping_next_day = make_session(ids, datetime(2026, 3, 1, 23, 0), datetime(2026, 3, 2, 1, 0))
        different_day = make_session(ids, datetime(2026, 3, 5, 9, 0), datetime(2026, 3, 5, 11, 0))
        different_instrument = make_session(
            ids, datetime(2026, 3, 1, 9, 30), datetime(2026, 3, 1, 10, 30),
            instrument_id=ids["other_instrument_id"],
        )
        db.session.commit()

        candidate_ids = {c.id for c in find_merge_candidates(session)}
        assert same_day.id in candidate_ids
        assert overlapping_next_day.id in candidate_ids
        assert different_day.id not in candidate_ids
        assert different_instrument.id not in candidate_ids
        assert session.id not in candidate_ids


# --- API routes ------------------------------------------------------------


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})


def test_merge_candidates_route_reports_locked_flag(app, client, ids):
    with app.app_context():
        session = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        candidate = make_session(ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0))
        db.session.add(Collection(data_location="/data/x", instrument_session_id=candidate.id, editable=False))
        db.session.commit()
        session_id, candidate_id = session.id, candidate.id

    resp = client.get(f"/api/instrumentsession/{session_id}/merge_candidates")
    assert resp.status_code == 200
    candidates = json.loads(resp.data)["candidates"]
    assert len(candidates) == 1
    assert candidates[0]["id"] == candidate_id
    assert candidates[0]["has_locked_collections"] is True


def test_merge_preview_route_does_not_write(app, client, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 13, 0))
        db.session.commit()
        primary_id, other_id = primary.id, other.id

    resp = post_json(client, "/api/instrumentsession/merge/preview", {
        "primary_id": primary_id, "other_ids": [other_id],
    })
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["end_date"] == "2026-03-01T13:00:00"

    with app.app_context():
        # Preview must not have changed anything.
        assert db.session.get(InstrumentSession, other_id) is not None
        assert db.session.get(InstrumentSession, primary_id).end_date == datetime(2026, 3, 1, 11, 0)


def test_merge_route_applies_and_returns_summary(app, client, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 13, 0))
        db.session.commit()
        primary_id, other_id = primary.id, other.id

    resp = post_json(client, "/api/instrumentsession/merge", {
        "primary_id": primary_id, "other_ids": [other_id],
    })
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["primary_id"] == primary_id
    assert body["other_ids"] == [other_id]

    with app.app_context():
        assert db.session.get(InstrumentSession, other_id) is None
        assert db.session.get(InstrumentSession, primary_id).end_date == datetime(2026, 3, 1, 13, 0)


def test_merge_route_rejects_locked_collection_with_400(app, client, ids):
    with app.app_context():
        primary = make_session(ids, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 11, 0))
        other = make_session(ids, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0))
        db.session.add(Collection(data_location="/data/x", instrument_session_id=other.id, editable=False))
        db.session.commit()
        primary_id, other_id = primary.id, other.id

    resp = post_json(client, "/api/instrumentsession/merge", {
        "primary_id": primary_id, "other_ids": [other_id],
    })
    assert resp.status_code == 400

    with app.app_context():
        assert db.session.get(InstrumentSession, other_id) is not None
