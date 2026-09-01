import json
from datetime import datetime, time

import pytest

from app import db
from app.models import Collection, InstrumentSession, SessionGroup, session_person_link
from routes.main_routes import day_boundaries, split_session_by_day


@pytest.fixture()
def session_fixtures(app):
    """A facility, instrument, project, and person to hang sessions off of."""
    with app.app_context():
        from app.models import Facility, Instrument, Person, Project

        facility = Facility(name="MCCET")
        db.session.add(facility)
        db.session.flush()

        instrument = Instrument(name="Krios", facility_id=facility.id)
        project = Project(project_id="P-001")
        project.facility_id = facility.id
        person = Person("Yan", "Zhuang", "yzhuang63@wisc.edu", "9084938471")
        db.session.add_all([instrument, project, person])
        db.session.commit()

        yield {
            "facility_id": facility.id,
            "instrument_id": instrument.id,
            "project_id": project.id,
            "person_id": person.id,
        }


def make_session(ids, start, end, hours=24.0):
    session = InstrumentSession(
        start_date=start,
        end_date=end,
        facility_id=ids["facility_id"],
        instrument_id=ids["instrument_id"],
        project_id=ids["project_id"],
    )
    db.session.add(session)
    db.session.flush()
    db.session.execute(
        session_person_link.insert().values(
            session_id=session.id,
            person_id=ids["person_id"],
            onsite=True,
            role="operator",
            hours=hours,
            remote_access_level="remote control",
        )
    )
    db.session.commit()
    return session


def test_day_boundaries_are_at_the_requested_clock_time():
    boundaries = day_boundaries(
        datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 4, 16, 0), time(9, 0)
    )
    assert boundaries == [datetime(2026, 3, 3, 9, 0), datetime(2026, 3, 4, 9, 0)]


def test_day_boundaries_excludes_the_session_endpoints():
    # A session that starts exactly on the boundary shouldn't be cut at its own start,
    # and one ending exactly on a boundary shouldn't get a zero-length trailing piece.
    boundaries = day_boundaries(
        datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 3, 9, 0), time(9, 0)
    )
    assert boundaries == []


def test_split_by_day_produces_contiguous_pieces(app, session_fixtures):
    with app.app_context():
        session = make_session(
            session_fixtures, datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 4, 16, 0)
        )
        original_id = session.id

        group, session_ids = split_session_by_day(session, time(9, 0))
        db.session.commit()

        assert session_ids[0] == original_id
        assert len(session_ids) == 3

        pieces = [db.session.get(InstrumentSession, sid) for sid in session_ids]
        ranges = [(p.start_date, p.end_date) for p in pieces]
        assert ranges == [
            (datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 3, 9, 0)),
            (datetime(2026, 3, 3, 9, 0), datetime(2026, 3, 4, 9, 0)),
            (datetime(2026, 3, 4, 9, 0), datetime(2026, 3, 4, 16, 0)),
        ]
        # Contiguous: no gaps, no overlap, same total span as the original.
        for earlier, later in zip(pieces, pieces[1:]):
            assert earlier.end_date == later.start_date

        # Every piece carries the original's facility/project/instrument and group.
        assert all(p.session_group_id == group.id for p in pieces)
        assert all(p.instrument_id == session_fixtures["instrument_id"] for p in pieces)
        assert all(p.project_id == session_fixtures["project_id"] for p in pieces)


def test_split_by_day_keeps_hours_on_the_original_only(app, session_fixtures):
    with app.app_context():
        session = make_session(
            session_fixtures, datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 4, 16, 0), hours=24.0
        )
        original_id = session.id
        _, session_ids = split_session_by_day(session, time(9, 0))
        db.session.commit()

        hours_by_session = {
            link.session_id: link.hours
            for link in db.session.execute(db.select(session_person_link)).fetchall()
        }
        assert hours_by_session[original_id] == 24.0
        assert all(hours_by_session[sid] == 0 for sid in session_ids[1:])
        # Participants are still on every piece, just without the hours.
        assert set(hours_by_session) == set(session_ids)


def test_split_by_day_moves_collections_onto_the_covering_piece(app, session_fixtures):
    with app.app_context():
        session = make_session(
            session_fixtures, datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 4, 16, 0)
        )
        day_one = Collection(
            data_location="/data/one",
            start_date=datetime(2026, 3, 2, 20, 0),
            instrument_session_id=session.id,
        )
        day_three = Collection(
            data_location="/data/three",
            start_date=datetime(2026, 3, 4, 11, 0),
            instrument_session_id=session.id,
        )
        undated = Collection(data_location="/data/undated", instrument_session_id=session.id)
        db.session.add_all([day_one, day_three, undated])
        db.session.commit()

        _, session_ids = split_session_by_day(session, time(9, 0))
        db.session.commit()

        assert db.session.get(Collection, day_one.id).instrument_session_id == session_ids[0]
        assert db.session.get(Collection, day_three.id).instrument_session_id == session_ids[2]
        # Nothing to place an undated collection on, so it stays put.
        assert db.session.get(Collection, undated.id).instrument_session_id == session_ids[0]


def test_split_by_day_rejects_a_session_that_crosses_no_boundary(app, session_fixtures):
    with app.app_context():
        session = make_session(
            session_fixtures, datetime(2026, 3, 2, 10, 0), datetime(2026, 3, 2, 18, 0)
        )
        with pytest.raises(ValueError, match="does not cross"):
            split_session_by_day(session, time(9, 0))


def test_split_by_day_reuses_an_existing_group(app, session_fixtures):
    with app.app_context():
        group = SessionGroup(name="Existing block")
        db.session.add(group)
        db.session.flush()
        session = make_session(
            session_fixtures, datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 4, 16, 0)
        )
        session.session_group_id = group.id
        db.session.commit()

        result_group, _ = split_session_by_day(session, time(9, 0))
        assert result_group.id == group.id
        assert db.session.execute(db.select(db.func.count(SessionGroup.id))).scalar() == 1


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})


def test_split_endpoint_defaults_to_nine_am(app, client, session_fixtures):
    with app.app_context():
        session = make_session(
            session_fixtures, datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 4, 16, 0)
        )
        session_id = session.id

    resp = post_json(client, f"/api/instrumentsession/{session_id}/split", {})
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert len(body["session_ids"]) == 3
    assert body["session_group_id"] is not None

    with app.app_context():
        pieces = [db.session.get(InstrumentSession, sid) for sid in body["session_ids"]]
        assert [p.start_date for p in pieces[1:]] == [
            datetime(2026, 3, 3, 9, 0),
            datetime(2026, 3, 4, 9, 0),
        ]


def test_split_endpoint_honours_a_custom_day_start_time(app, client, session_fixtures):
    with app.app_context():
        session = make_session(
            session_fixtures, datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 4, 16, 0)
        )
        session_id = session.id

    resp = post_json(
        client, f"/api/instrumentsession/{session_id}/split", {"day_start_time": "07:30"}
    )
    assert resp.status_code == 200

    with app.app_context():
        pieces = [
            db.session.get(InstrumentSession, sid)
            for sid in json.loads(resp.data)["session_ids"]
        ]
        assert [p.start_date for p in pieces[1:]] == [
            datetime(2026, 3, 3, 7, 30),
            datetime(2026, 3, 4, 7, 30),
        ]


def test_split_endpoint_rejects_an_unreadable_time(app, client, session_fixtures):
    with app.app_context():
        session = make_session(
            session_fixtures, datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 4, 16, 0)
        )
        session_id = session.id

    resp = post_json(
        client, f"/api/instrumentsession/{session_id}/split", {"day_start_time": "breakfast"}
    )
    assert resp.status_code == 400
    assert "breakfast" in json.loads(resp.data)["error"]

    with app.app_context():
        # Nothing was written on the rejected request.
        assert db.session.execute(db.select(db.func.count(InstrumentSession.id))).scalar() == 1


def test_split_preview_reports_ranges_without_changing_anything(app, client, session_fixtures):
    with app.app_context():
        session = make_session(
            session_fixtures, datetime(2026, 3, 2, 14, 0), datetime(2026, 3, 4, 16, 0)
        )
        session_id = session.id

    resp = post_json(
        client, f"/api/instrumentsession/{session_id}/split/preview", {"day_start_time": "09:00"}
    )
    assert resp.status_code == 200
    ranges = json.loads(resp.data)["ranges"]
    assert [r["start_date"] for r in ranges] == [
        "2026-03-02T14:00:00",
        "2026-03-03T09:00:00",
        "2026-03-04T09:00:00",
    ]

    with app.app_context():
        assert db.session.execute(db.select(db.func.count(InstrumentSession.id))).scalar() == 1


def test_session_group_membership_can_be_edited(app, client, session_fixtures):
    with app.app_context():
        first = make_session(
            session_fixtures, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 17, 0)
        )
        second = make_session(
            session_fixtures, datetime(2026, 3, 3, 9, 0), datetime(2026, 3, 3, 17, 0)
        )
        first_id, second_id = first.id, second.id

    resp = post_json(
        client,
        "/api/sessiongroups",
        {"name": "March Krios block", "session_ids": [first_id, second_id]},
    )
    assert resp.status_code == 200
    group_id = json.loads(resp.data)["id"]

    get_resp = client.get(f"/api/sessiongroups/{group_id}")
    assert {s["id"] for s in json.loads(get_resp.data)["sessions"]} == {first_id, second_id}

    # Dropping a session from the list unlinks it without deleting it.
    client.patch(
        f"/api/sessiongroups/{group_id}",
        data=json.dumps({"session_ids": [first_id]}),
        headers={"Content-Type": "application/json"},
    )
    with app.app_context():
        assert db.session.get(InstrumentSession, first_id).session_group_id == group_id
        assert db.session.get(InstrumentSession, second_id).session_group_id is None

    # Editing only the name leaves membership alone.
    client.patch(
        f"/api/sessiongroups/{group_id}",
        data=json.dumps({"name": "Renamed"}),
        headers={"Content-Type": "application/json"},
    )
    with app.app_context():
        assert db.session.get(InstrumentSession, first_id).session_group_id == group_id


def test_deleting_a_group_unlinks_but_keeps_its_sessions(app, client, session_fixtures):
    with app.app_context():
        session = make_session(
            session_fixtures, datetime(2026, 3, 2, 9, 0), datetime(2026, 3, 2, 17, 0)
        )
        session_id = session.id

    group_id = json.loads(
        post_json(client, "/api/sessiongroups", {"name": "Block", "session_ids": [session_id]}).data
    )["id"]

    assert client.delete(f"/api/sessiongroups/{group_id}").status_code == 200

    with app.app_context():
        survivor = db.session.get(InstrumentSession, session_id)
        assert survivor is not None
        assert survivor.session_group_id is None
        assert db.session.get(SessionGroup, group_id) is None
