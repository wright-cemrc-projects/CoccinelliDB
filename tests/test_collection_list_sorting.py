import json
from datetime import datetime

import pytest

from app import db
from app.models import Collection, Facility, Instrument, InstrumentSession


@pytest.fixture()
def three_collections(app):
    """Three collections whose id order and start_date order deliberately differ,
    so a test can tell which field the response was actually sorted by."""
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

        # Inserted in this id order, but with start_date deliberately reversed.
        specs = [
            ("/data/first-created-latest-start", datetime(2026, 3, 3)),
            ("/data/second-created-earliest-start", datetime(2026, 3, 1)),
            ("/data/third-created-middle-start", datetime(2026, 3, 2)),
        ]
        ids_by_location = {}
        for location, start in specs:
            c = Collection(data_location=location, start_date=start, instrument_session_id=session.id)
            db.session.add(c)
            db.session.flush()
            ids_by_location[location] = c.id
        db.session.commit()
        return ids_by_location


def get_locations(client, query=""):
    resp = client.get(f"/api/collection{query}")
    assert resp.status_code == 200
    return [row["data_location"] for row in json.loads(resp.data)]


def test_sort_by_start_date_ascending(client, three_collections):
    assert get_locations(client, "?_sort=start_date&_order=asc") == [
        "/data/second-created-earliest-start",
        "/data/third-created-middle-start",
        "/data/first-created-latest-start",
    ]


def test_sort_by_start_date_descending(client, three_collections):
    assert get_locations(client, "?_sort=start_date&_order=desc") == [
        "/data/first-created-latest-start",
        "/data/third-created-middle-start",
        "/data/second-created-earliest-start",
    ]


def test_sort_by_id_still_works(client, three_collections):
    assert get_locations(client, "?_sort=id&_order=asc") == [
        "/data/first-created-latest-start",
        "/data/second-created-earliest-start",
        "/data/third-created-middle-start",
    ]
    assert get_locations(client, "?_sort=id&_order=desc") == [
        "/data/third-created-middle-start",
        "/data/second-created-earliest-start",
        "/data/first-created-latest-start",
    ]


def test_unsortable_field_is_ignored_not_an_error(client, three_collections):
    # data_location isn't in the allowed sort fields — should be silently
    # ignored rather than raising or being applied.
    resp = client.get("/api/collection?_sort=data_location&_order=asc")
    assert resp.status_code == 200
    assert len(json.loads(resp.data)) == 3
