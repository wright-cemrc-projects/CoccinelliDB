import json

import pytest

from app import db
from app.models import Collection, Facility, Instrument, InstrumentSession


@pytest.fixture()
def three_collections(app):
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

        for location in [
            "/data/lee_lab/2026_03_grid1",
            "/data/lee_lab/2026_04_grid2",
            "/data/zhuang_lab/2026_03_gridA",
        ]:
            db.session.add(Collection(data_location=location, instrument_session_id=session.id))
        db.session.commit()


def get_locations(client, query):
    resp = client.get(f"/api/collection{query}")
    assert resp.status_code == 200
    return sorted(row["data_location"] for row in json.loads(resp.data))


def test_search_by_partial_path_matches_multiple(client, three_collections):
    assert get_locations(client, "?data_location_like=lee_lab") == [
        "/data/lee_lab/2026_03_grid1",
        "/data/lee_lab/2026_04_grid2",
    ]


def test_search_by_full_path_matches_one(client, three_collections):
    assert get_locations(client, "?data_location_like=/data/zhuang_lab/2026_03_gridA") == [
        "/data/zhuang_lab/2026_03_gridA",
    ]


def test_search_is_case_insensitive(client, three_collections):
    assert get_locations(client, "?data_location_like=LEE_LAB") == [
        "/data/lee_lab/2026_03_grid1",
        "/data/lee_lab/2026_04_grid2",
    ]


def test_search_with_no_match_returns_empty_list(client, three_collections):
    assert get_locations(client, "?data_location_like=does-not-exist") == []


def test_no_search_param_returns_everything(client, three_collections):
    assert len(get_locations(client, "")) == 3


def test_search_combines_with_sort(client, three_collections):
    assert get_locations(client, "?data_location_like=lee_lab&_sort=start_date&_order=asc") == [
        "/data/lee_lab/2026_03_grid1",
        "/data/lee_lab/2026_04_grid2",
    ]
