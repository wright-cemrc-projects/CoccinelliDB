"""Regression tests for two bugs found together while debugging a report that
sessions in a linked session group couldn't be deleted:

1. delete_session's except block had no db.session.rollback() and no error
   status code, so a failed delete (e.g. one blocked by a linked Collection)
   returned HTTP 200 with an "err" key nobody checked — the UI showed success
   while nothing was actually deleted.

2. InstrumentSession.persons carried cascade="all, delete" on what is a
   many-to-many secondary relationship. That doesn't just clear the
   session_person_link row on delete — it deletes the linked Person record
   itself. Sessions without a blocking Collection "successfully" deleted, but
   silently destroyed any participant's Person row along with them.
"""
import json
from datetime import datetime

import pytest

from app import db
from app.models import Collection, Facility, Instrument, InstrumentSession, Person, session_person_link


@pytest.fixture()
def session_fixtures(app):
    with app.app_context():
        facility = Facility(name="MCCET")
        db.session.add(facility)
        db.session.flush()
        instrument = Instrument(name="Krios", facility_id=facility.id)
        db.session.add(instrument)
        db.session.commit()
        return {"facility_id": facility.id, "instrument_id": instrument.id}


def make_session(ids):
    session = InstrumentSession(
        facility_id=ids["facility_id"],
        instrument_id=ids["instrument_id"],
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 1, 2),
    )
    db.session.add(session)
    db.session.flush()
    return session


def test_delete_with_a_linked_collection_fails_loudly_not_silently(app, client, session_fixtures):
    with app.app_context():
        session = make_session(session_fixtures)
        db.session.add(Collection(data_location="/data/x", instrument_session_id=session.id))
        db.session.commit()
        session_id = session.id

    resp = client.delete(f"/api/instrumentsession/{session_id}")

    # The bug: this used to come back 200 with an unchecked "err" key.
    assert resp.status_code == 400
    body = json.loads(resp.data)
    assert "collection" in body["error"].lower()

    with app.app_context():
        assert db.session.get(InstrumentSession, session_id) is not None


def test_delete_without_collections_still_works(app, client, session_fixtures):
    with app.app_context():
        session = make_session(session_fixtures)
        db.session.commit()
        session_id = session.id

    resp = client.delete(f"/api/instrumentsession/{session_id}")
    assert resp.status_code == 200

    with app.app_context():
        assert db.session.get(InstrumentSession, session_id) is None


def test_deleting_a_session_does_not_delete_its_participants(app, client, session_fixtures):
    """Regression test for the cascade="all, delete" bug on InstrumentSession.persons."""
    with app.app_context():
        session = make_session(session_fixtures)
        person = Person("Yan", "Zhuang", "yzhuang63@wisc.edu", "908")
        db.session.add(person)
        db.session.flush()
        db.session.execute(
            session_person_link.insert().values(
                session_id=session.id,
                person_id=person.id,
                onsite=True,
                role="operator",
                hours=8.0,
                remote_access_level="remote view",
            )
        )
        db.session.commit()
        session_id, person_id = session.id, person.id

    resp = client.delete(f"/api/instrumentsession/{session_id}")
    assert resp.status_code == 200

    with app.app_context():
        assert db.session.get(InstrumentSession, session_id) is None
        # The bug: this Person used to be deleted along with the session.
        assert db.session.get(Person, person_id) is not None

        # The link row itself should still be cleaned up.
        remaining_links = db.session.execute(
            db.select(session_person_link).filter_by(session_id=session_id)
        ).fetchall()
        assert remaining_links == []
