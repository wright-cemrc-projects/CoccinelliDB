"""Find-or-create helpers for bulk-importing persons onto projects.

Shared by the /api/projects/find_or_create + /api/persons/find_or_create routes
(for one-off use from the client or a shell) and scripts/import_project_persons.py
(for bulk CSV import). Keeping the matching rules in one place means the API and
the script can't drift apart on what counts as "the same" project or person.

None of these functions commit; the caller controls the transaction so a bulk
import can be done as one commit (or rolled back as one unit on error).
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_

from app import db
from app.models import Facility, Person, Project, project_person_link


@dataclass
class FindOrCreateResult:
    """Wraps a Project/Person lookup with whether it was newly created."""
    record: object
    created: bool


def find_or_create_project(project_id: str, facility_id: int) -> FindOrCreateResult:
    """Get the Project with this project_id, or create it under the given facility.

    project_id is globally unique, so an existing project is matched on that
    alone; facility_id is only used when creating a new one. Raises ValueError
    if project_id is blank or facility_id doesn't reference a real facility.
    """
    project_id = (project_id or "").strip()
    if not project_id:
        raise ValueError("project_id is required.")

    existing = db.session.execute(
        db.select(Project).filter_by(project_id=project_id)
    ).scalar_one_or_none()
    if existing:
        return FindOrCreateResult(existing, created=False)

    if not db.session.get(Facility, facility_id):
        raise ValueError(f"No facility with id {facility_id}.")

    project = Project(project_id)
    project.facility_id = facility_id
    db.session.add(project)
    db.session.flush()
    return FindOrCreateResult(project, created=True)


def find_or_create_person(
    first_name: str,
    last_name: str,
    email: str,
    net_id: str | None = None,
    **extra_fields,
) -> FindOrCreateResult:
    """Get the Person matching this email or net_id, or create a new one.

    Matching by either field (not requiring both) means a person re-imported
    with a newly-issued net_id, or one entered once with just an email, is
    still recognized as the same person. email is always required since it's
    the fallback identity for people with no net_id (e.g. outside collaborators);
    net_id is optional for the same reason. Raises ValueError if email is blank
    or a match can't be created without net_id/email uniqueness being violated.
    """
    email = (email or "").strip()
    if not email:
        raise ValueError("email is required to match or create a person.")
    net_id = (net_id or "").strip() or None

    conditions = [Person.email == email]
    if net_id:
        conditions.append(Person.net_id == net_id)
    existing = db.session.execute(
        db.select(Person).filter(or_(*conditions))
    ).scalars().first()
    if existing:
        return FindOrCreateResult(existing, created=False)

    if not (first_name and last_name):
        raise ValueError("first_name and last_name are required to create a new person.")

    person = Person(first_name=first_name, last_name=last_name, email=email, net_id=net_id)
    for field, value in extra_fields.items():
        if value is not None and hasattr(person, field):
            setattr(person, field, value)
    db.session.add(person)
    db.session.flush()
    return FindOrCreateResult(person, created=True)


def link_person_to_project(project: Project, person: Person, role: str | None = None) -> bool:
    """Link a person to a project, upserting the role. Returns True if newly linked.

    project_person has no ORM class of its own (it's a plain association table),
    so the link is read and written through it directly rather than via the
    `Project.persons` relationship, which would need a full Person object
    already attached to the session either way.
    """
    existing = db.session.execute(
        db.select(project_person_link).filter_by(project_id=project.id, person_id=person.id)
    ).first()
    if existing:
        db.session.execute(
            project_person_link.update()
            .where(project_person_link.c.project_id == project.id)
            .where(project_person_link.c.person_id == person.id)
            .values(role=role)
        )
        return False

    db.session.execute(
        project_person_link.insert().values(project_id=project.id, person_id=person.id, role=role)
    )
    return True
