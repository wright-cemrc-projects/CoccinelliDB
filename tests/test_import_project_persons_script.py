"""Tests for scripts/import_project_persons.py.

scripts/ isn't an importable package (matching the other tools in that
directory), so the module is loaded by path.
"""
import csv
import importlib.util
import sys
from pathlib import Path

import pytest

from app import db
from app.models import Facility, Person, Project

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "import_project_persons.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("import_project_persons", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def script():
    return _load_script_module()


@pytest.fixture()
def facility(app):
    with app.app_context():
        f = Facility(name="MCCET")
        db.session.add(f)
        db.session.commit()
        yield f.id


def write_csv(path: Path, rows: list[dict]) -> str:
    fieldnames = sorted({key for row in rows for key in row})
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return str(path)


def test_dry_run_writes_nothing(app, script, facility, tmp_path):
    csv_path = write_csv(
        tmp_path / "people.csv",
        [{"project_id": "P-100", "first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu"}],
    )
    with app.app_context():
        counts, errors = script.run_import(csv_path, "MCCET", verbose=False)
        assert counts["rows_ok"] == 1
        assert not errors
        db.session.rollback()

        assert db.session.execute(db.select(db.func.count(Project.id))).scalar() == 0
        assert db.session.execute(db.select(db.func.count(Person.id))).scalar() == 0


def test_a_bad_row_leaves_no_partial_project_or_person_behind(app, script, facility, tmp_path):
    """Regression test: a row that fails on its person shouldn't still create its project.

    process_row front-loads every check that can raise ValueError before doing
    any write specifically so this can't happen — see the comment on
    process_row for why (this project's SQLite setup can't rely on SAVEPOINTs
    to unwind a partially-written row).
    """
    csv_path = write_csv(
        tmp_path / "people.csv",
        [
            {"project_id": "P-100", "first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu"},
            {"project_id": "BADROW", "first_name": "Al", "last_name": "No", "email": "not-an-email"},
        ],
    )
    with app.app_context():
        counts, errors = script.run_import(csv_path, "MCCET", verbose=False)
        assert counts["rows_ok"] == 1
        assert len(errors) == 1
        assert "not a valid email" in errors[0][1]
        db.session.commit()

        project_ids = {p.project_id for p in db.session.execute(db.select(Project)).scalars()}
        assert project_ids == {"P-100"}


def test_rerun_over_the_same_rows_is_idempotent(app, script, facility, tmp_path):
    rows = [
        {"project_id": "P-100", "first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu", "net_id": "908"},
        {"project_id": "P-100", "first_name": "Jamie", "last_name": "Lee", "email": "jlee@wisc.edu", "net_id": "909"},
    ]
    csv_path = write_csv(tmp_path / "people.csv", rows)

    with app.app_context():
        counts, errors = script.run_import(csv_path, "MCCET", verbose=False)
        assert not errors
        db.session.commit()
        assert counts["projects_created"] == 1
        assert counts["persons_created"] == 2
        assert counts["links_created"] == 2

    with app.app_context():
        counts, errors = script.run_import(csv_path, "MCCET", verbose=False)
        assert not errors
        db.session.commit()
        assert counts["rows_ok"] == 2
        assert counts["projects_created"] == 0
        assert counts["persons_created"] == 0
        assert counts["links_created"] == 0

        assert db.session.execute(db.select(db.func.count(Project.id))).scalar() == 1
        assert db.session.execute(db.select(db.func.count(Person.id))).scalar() == 2


def test_missing_facility_column_without_default_is_an_error(app, script, tmp_path):
    csv_path = write_csv(
        tmp_path / "people.csv",
        [{"project_id": "P-100", "first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu"}],
    )
    with app.app_context():
        counts, errors = script.run_import(csv_path, None, verbose=False)
        assert counts["rows_ok"] == 0
        assert len(errors) == 1
        assert "no facility" in errors[0][1]


def test_unknown_facility_name_is_an_error(app, script, tmp_path):
    csv_path = write_csv(
        tmp_path / "people.csv",
        [{"project_id": "P-100", "first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu"}],
    )
    with app.app_context():
        with pytest.raises(ValueError, match="No facility named"):
            script.run_import(csv_path, "NoSuchFacility", verbose=False)


def test_missing_required_column_in_the_csv_itself_aborts_immediately(app, script, tmp_path):
    csv_path = write_csv(tmp_path / "people.csv", [{"project_id": "P-100", "email": "x@example.com"}])
    with app.app_context():
        with pytest.raises(SystemExit, match="missing required column"):
            script.run_import(csv_path, "MCCET", verbose=False)
