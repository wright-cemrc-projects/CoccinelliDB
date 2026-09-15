"""Tests for scripts/em_microscope_report.py.

scripts/ isn't an importable package (matching the other tools in that
directory), so the module is loaded by path.
"""
import importlib.util
from datetime import datetime
from pathlib import Path

import pytest

from app import db
from app.models import Collection, Facility, Instrument, InstrumentSession

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "em_microscope_report.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("em_microscope_report", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def script():
    return _load_script_module()


@pytest.fixture()
def session_id(app):
    with app.app_context():
        facility = Facility(name="MCCET")
        db.session.add(facility)
        db.session.flush()
        instrument = Instrument(name="Krios", facility_id=facility.id)
        db.session.add(instrument)
        db.session.flush()
        session = InstrumentSession(facility_id=facility.id, instrument_id=instrument.id)
        db.session.add(session)
        db.session.commit()
        return session.id


def make_collection(session_id, **kwargs):
    collection = Collection(instrument_session_id=session_id, **kwargs)
    db.session.add(collection)
    db.session.flush()
    return collection


def test_lamella_count_is_pulled_from_the_collection(app, script, session_id):
    with app.app_context():
        make_collection(
            session_id,
            data_location="/data/with-lamella",
            start_date=datetime(2026, 3, 1),
            lamella_count=4,
        )
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert len(rows) == 1
        assert rows[0]["Lamella Count (FIB-SEM only)"] == 4


def test_lamella_count_is_blank_not_none_when_unset(app, script, session_id):
    with app.app_context():
        make_collection(
            session_id,
            data_location="/data/no-lamella",
            start_date=datetime(2026, 3, 1),
        )
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert rows[0]["Lamella Count (FIB-SEM only)"] == ""


def test_finalized_column_reflects_editable_state(app, script, session_id):
    with app.app_context():
        finalized = make_collection(
            session_id, data_location="/data/finalized", start_date=datetime(2026, 3, 1)
        )
        finalized.editable = False
        editable = make_collection(
            session_id, data_location="/data/editable", start_date=datetime(2026, 3, 1)
        )
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        by_location = {r["Dataset Location"]: r["Finalized*"] for r in rows}
        assert by_location["/data/finalized"] == "Yes"
        assert by_location["/data/editable"] == "No"


def test_csv_fields_includes_finalized_column(script):
    assert "Finalized*" in script.CSV_FIELDS
