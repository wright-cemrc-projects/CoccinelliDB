"""Regression test: editing an InstrumentSession's facility had no effect.

update_session handled start_date, end_date, instrument_id, project_id,
notes, session_group_id, and persons, but never looked at facility_id at all
— so a PATCH that changed it silently kept the old value while still
reporting success, and the Edit page's Facility field appeared to do nothing.
"""
import json
from datetime import datetime

import pytest

from app import db
from app.models import Facility, Instrument, InstrumentSession


@pytest.fixture()
def two_facilities(app):
    with app.app_context():
        original = Facility(name="MCCET")
        other = Facility(name="Other Facility")
        db.session.add_all([original, other])
        db.session.flush()

        instrument = Instrument(name="Krios", facility_id=original.id)
        db.session.add(instrument)
        db.session.flush()

        session = InstrumentSession(
            facility_id=original.id,
            instrument_id=instrument.id,
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 2),
        )
        db.session.add(session)
        db.session.commit()

        return {"session_id": session.id, "original_facility_id": original.id, "other_facility_id": other.id}


def patch_json(client, url, payload):
    return client.patch(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})


def test_updating_facility_id_actually_changes_it(app, client, two_facilities):
    resp = patch_json(
        client,
        f"/api/instrumentsession/{two_facilities['session_id']}",
        {"facility_id": two_facilities["other_facility_id"]},
    )
    assert resp.status_code == 200

    with app.app_context():
        session = db.session.get(InstrumentSession, two_facilities["session_id"])
        assert session.facility_id == two_facilities["other_facility_id"]


def test_omitting_facility_id_leaves_it_unchanged(app, client, two_facilities):
    resp = patch_json(
        client,
        f"/api/instrumentsession/{two_facilities['session_id']}",
        {"notes": "unrelated edit"},
    )
    assert resp.status_code == 200

    with app.app_context():
        session = db.session.get(InstrumentSession, two_facilities["session_id"])
        assert session.facility_id == two_facilities["original_facility_id"]
