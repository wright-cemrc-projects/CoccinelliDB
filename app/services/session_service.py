from app.models import InstrumentSession
from app import db

def is_session_booked(session_id):
    """Check if a session is booked."""
    session = InstrumentSession.query.get(session_id)
    if not session:
        return None  # Or handle it appropriately
    return session.is_booked