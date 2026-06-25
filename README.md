# CoccinelliDB
React, Flask, and SQLAlchemy DB interface

# Setup environment (development)

```
pip install virtualenv
python -m venv venv

# For mac
source ./venv/bin/activate

pip install -r requirements.txt

# start server
python app.py

cd client

npm install

# start client
npx run dev
```

# Updating the database
`flask db migrate -m "Added a table"`

# API documentation
- [Instrument Client API](doc/instrument_client_api.md) - API for instrument-side scripts to log collections and instrument sessions.
