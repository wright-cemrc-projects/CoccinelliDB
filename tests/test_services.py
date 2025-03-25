import pytest
import json
import datetime

from app.models import InstrumentSession

def test_is_session_booked(app, db_session):

    start_date = datetime.time("2025-01-28 12:00:00")
    end_date = datetime.time("2025-01-29 12:00:00")
    project_id = 1
    facility_id = 1
    instrument_id = 1

    instrument_session = InstrumentSession(start_date=start_date, end_date=end_date, project_id=project_id, facility_id=facility_id, instrument_id=instrument_id)
    
    # TODO: need to be provided with a db instance here.
    #db.session.add(instrument_session)
    #db.session.commit()

    #assert is_session_booked(1) is True