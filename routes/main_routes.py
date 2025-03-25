from flask import Blueprint, render_template, jsonify, request, session, redirect
from sqlalchemy import or_, inspect
from app import db, oidc
from app.models import Project, Facility, Group, Person, Instrument, InstrumentSession, InstrumentIssue, group_person, session_person_link
from app.schema import facilitySchema, facilitiesSchema, projectSchema, projectsSchema, facilityGroupSchema, facilityGroupsSchema, facilityPersonSchema, facilityPersonsSchema, instrumentSessionSchema, instrumentSessionsSchema, instrumentSchema, instrumentsSchema, instrumentIssueSchema, instrumentIssuesSchema
from datetime import datetime
from flask_security import roles_accepted

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect("http://localhost:5173/")

@main.route('/api/home', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello World"})

@main.route('/api/projects', methods=['GET'])
# @roles_accepted('Admin')
def get_project_list():
    project_list = db.session.execute(db.select(Project)).scalars()
    return projectsSchema.jsonify(project_list)

@main.route('/api/projects/<int:id>', methods=['GET'])
def get_project_by_id(id):
    project_one = db.session.execute(db.select(Project).filter_by(id=id)).scalar_one()
    return projectSchema.jsonify(project_one)

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

@main.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    try:
        project = db.session.execute(db.select(Project).filter_by(id=id)).scalar_one()
        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": f"{project} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/facilities', methods=['GET'])
def get_facility_list():
    if oidc:
        print(oidc)
        print(oidc.user_loggedin)
        print(oidc.get_access_token())
        print(oidc.get_refresh_token())
    facility_list = db.session.execute(db.select(Facility)).scalars()
    return facilitiesSchema.jsonify(facility_list)

@main.route('/api/facilities/<int:id>', methods=['GET'])
def get_facility_by_id(id):
    facility_one = db.session.execute(db.select(Facility).filter_by(id=id)).scalar_one()
    return facilitySchema.jsonify(facility_one)

@main.route('/api/facilities', methods=['POST'])
def create_facility():
    name = request.json["name"]
    try:
        facility = Facility(name)
        db.session.add(facility)
        db.session.commit()
        db.session.flush()
        return jsonify({"message": "new facility created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/facilities/<int:id>', methods=['PATCH'])
def update_facility(id):
    try:
        name = request.json["name"]
        facility = db.session.execute(db.select(Facility).filter_by(id=id)).scalar_one()
        facility.name = name
        db.session.commit()
        return jsonify({"message": f"{facility} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/facilities/<int:id>', methods=['DELETE'])
def delete_facility(id):
    try:
        facility = db.session.execute(db.select(Facility).filter_by(id=id)).scalar_one()
        db.session.delete(facility)
        db.session.commit()
        return jsonify({"message": f"{facility} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/groups', methods=['POST'])
def create_group():
    try:
        name = request.json["name"]
        group = Group(name=name)
        db.session.add(group)
        db.session.commit()
        return jsonify({"message": f"new group {name} created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})


@main.route('/api/groups/<int:id>', methods=['GET'])
def get_group_by_id(id):
    try:
        group = db.get_or_404(Group, id)
        return facilityGroupSchema.jsonify(group)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/groups', methods=['GET'])
def get_group_list():
    try:
        name_like = request.args.get("name_like")
        query = db.session.query(Group)

        if name_like:
            query = query.filter(
                    Group.name.ilike(f"%{name_like}%"),
            )
        return facilityGroupsSchema.jsonify(query.all())
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/groups/<int:id>', methods=['PATCH'])
def update_group(id):
    try:
        group = db.session.execute(db.select(Group).filter_by(id=id)).scalar_one()
        if "name" in request.json:
            group.name = request.json["name"]
        if "persons" in request.json:
            persons_data = request.json["persons"]
            new_persons_set = set(person["id"] for person in persons_data)
            old_persons_set = set([person.id for person in group.persons])
            add_persons = new_persons_set.difference(old_persons_set)
            delete_persons = old_persons_set.difference(new_persons_set)

            for person_id in add_persons:
                person = db.session.execute(db.select(Person).filter_by(id=person_id)).scalar_one()
                group.persons.append(person)
            for person_id in delete_persons:
                person = db.session.execute(db.select(Person).filter_by(id=person_id)).scalar_one()
                group.persons.remove(person)
            for person_data in persons_data:
                stmt = (
                    group_person.update()
                    .where(group_person.c.group_id == group.id)
                    .where(group_person.c.person_id == person_data["id"])
                    .values(primary_contact=person_data.get("primary_contact", False))
                )
                db.session.execute(stmt)
        db.session.commit()
        return jsonify({"message": f"{group} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})    

@main.route('/api/groups/<int:id>', methods=['DELETE'])
def delete_group(id):
    try:
        group = db.session.execute(db.select(Group).filter_by(id=id)).scalar_one()
        db.session.delete(group)
        db.session.commit()
        return jsonify({"message": f"{group} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/persons', methods=['POST'])
def create_person():
    try:
        date_format = "%Y-%m-%dT%H:%M:%S"

        # Get required arguments for initializer
        first_name = None
        if "first_name" in request.json:
            first_name = request.json["first_name"]
        last_name = None
        if "last_name" in request.json:
            last_name = request.json["last_name"]
        net_id = None    
        if "net_id" in request.json:
            net_id = request.json["net_id"]
        email = None
        if "email" in request.json:
            email = request.json["email"]

        if (first_name and last_name and net_id and email) :
            person = Person(first_name = first_name, last_name = last_name, net_id = net_id, email = email)
        else:
            raise Exception('Missing arguments: first_name, last_name, net_id, and email')

        if "group_id" in request.json:
            person.group_id = request.json["group_id"]
        if "address1" in request.json:
            person.address1 = request.json["address1"]
        if "address2" in request.json:
            person.address2 = request.json["address2"]
        if "organization" in request.json:
            person.organization = request.json["organization"]
        if "state" in request.json:
            person.state = request.json["state"]
        if "telephone" in request.json:
            person.telephone = request.json["telephone"]
        if "start_date" in request.json:
            if request.json["start_date"]:
                cleaned_start_date = request.json["start_date"].split(".")[0]
                person.start_date = datetime.strptime(cleaned_start_date, date_format)
            else:
                person.start_date = None
        if "end_date" in request.json:
            if request.json["end_date"]:
                cleaned_end_date = request.json["end_date"].split(".")[0]
                person.end_date = datetime.strptime(cleaned_end_date, date_format)
            else:
                person.end_date = None
        db.session.add(person)
        db.session.commit()
        return jsonify({"message": f"{person} created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/persons/<int:id>', methods=['GET'])
def get_person_by_id(id):
    try:
        person = db.get_or_404(Person, id)
        return facilityPersonSchema.jsonify(person)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/groups/<int:id>/persons', methods=['GET'])
def get_person_by_group(id):
    try:
        group = Group.query.get_or_404(id)
        persons = db.session.execute(
            db.select(
                Person.id,
                Person.first_name,
                Person.last_name,
                Person.email,
                group_person.c.primary_contact
            ).join(group_person).filter(group_person.c.group_id == group.id)
        ).all()

        return facilityPersonsSchema.jsonify(persons)
    except Exception as err:
        return jsonify({"err": f"{err=}"})


@main.route('/api/persons', methods=['GET'])
def get_person_list():
    try:
        full_name_like = request.args.get("full_name_like")
        first_name_like = request.args.get("first_name_like")
        last_name_like = request.args.get("last_name_like")
        if full_name_like is not None:
            name_parse = full_name_like.split(" ")
            if len(name_parse) >= 2:
                last_name_like = name_parse[1]
            first_name_like = name_parse[0]

        query = db.session.query(Person)
        if first_name_like or last_name_like:
            if not first_name_like:
                first_name_like = ""
            if not last_name_like:
                last_name_like = ""
            query = query.filter(
                or_(
                    Person.first_name.ilike(first_name_like),
                    Person.last_name.ilike(last_name_like)
                )
            )

        persons = query.all()

        # Serialize the results using the facilityPersonsSchema
        return facilityPersonsSchema.jsonify(persons)

    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/persons/<int:id>', methods=['PATCH'])
def update_person(id):
    try:
        date_format = "%Y-%m-%dT%H:%M:%S"
        person = db.session.execute(db.select(Person).filter_by(id=id)).scalar_one()
        if "first_name" in request.json:
            person.first_name = request.json["first_name"]
        if "last_name" in request.json:
            person.last_name = request.json["last_name"]
        if "organization" in request.json:
            person.organization = request.json["organization"]
        if "email" in request.json:
            person.email = request.json["email"]
        if "state" in request.json:
            person.state = request.json["state"]
        if "address1" in request.json:
            person.address1 = request.json["address1"]
        if "address2" in request.json:
            person.address2 = request.json["address2"]
        if "country" in request.json:
            person.country = request.json["country"]
        if "telephone" in request.json:
            person.telephone = request.json["telephone"]
        if "net_id" in request.json:
            person.net_id = request.json["net_id"]
        if "start_date" in request.json:
            if request.json["start_date"]:
                cleaned_start_date = request.json["start_date"].split(".")[0]
                person.start_date = datetime.strptime(cleaned_start_date, date_format)
            else:
                person.start_date = None
        if "end_date" in request.json:
            if request.json["end_date"]:
                cleaned_end_date = request.json["end_date"].split(".")[0]
                person.end_date = datetime.strptime(cleaned_end_date, date_format)
            else:
                person.end_date = None
        db.session.commit()
        return jsonify({"message": f"{person} got updated."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/persons/<int:id>', methods=['DELETE'])
def delete_person(id):
    try:
        person = db.session.execute(db.select(Person).filter_by(id=id)).scalar_one()
        db.session.delete(person)
        db.session.commit()
        return jsonify({"message": f"{person} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})
    
# instrument entries
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

@main.route('/api/instruments/<int:id>', methods=['GET'])
def get_instrument_by_id(id):
    try:
        session = db.get_or_404(Instrument, id)
        return instrumentSchema.jsonify(session)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/instruments', methods=['GET'])
def get_instrument_list():
    try:
        instruments_list = db.session.execute(db.select(Instrument)).scalars()
        return instrumentsSchema.jsonify(instruments_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})
     
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

@main.route('/api/instruments/<int:id>', methods=['DELETE'])
def delete_instrument(id):
    try:
        instrument = db.session.execute(db.select(Instrument).filter_by(id=id)).scalar_one()
        db.session.delete(instrument)
        db.session.commit()
        return jsonify({"message": f"{instrument} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

# instrument entries end
    
@main.route('/api/instrumentsession', methods=['POST'])
def create_session():
    try:
        date_format = "%Y-%m-%dT%H:%M:%S"
        cleaned_start_date = request.json["start_date"].split(".")[0]
        start_date = datetime.strptime(cleaned_start_date, date_format)
        cleaned_end_date = request.json["end_date"].split(".")[0]
        end_date = datetime.strptime(cleaned_end_date, date_format)
        instrument_id = int(request.json["instrument_id"])
        project_id = None
        if "project_id" in request.json:
            project_id = int(request.json["project_id"])
        facility_id = int(request.json["facility_id"])
        instrument_session = InstrumentSession(start_date=start_date, end_date=end_date, project_id=project_id, facility_id=facility_id, instrument_id=instrument_id)
        db.session.add(instrument_session)
        db.session.commit()
        return jsonify({"message": f"new instrument session {start_date} created."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})


@main.route('/api/instrumentsession/<int:id>', methods=['GET'])
def get_session_by_id(id):
    try:
        session = db.get_or_404(InstrumentSession, id)
        return instrumentSessionSchema.jsonify(session)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/instrumentsession', methods=['GET'])
def get_session_list():
    try:
        session_list = db.session.execute(db.select(InstrumentSession)).scalars()
        return instrumentSessionsSchema.jsonify(session_list)
    except Exception as err:
        return jsonify({"err": f"{err=}"})

@main.route('/api/instrumentsession/<int:id>', methods=['PATCH'])
def update_session(id):
    try:
        date_format = "%Y-%m-%dT%H:%M:%S"
        session = db.session.execute(db.select(InstrumentSession).filter_by(id=id)).scalar_one()
        if "start_date" in request.json:
            cleaned_start_date = request.json["start_date"].split(".")[0]
            session.start_date = datetime.strptime(cleaned_start_date, date_format)
        if "end_date" in request.json:
            cleaned_end_date = request.json["end_date"].split(".")[0]
            session.end_date = datetime.strptime(cleaned_end_date, date_format)
        if "instrument_id" in request.json:
            session.instrument_id = request.json["instrument_id"]

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

        db.session.commit()
        return jsonify({"message": f"{session} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})    

@main.route('/api/instrumentsession/<int:id>', methods=['DELETE'])
def delete_session(id):
    try:
        session = db.session.execute(db.select(InstrumentSession).filter_by(id=id)).scalar_one()
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": f"{session} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})

# Stat of instrument issue routes

@main.route('/api/instrumentissues', methods=['POST'])
def create_instrumentissue():
    try:
        date_format = "%Y-%m-%dT%H:%M:%S"
        cleaned_start_date = request.json["start_date"].split(".")[0]
        start_date = datetime.strptime(cleaned_start_date, date_format)
        cleaned_end_date = request.json["end_date"].split(".")[0]
        end_date = datetime.strptime(cleaned_end_date, date_format)
        instrument_id = request.json["instrument_id"]
        issue_title = request.json["issue_title"]
        issue_description = request.json["issue_description"]

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
        date_format = "%Y-%m-%dT%H:%M:%S"
        issue = db.session.execute(db.select(InstrumentIssue).filter_by(id=id)).scalar_one()
        if "issue_title" in request.json:
            issue.issue_title = request.json["issue_title"]
        if "issue_description" in request.json:
            issue.issue_description = request.json["issue_description"]
        if "instrument_id" in request.json:
            issue.instrument_id = request.json["instrument_id"]
        if "start_date" in request.json:
            cleaned_start_date = request.json["start_date"].split(".")[0]
            issue.start_date = datetime.strptime(cleaned_start_date, date_format)
        if "end_date" in request.json:
            cleaned_end_date = request.json["end_date"].split(".")[0]
            issue.end_date = datetime.strptime(cleaned_end_date, date_format)
        db.session.commit()
        return jsonify({"message": f"{issue} got updated"})
    except Exception as err:
        return jsonify({"err": f"{err=}"})    

@main.route('/api/instrumentissues/<int:id>', methods=['DELETE'])
def delete_instrumentissue(id):
    try:
        session = db.session.execute(db.select(InstrumentIssue).filter_by(id=id)).scalar_one()
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": f"{session} got deleted."})
    except Exception as err:
        return jsonify({"err": f"{err=}"})


