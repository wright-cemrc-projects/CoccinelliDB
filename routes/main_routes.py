from flask import Blueprint, jsonify, request, redirect
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Project, Person, Instrument, InstrumentSession, InstrumentIssue, session_person_link, RemoteSessionLog, Collection, SessionGroup, project_person_link
from app.schema import projectSchema, projectsSchema,  \
    instrumentSessionSchema, \
    instrumentSessionsSchema, instrumentSchema, instrumentsSchema, instrumentIssueSchema, instrumentIssuesSchema, \
    remoteSessionLogsSchema, collectionSchema, collectionsSchema, sessionGroupSchema, sessionGroupsSchema
from app.services.project_import_service import find_or_create_project, link_person_to_project
from datetime import datetime, time, timedelta
from flask_security import roles_accepted

import sys

main = Blueprint('main', __name__)

@main.route('/')
def index():
    print(current_user)
    return redirect("http://localhost:5173/")

@main.route('/api/home', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello World"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/projects', methods=['GET'])
def get_project_list():
    search_query = request.args.get("project_id_like", "")

    project_list = []
    if search_query:
        project_list = Project.query.filter(Project.project_id.ilike(f"%{search_query}%")).all()
    else:
        project_list = Project.query.all()

    return projectsSchema.jsonify(project_list)

@roles_accepted('Admin', 'Editor')
@main.route('/api/projects/<int:id>', methods=['GET'])
def get_project_by_id(id):
    project_one = db.session.execute(db.select(Project).filter_by(id=id)).scalar_one()
    return projectSchema.jsonify(project_one)

def _existing_project_id_conflict(project_id, exclude_id=None):
    """The id of another Project already using this project_id, if any."""
    query = db.select(Project.id).filter_by(project_id=project_id)
    if exclude_id is not None:
        query = query.filter(Project.id != exclude_id)
    return db.session.execute(query).scalar_one_or_none()

@roles_accepted('Admin', 'Editor')
@main.route('/api/projects', methods=['POST'])
def create_project():
    project_id = request.json["project_id"]
    facility_id = request.json["facility_id"]
    try:
        conflict_id = _existing_project_id_conflict(project_id)
        if conflict_id is not None:
            return jsonify({
                "error": f"Project ID '{project_id}' is already in use.",
                "existing_id": conflict_id,
            }), 409

        project = Project(project_id)
        project.facility_id = facility_id
        db.session.add(project)
        db.session.commit()
        return jsonify({"message": "new project created.", "id": project.id})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": f"Project ID '{project_id}' is already in use."}), 409
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

@roles_accepted('Admin', 'Editor')
@main.route('/api/projects/find_or_create', methods=['POST'])
def find_or_create_project_route():
    """Get-or-create a project by project_id, for idempotent bulk import.

    Unlike POST /api/projects, a project_id that already exists is not an
    error here — the existing project is returned so re-running an import
    over the same rows doesn't create duplicates.
    """
    try:
        result = find_or_create_project(
            project_id=request.json.get("project_id"),
            facility_id=request.json.get("facility_id"),
        )
        verb = "created" if result.created else "matched existing"
        return jsonify({
            "id": result.record.id,
            "created": result.created,
            "message": f"{verb} project '{result.record.project_id}'.",
        })
    except ValueError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

@roles_accepted('Admin', 'Editor')
@main.route('/api/projects/<int:id>', methods=['PATCH'])
def update_project(id):
    try:
        project_id = request.json["project_id"]
        facility_id = request.json["facility_id"]

        conflict_id = _existing_project_id_conflict(project_id, exclude_id=id)
        if conflict_id is not None:
            return jsonify({
                "error": f"Project ID '{project_id}' is already in use.",
                "existing_id": conflict_id,
            }), 409

        project = db.session.execute(db.select(Project).filter_by(id=id)).scalar_one()
        project.project_id = project_id
        project.facility_id = facility_id
        db.session.commit()
        return jsonify({"message": f"{project} got updated"})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": f"Project ID '{project_id}' is already in use."}), 409
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

@roles_accepted('Admin', 'Editor')
@main.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    try:
        project = db.session.execute(db.select(Project).filter_by(id=id)).scalar_one()
        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": f"{project} got deleted."})
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

@roles_accepted('Admin', 'Editor')
@main.route('/api/projects/<int:id>/persons', methods=['POST'])
def link_project_person(id):
    """Link a person to a project (or update their role if already linked)."""
    try:
        project = db.session.execute(db.select(Project).filter_by(id=id)).scalar_one()
        person_id = request.json.get("person_id")
        if person_id is None:
            return jsonify({"error": "person_id is required."}), 400
        person = db.session.execute(db.select(Person).filter_by(id=person_id)).scalar_one()

        newly_linked = link_person_to_project(project, person, request.json.get("role"))
        db.session.commit()
        verb = "Linked" if newly_linked else "Updated role for"
        return jsonify({"message": f"{verb} {person} on project '{project.project_id}'."})
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

@roles_accepted('Admin', 'Editor')
@main.route('/api/projects/<int:id>/persons/<int:person_id>', methods=['DELETE'])
def unlink_project_person(id, person_id):
    try:
        db.session.execute(
            project_person_link.delete()
            .where(project_person_link.c.project_id == id)
            .where(project_person_link.c.person_id == person_id)
        )
        db.session.commit()
        return jsonify({"message": f"Unlinked person {person_id} from project {id}."})
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400


@roles_accepted('Admin', 'Editor')
@main.route('/api/instruments', methods=['POST'])
def create_instrument():
    try:
        instrument = Instrument()
        if "name" in request.json:
            instrument.name = request.json["name"]
        if "model" in request.json:
            instrument.model = request.json["model"]
        if "facility_id" in request.json:
            instrument.facility_id = request.json["facility_id"]
        db.session.add(instrument)
        db.session.commit()
        return jsonify({"message": f"{instrument} created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instruments/<int:id>', methods=['GET'])
def get_instrument_by_id(id):
    try:
        session = db.get_or_404(Instrument, id)
        return instrumentSchema.jsonify(session)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instruments', methods=['GET'])
def get_instrument_list():
    try:
        search_query = request.args.get("name_like", "")
        instruments_list = []
        if search_query:
            instruments_list = Instrument.query.filter(Instrument.name.ilike(f"%{search_query}%")).all()
        else:
            instruments_list = Instrument.query.all()
        return instrumentsSchema.jsonify(instruments_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instruments/<int:id>', methods=['PATCH'])
def update_instrument(id):
    try:
        instrument = db.session.execute(db.select(Instrument).filter_by(id=id)).scalar_one()
        if "name" in request.json:
            instrument.name = request.json["name"]
        if "model" in request.json:
            instrument.model = request.json["model"]
        if "facility_id" in request.json:
            instrument.facility_id = request.json["facility_id"]

        db.session.commit()
        return jsonify({"message": f"{instrument} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instruments/<int:id>', methods=['DELETE'])
def delete_instrument(id):
    try:
        instrument = db.session.execute(db.select(Instrument).filter_by(id=id)).scalar_one()
        db.session.delete(instrument)
        db.session.commit()
        return jsonify({"message": f"{instrument} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

def _normalize_person_entry(person_data):
    """Validate and coerce one 'persons' entry from the instrument session form.

    Blank fields (e.g. an Hours input the user cleared) arrive as "" rather
    than being omitted, so a plain dict.get(key, default) doesn't catch them
    and the DB driver ends up raising on the bad type instead. Coerce those
    cases here so failures produce a clear message rather than a raw
    SQLAlchemy/db-driver error.
    """
    person_id = person_data.get("person_id")
    if not person_id:
        raise ValueError("Each session participant must have a person selected.")

    hours = person_data.get("hours", 0)
    if hours in (None, ""):
        hours = 0
    try:
        hours = float(hours)
    except (TypeError, ValueError):
        raise ValueError(f"Hours must be a number, got {hours!r}.")

    return {
        "person_id": int(person_id),
        "onsite": bool(person_data.get("onsite", False)),
        "role": person_data.get("role") or "",
        "hours": hours,
        "remote_access_level": person_data.get("remote_access_level") or "",
    }

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentsession', methods=['POST'])
def create_session():
    try:
        print(request.json, file=sys.stderr)
        start_date = None
        if "start_date" in request.json:
            start_date = datetime.fromisoformat(request.json["start_date"])
        end_date = None
        if "end_date" in request.json:
            end_date = datetime.fromisoformat(request.json["end_date"])
        instrument_id = int(request.json["instrument_id"])
        project_id = None
        if request.json.get("project_id") is not None:
            project_id = int(request.json["project_id"])
        facility_id = int(request.json["facility_id"])
        notes = request.json.get("notes") or None
        session_group_id = None
        if request.json.get("session_group_id") is not None:
            session_group_id = int(request.json["session_group_id"])
        instrument_session = InstrumentSession(start_date=start_date, end_date=end_date, project_id=project_id, facility_id=facility_id, instrument_id=instrument_id, notes=notes, session_group_id=session_group_id)
        db.session.add(instrument_session)

        try:
            db.session.flush()
        except Exception as e:
            db.session.rollback()  # Rollback to avoid session corruption
            print(f"Flush failed: {e}", file=sys.stderr)
            return jsonify({"error": f"Flush failed: {str(e)}"}), 400
        if "persons" in request.json and request.json["persons"]:
            new_persons = request.json["persons"]  # List of dicts with person_id, onsite, role, hours, remote_access_level
            # Process new persons list
            for person_data in new_persons:
                entry = _normalize_person_entry(person_data)
                db.session.execute(
                    session_person_link.insert().values(
                        session_id=instrument_session.id,
                        **entry
                    )
                )

        db.session.commit()
        return jsonify({"message": f"new instrument session {start_date} created."})
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentsession/<int:id>', methods=['GET'])
def get_session_by_id(id):
    try:
        session = db.get_or_404(InstrumentSession, id)
        return instrumentSessionSchema.jsonify(session)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentsession', methods=['GET'])
def get_session_list():
    try:
        session_list = db.session.execute(db.select(InstrumentSession)).scalars()
        return instrumentSessionsSchema.jsonify(session_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentsession/<int:id>', methods=['PATCH'])
def update_session(id):
    try:
        session = db.session.execute(db.select(InstrumentSession).filter_by(id=id)).scalar_one()
        if "start_date" in request.json:
            session.start_date = datetime.fromisoformat(request.json["start_date"])
        if "end_date" in request.json:
            session.end_date = datetime.fromisoformat(request.json["end_date"])
        if request.json.get("instrument_id") is not None:
            session.instrument_id = request.json["instrument_id"]
        if "project_id" in request.json:
            session.project_id = int(request.json["project_id"]) if request.json["project_id"] is not None else None
        if "notes" in request.json:
            session.notes = request.json["notes"] or None
        if "session_group_id" in request.json:
            group_id = request.json["session_group_id"]
            session.session_group_id = int(group_id) if group_id is not None else None

        # Update persons in the session
        if "persons" in request.json:
            new_persons = request.json["persons"]  # List of dicts with person_id, onsite, role, remote_access_level

            # Get current person IDs linked to the session
            current_person_ids = {
                person_id for person_id, in db.session.query(session_person_link.c.person_id)
                .filter_by(session_id=id)
                .all()
            }

            # Process new persons list
            for person_data in new_persons:
                entry = _normalize_person_entry(person_data)
                person_id = entry["person_id"]

                print(f"Adding person: {entry}", file=sys.stderr)

                if person_id in current_person_ids:
                    # Update existing record
                    db.session.execute(
                        session_person_link.update()
                        .where(session_person_link.c.session_id == id)
                        .where(session_person_link.c.person_id == person_id)
                        .values(onsite=entry["onsite"], role=entry["role"], hours=entry["hours"], remote_access_level=entry["remote_access_level"])
                    )
                    current_person_ids.remove(person_id)  # Mark as processed
                else:
                    # Insert new record
                    db.session.execute(
                        session_person_link.insert().values(
                            session_id=id,
                            **entry
                        )
                    )

            # Remove persons that were not in the updated list
            if current_person_ids:
                db.session.execute(
                    session_person_link.delete()
                    .where(session_person_link.c.session_id == id)
                    .where(session_person_link.c.person_id.in_(current_person_ids))
                )

        print(f"Updating InstrumentSession: {session}", file=sys.stderr)
        db.session.commit()
        return jsonify({"message": f"{session} got updated"})
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

def _session_person_rows(session_id):
    """Read the session_person_link rows for a session as plain dicts."""
    return [
        {
            "person_id": link.person_id,
            "onsite": link.onsite,
            "role": link.role,
            "hours": link.hours,
            "remote_access_level": link.remote_access_level,
        }
        for link in db.session.execute(
            db.select(session_person_link).filter_by(session_id=session_id)
        ).fetchall()
    ]

def _group_for_split(session, name=None):
    """Get the SessionGroup the pieces of a split should land in.

    A session that is already grouped keeps its group, so splitting a session
    twice doesn't scatter the block across two groups.
    """
    if session.session_group_id is not None:
        return session.session_group

    if not name:
        name = f"Session {session.id}"
        if session.start_date and session.end_date:
            name += f" ({session.start_date:%Y-%m-%d} to {session.end_date:%Y-%m-%d})"

    group = SessionGroup(name=name, created_date=datetime.now())
    db.session.add(group)
    db.session.flush()
    session.session_group_id = group.id
    return group

def _copy_session(session, start_date, end_date, group_id, person_rows, keep_hours=False):
    """Create a sibling session over a new time range, in the same group.

    Participants are copied over, but their recorded `hours` stay behind on the
    original session unless `keep_hours`: there's no way to know how the hours
    actually fell across the pieces, so they're left for a human to fill in.
    """
    new_session = InstrumentSession(
        start_date=start_date,
        end_date=end_date,
        project_id=session.project_id,
        facility_id=session.facility_id,
        instrument_id=session.instrument_id,
        session_group_id=group_id,
    )
    db.session.add(new_session)
    db.session.flush()

    for row in person_rows:
        values = dict(row, hours=row["hours"] if keep_hours else 0)
        db.session.execute(session_person_link.insert().values(session_id=new_session.id, **values))

    return new_session

def day_boundaries(start_date, end_date, day_start_time):
    """List every `day_start_time` clock time strictly between start_date and end_date.

    Boundaries are rebuilt from each calendar date rather than by adding 24 hours,
    so the cut lands on the requested wall-clock time on every day.
    """
    boundaries = []
    candidate = datetime.combine(start_date.date(), day_start_time)
    if candidate <= start_date:
        candidate = datetime.combine(start_date.date() + timedelta(days=1), day_start_time)
    while candidate < end_date:
        boundaries.append(candidate)
        candidate = datetime.combine(candidate.date() + timedelta(days=1), day_start_time)
    return boundaries

def split_session_by_day(session, day_start_time, group_name=None):
    """Split a multi-day session into one session per day, cut at `day_start_time`.

    The pieces are contiguous — each one ends exactly where the next begins — so
    the block still covers the original range with no gaps or overlap, and the
    total hours are preserved. A session running Mon 14:00 -> Wed 16:00 cut at
    09:00 becomes Mon 14:00 -> Tue 09:00, Tue 09:00 -> Wed 09:00, and
    Wed 09:00 -> Wed 16:00.

    The original session row is kept and repurposed as the first piece so its id
    stays valid; a new row is created for each later piece, copying
    facility/project/instrument and the participant list. Collections move onto
    whichever piece covers their start_date; collections with no start_date stay
    on the original session. Every piece lands in a shared SessionGroup so the
    block is still visible as one unit afterwards.

    Returns (group, [session ids, original first]). Raises ValueError if the
    session doesn't cross a boundary. Does not commit; the caller controls the
    transaction.
    """
    if session.start_date is None or session.end_date is None:
        raise ValueError("Session needs both a start and end date to split by day.")

    boundaries = day_boundaries(session.start_date, session.end_date, day_start_time)
    if not boundaries:
        raise ValueError(
            f"Session does not cross a {day_start_time:%H:%M} boundary, so there is nothing to split."
        )

    person_rows = _session_person_rows(session.id)
    group = _group_for_split(session, group_name)

    # Contiguous ranges: [start, b1], [b1, b2], ... [bN, end]
    edges = [session.start_date, *boundaries, session.end_date]
    ranges = list(zip(edges, edges[1:]))

    # Shrink the original to the first piece before the new rows claim later ranges.
    first_start, first_end = ranges[0]
    session.end_date = first_end
    pieces = [session]
    for start_date, end_date in ranges[1:]:
        pieces.append(_copy_session(session, start_date, end_date, group.id, person_rows))

    # Move each dated collection onto the piece covering its start. Ranges are
    # half-open except the last, which includes the session's end.
    for collection in list(session.collections):
        if collection.start_date is None:
            continue
        for piece in pieces:
            if piece.start_date <= collection.start_date < piece.end_date or (
                piece is pieces[-1] and collection.start_date == piece.end_date
            ):
                collection.instrument_session_id = piece.id
                break

    db.session.flush()
    return group, [piece.id for piece in pieces]

def split_session_by_collections(session, group_name=None):
    """Split a session with multiple, distinct Collections into one session per Collection.

    Each resulting session's start/end_date matches its Collection's time range;
    facility/project/instrument and the participant list are copied from the
    original session. The original session row is kept and repurposed for the
    earliest Collection so its id stays valid; a new session row is created for
    each remaining Collection. Collections with no start_date can't be assigned
    a time range and are left linked to the original session. Every piece lands
    in a shared SessionGroup so the block stays visible as one unit.

    Returns (group, [session ids, original first]). Raises ValueError if there
    aren't at least 2 dated collections to split across. Does not commit; the
    caller controls the transaction.
    """
    dated_collections = sorted(
        (c for c in session.collections if c.start_date is not None),
        key=lambda c: c.start_date,
    )
    if len(dated_collections) < 2:
        raise ValueError("Session needs at least 2 dated collections to split.")

    person_rows = _session_person_rows(session.id)
    group = _group_for_split(session, group_name)

    first, *rest = dated_collections
    session.start_date = first.start_date
    session.end_date = first.end_date
    new_session_ids = [session.id]

    for collection in rest:
        new_session = _copy_session(
            session, collection.start_date, collection.end_date, group.id, person_rows
        )
        collection.instrument_session_id = new_session.id
        new_session_ids.append(new_session.id)

    db.session.flush()
    return group, new_session_ids

def _parse_day_start_time(raw):
    """Parse an 'HH:MM' (or 'HH:MM:SS') day-boundary time from a request body."""
    if raw is None:
        return time(9, 0)
    if not isinstance(raw, str):
        raise ValueError("day_start_time must be a time string such as '09:00'.")
    try:
        return time.fromisoformat(raw)
    except ValueError:
        raise ValueError(f"Could not read '{raw}' as a time. Use a 24-hour time such as '09:00'.")

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentsession/<int:id>/split', methods=['POST'])
def split_session(id):
    """Split a session into pieces, either per calendar day or per collection.

    Body (all optional): `mode` ("day", the default, or "collections"),
    `day_start_time` (an 'HH:MM' clock time for day mode, default '09:00'), and
    `group_name` for the SessionGroup the pieces are linked into.
    """
    try:
        session = db.session.execute(db.select(InstrumentSession).filter_by(id=id)).scalar_one()
        body = request.json or {}
        mode = body.get("mode", "day")
        group_name = body.get("group_name") or None

        try:
            if mode == "day":
                group, new_session_ids = split_session_by_day(
                    session, _parse_day_start_time(body.get("day_start_time")), group_name
                )
            elif mode == "collections":
                group, new_session_ids = split_session_by_collections(session, group_name)
            else:
                raise ValueError(f"Unknown split mode '{mode}'. Use 'day' or 'collections'.")
        except ValueError as err:
            db.session.rollback()
            return jsonify({"error": str(err), "message": str(err)}), 400

        db.session.commit()
        return jsonify({
            "message": f"Split session {id} into {len(new_session_ids)} sessions.",
            "session_ids": new_session_ids,
            "session_group_id": group.id,
        })
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentsession/<int:id>/split/preview', methods=['POST'])
def preview_split_session(id):
    """Report the time ranges a day split would produce, without changing anything."""
    try:
        session = db.session.execute(db.select(InstrumentSession).filter_by(id=id)).scalar_one()
        body = request.json or {}
        day_start_time = _parse_day_start_time(body.get("day_start_time"))

        if session.start_date is None or session.end_date is None:
            raise ValueError("Session needs both a start and end date to split by day.")

        edges = [session.start_date, *day_boundaries(session.start_date, session.end_date, day_start_time), session.end_date]
        return jsonify({
            "ranges": [
                {"start_date": start.isoformat(), "end_date": end.isoformat()}
                for start, end in zip(edges, edges[1:])
            ]
        })
    except ValueError as err:
        return jsonify({"error": str(err), "message": str(err)}), 400
    except Exception as err:
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

@roles_accepted('Admin', 'Editor')
@main.route('/api/sessiongroups', methods=['GET'])
def get_session_group_list():
    try:
        search_query = request.args.get("name_like", "")
        if search_query:
            groups = SessionGroup.query.filter(SessionGroup.name.ilike(f"%{search_query}%")).all()
        else:
            groups = SessionGroup.query.all()
        return sessionGroupsSchema.jsonify(groups)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/sessiongroups/<int:id>', methods=['GET'])
def get_session_group_by_id(id):
    try:
        group = db.get_or_404(SessionGroup, id)
        return sessionGroupSchema.jsonify(group)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/sessiongroups', methods=['POST'])
def create_session_group():
    try:
        group = SessionGroup(
            name=request.json.get("name") or None,
            notes=request.json.get("notes") or None,
            created_date=datetime.now(),
        )
        db.session.add(group)
        db.session.flush()

        _set_session_group_members(group.id, request.json.get("session_ids"))

        db.session.commit()
        return jsonify({"message": f"new session group {group.name} created.", "id": group.id})
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

def _set_session_group_members(group_id, session_ids):
    """Make exactly `session_ids` the members of a group, unlinking any others.

    A None `session_ids` leaves the membership alone, so a PATCH that only edits
    the name or notes doesn't empty the group.
    """
    if session_ids is None:
        return
    wanted = {int(session_id) for session_id in session_ids}

    for session in db.session.execute(
        db.select(InstrumentSession).filter_by(session_group_id=group_id)
    ).scalars():
        if session.id not in wanted:
            session.session_group_id = None

    if wanted:
        for session in db.session.execute(
            db.select(InstrumentSession).filter(InstrumentSession.id.in_(wanted))
        ).scalars():
            session.session_group_id = group_id

@roles_accepted('Admin', 'Editor')
@main.route('/api/sessiongroups/<int:id>', methods=['PATCH'])
def update_session_group(id):
    try:
        group = db.session.execute(db.select(SessionGroup).filter_by(id=id)).scalar_one()
        if "name" in request.json:
            group.name = request.json["name"] or None
        if "notes" in request.json:
            group.notes = request.json["notes"] or None

        _set_session_group_members(group.id, request.json.get("session_ids"))

        db.session.commit()
        return jsonify({"message": f"{group} got updated"})
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

@roles_accepted('Admin', 'Editor')
@main.route('/api/sessiongroups/<int:id>', methods=['DELETE'])
def delete_session_group(id):
    """Delete a group. Its sessions are unlinked, never deleted along with it."""
    try:
        group = db.session.execute(db.select(SessionGroup).filter_by(id=id)).scalar_one()
        _set_session_group_members(group.id, [])
        db.session.delete(group)
        db.session.commit()
        return jsonify({"message": f"{group} got deleted."})
    except Exception as err:
        db.session.rollback()
        print(err, file=sys.stderr)
        return jsonify({"error": str(err), "message": str(err)}), 400

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentsession/<int:id>', methods=['DELETE'])
def delete_session(id):
    try:
        session = db.session.execute(db.select(InstrumentSession).filter_by(id=id)).scalar_one()
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": f"{session} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentissues', methods=['POST'])
def create_instrumentissue():
    try:
        instrument_id = request.json["instrument_id"]
        issue_title = ""
        issue_description = ""

        if "issue_title" in request.json:
            issue_title = request.json["issue_title"]
        if "issue_description" in request.json:
            issue_description = request.json["issue_description"]
        start_date = None
        if "start_date" in request.json:
            start_date = datetime.fromisoformat(request.json["start_date"])
        end_date = None
        if "end_date" in request.json:
            end_date = datetime.fromisoformat(request.json["end_date"])

        issue = InstrumentIssue(issue_title=issue_title,issue_description=issue_description,start_date=start_date, end_date=end_date, instrument_id=instrument_id)
        db.session.add(issue)
        db.session.commit()
        return jsonify({"message": f"new instrument session {start_date} created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentissues/<int:id>', methods=['GET'])
def get_instrumentissue_by_id(id):
    try:
        issue = db.get_or_404(InstrumentIssue, id)
        return instrumentIssueSchema.jsonify(issue)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentissues', methods=['GET'])
def get_instrumentissue_list():
    try:
        issue_list = db.session.execute(db.select(InstrumentIssue)).scalars()
        return instrumentIssuesSchema.jsonify(issue_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentissues/<int:id>', methods=['PATCH'])
def update_instrumentissue(id):
    try:
        issue = db.session.execute(db.select(InstrumentIssue).filter_by(id=id)).scalar_one()
        if "issue_title" in request.json:
            issue.issue_title = request.json["issue_title"]
        if "issue_description" in request.json:
            issue.issue_description = request.json["issue_description"]
        if "instrument_id" in request.json:
            issue.instrument_id = request.json["instrument_id"]
        if "start_date" in request.json:
            issue.start_date = datetime.fromisoformat(request.json["start_date"])
        if "end_date" in request.json:
            issue.end_date = datetime.fromisoformat(request.json["end_date"])
        db.session.commit()
        return jsonify({"message": f"{issue} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/instrumentissues/<int:id>', methods=['DELETE'])
def delete_instrumentissue(id):
    try:
        session = db.session.execute(db.select(InstrumentIssue).filter_by(id=id)).scalar_one()
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": f"{session} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})


@roles_accepted('Admin', 'Editor')
@main.route('/api/collection', methods=['GET'])
def get_collection_list():
    try:
        collection_list = db.session.execute(db.select(Collection)).scalars()
        return collectionsSchema.jsonify(collection_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/collection/<int:id>', methods=['GET'])
def get_collection_by_id(id):
    try:
        collection = db.get_or_404(Collection, id)
        return collectionSchema.jsonify(collection)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin', 'Editor')
@main.route('/api/collection/<int:id>', methods=['PATCH'])
def update_collection(id):
    try:
        collection = db.session.execute(db.select(Collection).filter_by(id=id)).scalar_one()
        if "instrument_session_id" in request.json:
            collection.instrument_session_id = request.json["instrument_session_id"]
        if "collection_type" in request.json:
            collection.collection_type = request.json["collection_type"]
        if "data_location" in request.json:
            collection.data_location = request.json["data_location"]
        if "thumbnail_location" in request.json:
            collection.thumbnail_location = request.json["thumbnail_location"]
        if "total_image_count" in request.json:
            collection.total_image_count = request.json["total_image_count"]
        if "start_date" in request.json:
            collection.start_date = datetime.fromisoformat(request.json["start_date"]) if request.json["start_date"] else None
        if "end_date" in request.json:
            collection.end_date = datetime.fromisoformat(request.json["end_date"]) if request.json["end_date"] else None
        db.session.commit()
        return jsonify({"message": f"Collection {id} got updated"})
    except Exception as err:
        db.session.rollback()
        return jsonify({"err": f"{err=}"}), 400

@roles_accepted('Admin')
@main.route('/api/remotelogs', methods=['GET'])
def get_remotelog_list():
    try:
        log_list = db.session.execute(db.select(RemoteSessionLog)).scalars()
        return remoteSessionLogsSchema.jsonify(log_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})


