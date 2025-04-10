from flask import Blueprint, jsonify, request, redirect
from app import db
from app.models import Project, Instrument, InstrumentSession, InstrumentIssue, session_person_link
from app.schema import projectSchema, projectsSchema,  \
    instrumentSessionSchema, \
    instrumentSessionsSchema, instrumentSchema, instrumentsSchema, instrumentIssueSchema, instrumentIssuesSchema
from datetime import datetime
from flask_security import roles_accepted

import sys

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect("http://localhost:5173/")

@main.route('/api/home', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello World"})

@main.route('/api/projects', methods=['GET'])
@roles_accepted('Admin')
def get_project_list():
    search_query = request.args.get("project_id_like", "")

    project_list = []
    if search_query:
        project_list = Project.query.filter(Project.project_id.ilike(f"%{search_query}%")).all()
    else:
        project_list = Project.query.all()

    return projectsSchema.jsonify(project_list)

@roles_accepted('Admin')
@main.route('/api/projects/<int:id>', methods=['GET'])
def get_project_by_id(id):
    project_one = db.session.execute(db.select(Project).filter_by(id=id)).scalar_one()
    return projectSchema.jsonify(project_one)

@roles_accepted('Admin')
@main.route('/api/projects', methods=['POST'])
def create_project():
    project_id = request.json["project_id"]
    facility_id = request.json["facility_id"]
    try:
        project = Project(project_id)
        project.facility_id = facility_id
        db.session.add(project)
        db.session.commit()
        return jsonify({"message": "new project created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@main.route('/api/projects/<int:id>', methods=['PATCH'])
def update_project(id):
    try:
        project_id = request.json["project_id"]
        facility_id = request.json["facility_id"]
        project = db.session.execute(db.select(Project).filter_by(id=id)).scalar_one()
        project.project_id = project_id
        project.facility_id = facility_id
        db.session.commit()
        return jsonify({"message": f"{project} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@main.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    try:
        project = db.session.execute(db.select(Project).filter_by(id=id)).scalar_one()
        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": f"{project} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})



@roles_accepted('Admin')
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

@roles_accepted('Admin')
@main.route('/api/instruments/<int:id>', methods=['GET'])
def get_instrument_by_id(id):
    try:
        session = db.get_or_404(Instrument, id)
        return instrumentSchema.jsonify(session)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
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

@roles_accepted('Admin')
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

@roles_accepted('Admin')
@main.route('/api/instruments/<int:id>', methods=['DELETE'])
def delete_instrument(id):
    try:
        instrument = db.session.execute(db.select(Instrument).filter_by(id=id)).scalar_one()
        db.session.delete(instrument)
        db.session.commit()
        return jsonify({"message": f"{instrument} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
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
        if "project_id" in request.json:
            project_id = int(request.json["project_id"])
        facility_id = int(request.json["facility_id"])
        instrument_session = InstrumentSession(start_date=start_date, end_date=end_date, project_id=project_id, facility_id=facility_id, instrument_id=instrument_id)
        db.session.add(instrument_session)

        try:
            db.session.flush()
        except Exception as e:
            db.session.rollback()  # Rollback to avoid session corruption
            print(f"Flush failed: {e}", file=sys.stderr)
            return jsonify({"error": f"Flush failed: {str(e)}"}), 400
        if "persons" in request.json and request.json["persons"]:
            new_persons = request.json["persons"]  # List of dicts with person_id, onsite, role, remote_access_level
            # Process new persons list
            for person_data in new_persons:
                person_id = person_data["person_id"]
                onsite = person_data.get("onsite", False)
                role = person_data.get("role", "")
                remote_access_level = person_data.get("remote_access_level", "")
                    # Insert new record
                db.session.execute(
                    session_person_link.insert().values(
                        session_id=instrument_session.id,
                        person_id=person_id,
                        onsite=onsite,
                        role=role,
                        remote_access_level=remote_access_level
                    )
                )
        
        db.session.commit()
        return jsonify({"message": f"new instrument session {start_date} created."})
    except Exception as err:
        print(err, file=sys.stderr)
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@main.route('/api/instrumentsession/<int:id>', methods=['GET'])
def get_session_by_id(id):
    try:
        session = db.get_or_404(InstrumentSession, id)
        return instrumentSessionSchema.jsonify(session)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@main.route('/api/instrumentsession', methods=['GET'])
def get_session_list():
    try:
        session_list = db.session.execute(db.select(InstrumentSession)).scalars()
        return instrumentSessionsSchema.jsonify(session_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@main.route('/api/instrumentsession/<int:id>', methods=['PATCH'])
def update_session(id):
    try:
        session = db.session.execute(db.select(InstrumentSession).filter_by(id=id)).scalar_one()
        if "start_date" in request.json:
            session.start_date = datetime.fromisoformat(request.json["start_date"])
        if "end_date" in request.json:
            session.end_date = datetime.fromisoformat(request.json["end_date"])
        if "instrument_id" in request.json:
            session.instrument_id = request.json["instrument_id"]
        if "project_id" in request.json:
            session.project_id = int(request.json["project_id"])

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
                person_id = person_data["person_id"]
                onsite = person_data.get("onsite", False)
                role = person_data.get("role", "")
                remote_access_level = person_data.get("remote_access_level", "")

                print(f"Adding person: {person_data}", file=sys.stderr)

                if person_id in current_person_ids:
                    # Update existing record
                    db.session.execute(
                        session_person_link.update()
                        .where(session_person_link.c.session_id == id)
                        .where(session_person_link.c.person_id == person_id)
                        .values(onsite=onsite, role=role, remote_access_level=remote_access_level)
                    )
                    current_person_ids.remove(person_id)  # Mark as processed
                else:
                    # Insert new record
                    db.session.execute(
                        session_person_link.insert().values(
                            session_id=id,
                            person_id=person_id,
                            onsite=onsite,
                            role=role,
                            remote_access_level=remote_access_level
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
        print(err, file=sys.stderr)
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
@main.route('/api/instrumentsession/<int:id>', methods=['DELETE'])
def delete_session(id):
    try:
        session = db.session.execute(db.select(InstrumentSession).filter_by(id=id)).scalar_one()
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": f"{session} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@roles_accepted('Admin')
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


@main.route('/api/instrumentissues/<int:id>', methods=['GET'])
def get_instrumentissue_by_id(id):
    try:
        issue = db.get_or_404(InstrumentIssue, id)
        return instrumentIssueSchema.jsonify(issue)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/instrumentissues', methods=['GET'])
def get_instrumentissue_list():
    try:
        issue_list = db.session.execute(db.select(InstrumentIssue)).scalars()
        return instrumentIssuesSchema.jsonify(issue_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

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

@roles_accepted('Admin')
@main.route('/api/instrumentissues/<int:id>', methods=['DELETE'])
def delete_instrumentissue(id):
    try:
        session = db.session.execute(db.select(InstrumentIssue).filter_by(id=id)).scalar_one()
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": f"{session} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})


