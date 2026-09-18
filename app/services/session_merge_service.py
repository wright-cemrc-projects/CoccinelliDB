"""Merge two or more InstrumentSessions that turned out to be accidental
duplicates — same instrument, overlapping or same-day, created separately by
mistake — into one.

One session (`primary_id`) survives and absorbs the others: its time range
widens to cover all of them, their notes are concatenated onto its own
(labeled by source session), their participant lists are unioned (summing
hours for anyone listed on more than one), and all of their Collections move
onto it. The other sessions are then deleted.

`plan_merge` computes all of this without writing anything, so the API can
show a preview before the user commits. `merge_sessions` computes the same
plan and applies it. Neither commits; the caller controls the transaction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from app import db
from app.models import InstrumentSession, session_person_link


@dataclass
class MergedPerson:
    person_id: int
    onsite: bool
    role: str
    hours: float
    remote_access_level: str


@dataclass
class MergePlan:
    primary_id: int
    other_ids: list[int]
    start_date: object
    end_date: object
    notes: str | None
    persons: list[MergedPerson]
    collection_ids_to_move: list[int]
    warnings: list[str] = field(default_factory=list)


def _load_sessions(primary_id: int, other_ids: list[int]) -> tuple[InstrumentSession, list[InstrumentSession]]:
    all_ids = [primary_id, *other_ids]
    if not other_ids:
        raise ValueError("Select at least one other session to merge in.")
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("A session can't be merged with itself, and each session may only be listed once.")

    sessions_by_id = {
        s.id: s for s in db.session.execute(
            db.select(InstrumentSession).filter(InstrumentSession.id.in_(all_ids))
        ).scalars()
    }
    missing = set(all_ids) - set(sessions_by_id)
    if missing:
        raise ValueError(f"Session(s) not found: {', '.join(str(i) for i in sorted(missing))}.")

    return sessions_by_id[primary_id], [sessions_by_id[i] for i in other_ids]


def _check_mergeable(primary: InstrumentSession, others: list[InstrumentSession]) -> None:
    if primary.start_date is None or primary.end_date is None:
        raise ValueError(f"Session {primary.id} is missing a start or end date.")

    for other in others:
        if other.instrument_id != primary.instrument_id:
            raise ValueError(
                f"Session {other.id} is on a different instrument than session {primary.id}; "
                "only sessions on the same instrument can be merged."
            )
        if other.facility_id != primary.facility_id:
            raise ValueError(f"Session {other.id} is at a different facility than session {primary.id}.")
        if other.start_date is None or other.end_date is None:
            raise ValueError(f"Session {other.id} is missing a start or end date.")

        locked = [c for c in other.collections if not c.editable]
        if locked:
            locked_ids = ", ".join(str(c.id) for c in locked)
            raise ValueError(
                f"Session {other.id} has finalized collection(s) (id {locked_ids}) that must "
                "be unlocked before this session can be merged away."
            )


def _merge_notes(primary: InstrumentSession, others: list[InstrumentSession]) -> str | None:
    parts = []
    for session in [primary, *others]:
        if session.notes and session.notes.strip():
            label = f"Session {session.id}"
            if session.start_date and session.end_date:
                label += f" ({session.start_date:%Y-%m-%d %H:%M}–{session.end_date:%H:%M})"
            parts.append(f"--- {label} ---\n{session.notes.strip()}")
    return "\n\n".join(parts) if parts else None


def _merge_persons(primary: InstrumentSession, others: list[InstrumentSession]) -> list[MergedPerson]:
    """Union the participant lists; sum hours for anyone listed on more than one.

    Non-hours fields (onsite/role/remote_access_level) come from whichever
    session lists the person first — primary is checked before the others, in
    the order `others` was given.
    """
    merged: dict[int, MergedPerson] = {}
    for session in [primary, *others]:
        rows = db.session.execute(
            db.select(session_person_link).filter_by(session_id=session.id)
        ).fetchall()
        for row in rows:
            existing = merged.get(row.person_id)
            if existing:
                existing.hours += row.hours or 0
            else:
                merged[row.person_id] = MergedPerson(
                    person_id=row.person_id,
                    onsite=row.onsite,
                    role=row.role,
                    hours=row.hours or 0,
                    remote_access_level=row.remote_access_level,
                )
    return list(merged.values())


def _compute_plan(primary: InstrumentSession, others: list[InstrumentSession]) -> MergePlan:
    all_sessions = [primary, *others]
    warnings = []

    distinct_projects = {s.project_id for s in all_sessions}
    if len(distinct_projects) > 1:
        warnings.append(
            f"These sessions have different projects; the merged session keeps "
            f"session {primary.id}'s project."
        )

    return MergePlan(
        primary_id=primary.id,
        other_ids=[o.id for o in others],
        start_date=min(s.start_date for s in all_sessions),
        end_date=max(s.end_date for s in all_sessions),
        notes=_merge_notes(primary, others),
        persons=_merge_persons(primary, others),
        collection_ids_to_move=[c.id for other in others for c in other.collections],
        warnings=warnings,
    )


def plan_merge(primary_id: int, other_ids: list[int]) -> MergePlan:
    """Compute what merging `other_ids` into `primary_id` would produce. Read-only."""
    primary, others = _load_sessions(primary_id, other_ids)
    _check_mergeable(primary, others)
    return _compute_plan(primary, others)


def merge_sessions(primary_id: int, other_ids: list[int]) -> MergePlan:
    """Merge `other_ids` into `primary_id` and delete the other sessions.

    Returns the MergePlan that was applied. Does not commit; the caller
    controls the transaction.
    """
    primary, others = _load_sessions(primary_id, other_ids)
    _check_mergeable(primary, others)
    plan = _compute_plan(primary, others)

    primary.start_date = plan.start_date
    primary.end_date = plan.end_date
    primary.notes = plan.notes

    db.session.execute(
        session_person_link.delete().where(session_person_link.c.session_id == primary.id)
    )
    for person in plan.persons:
        db.session.execute(session_person_link.insert().values(
            session_id=primary.id,
            person_id=person.person_id,
            onsite=person.onsite,
            role=person.role,
            hours=person.hours,
            remote_access_level=person.remote_access_level,
        ))

    # Force both sides of the relationship to load before mutating either.
    # Without this, `primary.collections.append(...)` below lazy-loads
    # `primary.collections` for the first time mid-move, and that lazy load
    # triggers an autoflush — catching a collection in the momentary
    # NULL-FK state left by `other.collections.remove(...)` on the line just
    # before, and failing the NOT NULL constraint.
    list(primary.collections)
    for other in others:
        list(other.collections)

    for other in others:
        # Move via the relationship on both sides, not just the FK column:
        # setting collection.instrument_session_id directly leaves `other`'s
        # in-memory `.collections` still listing it as a member, and deleting
        # `other` afterwards would then have SQLAlchemy null out that FK
        # itself (orphaning it) — racing with the reassignment and violating
        # the NOT NULL constraint. Removing/appending through the relationship
        # keeps both sides' in-memory state consistent with what's intended.
        for collection in list(other.collections):
            other.collections.remove(collection)
            primary.collections.append(collection)
        db.session.delete(other)

    db.session.flush()
    return plan


def find_merge_candidates(session: InstrumentSession) -> list[InstrumentSession]:
    """Other sessions on the same instrument that look like they might be
    duplicates of `session`: overlapping time ranges, or falling on the same
    calendar date as its start. A suggestion list, not a hard filter — the
    human doing the merge makes the final call, including for a candidate
    this reports as blocked (e.g. by a finalized collection)."""
    if session.start_date is None:
        return []

    day_start = session.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    # Same calendar date as this session's start...
    same_day = db.and_(
        InstrumentSession.start_date >= day_start,
        InstrumentSession.start_date < day_end,
    )
    match_clauses = [same_day]
    if session.end_date is not None:
        # ...or an overlapping time range, regardless of date.
        match_clauses.append(db.and_(
            InstrumentSession.start_date < session.end_date,
            InstrumentSession.end_date > session.start_date,
        ))

    query = (
        db.select(InstrumentSession)
        .filter(InstrumentSession.id != session.id)
        .filter(InstrumentSession.instrument_id == session.instrument_id)
        .filter(db.or_(*match_clauses))
        .order_by(InstrumentSession.start_date)
    )
    return list(db.session.execute(query).scalars())
