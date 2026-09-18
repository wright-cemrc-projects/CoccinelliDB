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
def ids(app):
    with app.app_context():
        facility = Facility(name="MCCET")
        db.session.add(facility)
        db.session.flush()
        instrument = Instrument(name="Krios", facility_id=facility.id)
        db.session.add(instrument)
        db.session.commit()
        return {"facility_id": facility.id, "instrument_id": instrument.id}


def make_session(ids):
    session = InstrumentSession(facility_id=ids["facility_id"], instrument_id=ids["instrument_id"])
    db.session.add(session)
    db.session.flush()
    return session


def make_collection(session_id, **kwargs):
    collection = Collection(instrument_session_id=session_id, **kwargs)
    db.session.add(collection)
    db.session.flush()
    return collection


def row_by_location_substring(rows, substring):
    return next(r for r in rows if substring in r["Dataset Location"])


# --- Lamella Count -----------------------------------------------------


def test_lamella_count_is_pulled_from_the_collection(app, script, ids):
    with app.app_context():
        session = make_session(ids)
        make_collection(
            session.id, data_location="/data/with-lamella", start_date=datetime(2026, 3, 1), lamella_count=4
        )
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert len(rows) == 1
        assert rows[0]["Lamella Count (FIB-SEM only)"] == 4


def test_lamella_count_is_blank_not_none_when_unset(app, script, ids):
    with app.app_context():
        session = make_session(ids)
        make_collection(session.id, data_location="/data/no-lamella", start_date=datetime(2026, 3, 1))
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert rows[0]["Lamella Count (FIB-SEM only)"] == ""


# --- Finalized -----------------------------------------------------------


def test_finalized_reflects_editable_state_for_independent_sessions(app, script, ids):
    with app.app_context():
        finalized_session = make_session(ids)
        finalized = make_collection(
            finalized_session.id, data_location="/data/finalized", start_date=datetime(2026, 3, 1)
        )
        finalized.editable = False

        editable_session = make_session(ids)
        make_collection(editable_session.id, data_location="/data/editable", start_date=datetime(2026, 3, 1))
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert row_by_location_substring(rows, "/data/finalized")["Finalized"] == "Yes"
        assert row_by_location_substring(rows, "/data/editable")["Finalized"] == "No"


def test_csv_fields_includes_finalized_column(script):
    assert "Finalized" in script.CSV_FIELDS


# --- EM_Use_Category -------------------------------------------------------


@pytest.mark.parametrize("collection_type", ["SPA", "spa", "CryoET", "Cryo-ET", "cryo_et", "Tomography", "tomo"])
def test_em_use_category_is_data_collection_for_spa_and_cryoet(app, script, ids, collection_type):
    with app.app_context():
        session = make_session(ids)
        make_collection(
            session.id, data_location="/data/x", start_date=datetime(2026, 3, 1), collection_type=collection_type
        )
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert rows[0]["EM_Use_Category"] == "Data Collection"


@pytest.mark.parametrize("collection_type", ["Screening", None, "Setup"])
def test_em_use_category_is_blank_for_non_data_collection_types(app, script, ids, collection_type):
    with app.app_context():
        session = make_session(ids)
        make_collection(
            session.id, data_location="/data/x", start_date=datetime(2026, 3, 1), collection_type=collection_type
        )
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert rows[0]["EM_Use_Category"] == ""


# --- Combining collections on the same session ----------------------------


def test_collections_on_the_same_session_combine_into_one_row(app, script, ids):
    with app.app_context():
        session = make_session(ids)
        make_collection(
            session.id,
            data_location="/data/part-one",
            start_date=datetime(2026, 3, 1, 9, 0),
            end_date=datetime(2026, 3, 1, 11, 0),
            total_image_count=100,
            lamella_count=2,
        )
        make_collection(
            session.id,
            data_location="/data/part-two",
            start_date=datetime(2026, 3, 1, 12, 0),
            end_date=datetime(2026, 3, 1, 15, 0),
            total_image_count=50,
            lamella_count=3,
        )
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert len(rows) == 1
        row = rows[0]
        assert row["Start Date"] == "2026-03-01" and row["Start Time"] == "09:00"
        assert row["End Date"] == "2026-03-01" and row["End Time"] == "15:00"
        assert row["Image Count"] == 150
        assert row["Lamella Count (FIB-SEM only)"] == 5
        assert row["Dataset Location"] == "/data/part-one; /data/part-two"


def test_combined_row_counts_blank_when_all_parts_are_unset(app, script, ids):
    with app.app_context():
        session = make_session(ids)
        make_collection(session.id, data_location="/data/a", start_date=datetime(2026, 3, 1, 9, 0))
        make_collection(session.id, data_location="/data/b", start_date=datetime(2026, 3, 1, 10, 0))
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert rows[0]["Image Count"] == ""
        assert rows[0]["Lamella Count (FIB-SEM only)"] == ""


def test_combined_row_is_data_collection_if_any_part_matches(app, script, ids):
    with app.app_context():
        session = make_session(ids)
        make_collection(
            session.id, data_location="/data/screen", start_date=datetime(2026, 3, 1, 9, 0),
            collection_type="Screening",
        )
        make_collection(
            session.id, data_location="/data/spa", start_date=datetime(2026, 3, 1, 10, 0),
            collection_type="SPA",
        )
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert rows[0]["EM_Use_Category"] == "Data Collection"


def test_combined_row_is_not_finalized_if_only_some_parts_are(app, script, ids):
    with app.app_context():
        session = make_session(ids)
        locked = make_collection(session.id, data_location="/data/a", start_date=datetime(2026, 3, 1, 9, 0))
        locked.editable = False
        make_collection(session.id, data_location="/data/b", start_date=datetime(2026, 3, 1, 10, 0))
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert rows[0]["Finalized"] == "No"


def test_combined_row_is_finalized_if_every_part_is(app, script, ids):
    with app.app_context():
        session = make_session(ids)
        a = make_collection(session.id, data_location="/data/a", start_date=datetime(2026, 3, 1, 9, 0))
        b = make_collection(session.id, data_location="/data/b", start_date=datetime(2026, 3, 1, 10, 0))
        a.editable = False
        b.editable = False
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert rows[0]["Finalized"] == "Yes"


def test_collections_on_different_sessions_are_not_combined(app, script, ids):
    with app.app_context():
        first = make_session(ids)
        second = make_session(ids)
        make_collection(first.id, data_location="/data/first", start_date=datetime(2026, 3, 1, 9, 0))
        make_collection(second.id, data_location="/data/second", start_date=datetime(2026, 3, 1, 9, 30))
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert len(rows) == 2


# --- QC Check #1 default ---------------------------------------------------


def test_qc_check_1_defaults_to_ok(app, script, ids):
    with app.app_context():
        session = make_session(ids)
        make_collection(session.id, data_location="/data/x", start_date=datetime(2026, 3, 1))
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert rows[0]["EM Performance QC Check #1"] == "OK"
        # Left blank for manual entry, unlike QC Check #1.
        assert rows[0]["EM Outcome Category"] == ""
        assert rows[0]["EM Performance QC Check #2"] == ""


def test_no_column_headers_are_starred(script):
    assert not any(field.endswith("*") for field in script.CSV_FIELDS)


# --- Instrument Session ID ---------------------------------------------------


def test_instrument_session_id_column_is_the_source_session(app, script, ids):
    with app.app_context():
        first = make_session(ids)
        second = make_session(ids)
        make_collection(first.id, data_location="/data/first", start_date=datetime(2026, 3, 1, 9, 0))
        make_collection(second.id, data_location="/data/second", start_date=datetime(2026, 3, 1, 9, 30))
        db.session.commit()
        first_id, second_id = first.id, second.id

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert row_by_location_substring(rows, "/data/first")["Instrument Session ID"] == first_id
        assert row_by_location_substring(rows, "/data/second")["Instrument Session ID"] == second_id


def test_combined_row_reports_its_single_shared_session_id(app, script, ids):
    with app.app_context():
        session = make_session(ids)
        make_collection(session.id, data_location="/data/a", start_date=datetime(2026, 3, 1, 9, 0))
        make_collection(session.id, data_location="/data/b", start_date=datetime(2026, 3, 1, 10, 0))
        db.session.commit()

        rows = script.collect_rows(datetime(2026, 3, 1), datetime(2026, 3, 2))
        assert len(rows) == 1
        assert rows[0]["Instrument Session ID"] == session.id


def test_instrument_session_id_is_the_last_column(script):
    # Appended after the template columns so they keep their positions.
    assert script.CSV_FIELDS[-1] == "Instrument Session ID"
