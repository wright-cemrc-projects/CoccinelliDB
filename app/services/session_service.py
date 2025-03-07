from app.models import InstrumentSession, session_person_link, Person
from app import db
from sqlalchemy import select, join

from dataclasses import dataclass
from datetime import datetime

def is_session_booked(session_id):
    """Check if a session is booked."""
    session = InstrumentSession.query.get(session_id)
    if not session:
        return None  # Or handle it appropriately
    return session.is_booked

# Rather than refactor `session_person_link` to a class, this is a dataclass object
# that can wrap the resulting query and organie into a data structure we can return
@dataclass
class SessionPersonLink:
    session_id: int
    onsite: bool
    role: str
    remote_access_level: str
    first_name: str
    last_name: str
    email: str
    net_id: str

def get_matching_session_persons(instrument_id: int, target_datetime: datetime):

    # Query for a matching InstrumentSession
    session_query = (
        db.session.query(InstrumentSession)
        .filter(
            InstrumentSession.instrument_id == instrument_id,
            InstrumentSession.start_date <= target_datetime,
            InstrumentSession.end_date >= target_datetime
        )
        .first()
    )

    # Define the join between session_person_link and person
    stmt = select(
        session_person_link.c.session_id,
        session_person_link.c.onsite,
        session_person_link.c.role,
        session_person_link.c.remote_access_level,
        Person.first_name,
        Person.last_name,
        Person.email,
        Person.net_id
    ).join(
        Person, session_person_link.c.person_id == Person.id  # Join ORM class directly
    ).where(
        session_person_link.c.session_id == session_query.id
    )

    if not session_query:
        print("No matching InstrumentSession found.")
        return None

    # We are joining the SessionPersonLink, with a Person object 
    #  to include the Person field: first_name, last_name, email, netid

    # Execute query and convert rows to dataclass objects
    session_persons = [
        SessionPersonLink(*row)
         for row in db.session.execute(stmt).fetchall()
    ]

    return session_persons

def check_is_person_allowed(instrument_id: int, target_datetime: datetime, username: str):

    session_persons = get_matching_session_persons(instrument_id, target_datetime)

    for person in session_persons:
        if person.net_id == username and person.remote_access_level == 'remote control':
            return True

    return False