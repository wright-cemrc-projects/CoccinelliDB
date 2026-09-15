"""Tests for scripts/finalize_collections.py.

scripts/ isn't an importable package (matching the other tools in that
directory), so the module is loaded by path.
"""
import csv
import importlib.util
from pathlib import Path

import pytest

from app import db
from app.models import Collection, Facility, Instrument, InstrumentSession

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "finalize_collections.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("finalize_collections", SCRIPT_PATH)
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


def make_collection(session_id, data_location, editable=True):
    collection = Collection(data_location=data_location, instrument_session_id=session_id)
    collection.editable = editable
    db.session.add(collection)
    db.session.flush()
    return collection


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> str:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    return str(path)


def test_dry_run_writes_nothing(app, script, session_id, tmp_path):
    with app.app_context():
        collection = make_collection(session_id, "/data/one")
        db.session.commit()
        cid = collection.id

    csv_path = write_csv(
        tmp_path / "reviewed.csv",
        ["id", "image_count", "lamella_count"],
        [[str(cid), "100", "2"]],
    )
    with app.app_context():
        counts, errors = script.run_import(csv_path, verbose=False)
        assert counts["finalized"] == 1
        assert not errors
        db.session.rollback()

        untouched = db.session.get(Collection, cid)
        assert untouched.editable is True
        assert untouched.total_image_count is None


def test_commit_applies_counts_and_locks(app, script, session_id, tmp_path):
    with app.app_context():
        collection = make_collection(session_id, "/data/one")
        db.session.commit()
        cid = collection.id

    csv_path = write_csv(
        tmp_path / "reviewed.csv",
        ["id", "image_count", "lamella_count"],
        [[str(cid), "100", "2"]],
    )
    with app.app_context():
        counts, errors = script.run_import(csv_path, verbose=False)
        assert not errors
        db.session.commit()

        updated = db.session.get(Collection, cid)
        assert updated.total_image_count == 100
        assert updated.lamella_count == 2
        assert updated.editable is False


def test_header_variants_are_recognized(app, script, session_id, tmp_path):
    with app.app_context():
        collection = make_collection(session_id, "/data/spaced-headers")
        db.session.commit()
        cid = collection.id

    csv_path = write_csv(
        tmp_path / "reviewed.csv",
        ["Collection ID", "Image Count", "Lamella Count"],
        [[str(cid), "55", "1"]],
    )
    with app.app_context():
        counts, errors = script.run_import(csv_path, verbose=False)
        assert counts["finalized"] == 1
        assert not errors
        db.session.commit()
        assert db.session.get(Collection, cid).lamella_count == 1


def test_data_location_identifier_works(app, script, session_id, tmp_path):
    with app.app_context():
        make_collection(session_id, "/data/by-path")
        db.session.commit()

    csv_path = write_csv(
        tmp_path / "reviewed.csv",
        ["data_location", "lamella_count"],
        [["/data/by-path", "9"]],
    )
    with app.app_context():
        counts, errors = script.run_import(csv_path, verbose=False)
        assert counts["finalized"] == 1
        db.session.commit()

        updated = db.session.execute(
            db.select(Collection).filter_by(data_location="/data/by-path")
        ).scalar_one()
        assert updated.lamella_count == 9


def test_already_finalized_row_is_reported_not_overwritten(app, script, session_id, tmp_path):
    with app.app_context():
        collection = make_collection(session_id, "/data/locked", editable=False)
        db.session.commit()
        cid = collection.id

    csv_path = write_csv(
        tmp_path / "reviewed.csv",
        ["id", "lamella_count"],
        [[str(cid), "99"]],
    )
    with app.app_context():
        counts, errors = script.run_import(csv_path, verbose=False)
        assert counts["finalized"] == 0
        assert counts["already_finalized"] == 1
        assert not errors
        db.session.commit()

        untouched = db.session.get(Collection, cid)
        assert untouched.lamella_count is None


def test_rerun_over_the_same_file_is_idempotent(app, script, session_id, tmp_path):
    with app.app_context():
        collection = make_collection(session_id, "/data/rerun")
        db.session.commit()
        cid = collection.id

    csv_path = write_csv(
        tmp_path / "reviewed.csv",
        ["id", "lamella_count"],
        [[str(cid), "3"]],
    )
    with app.app_context():
        counts, _ = script.run_import(csv_path, verbose=False)
        db.session.commit()
        assert counts["finalized"] == 1

    with app.app_context():
        counts, _ = script.run_import(csv_path, verbose=False)
        db.session.commit()
        assert counts["finalized"] == 0
        assert counts["already_finalized"] == 1
        assert db.session.get(Collection, cid).lamella_count == 3


def test_unknown_id_is_a_per_row_error_not_a_hard_stop(app, script, session_id, tmp_path):
    with app.app_context():
        collection = make_collection(session_id, "/data/good-row")
        db.session.commit()
        cid = collection.id

    csv_path = write_csv(
        tmp_path / "reviewed.csv",
        ["id", "lamella_count"],
        [["999999", "1"], [str(cid), "5"]],
    )
    with app.app_context():
        counts, errors = script.run_import(csv_path, verbose=False)
        assert counts["finalized"] == 1
        assert len(errors) == 1
        db.session.commit()
        assert db.session.get(Collection, cid).lamella_count == 5


def test_missing_identifier_column_aborts_immediately(app, script, tmp_path):
    csv_path = write_csv(tmp_path / "reviewed.csv", ["image_count", "lamella_count"], [["1", "2"]])
    with app.app_context():
        with pytest.raises(SystemExit, match="identifier column"):
            script.run_import(csv_path, verbose=False)
