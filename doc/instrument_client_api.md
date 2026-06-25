# Instrument Client API

This API allows instrument-side client scripts to log data collections and
instrument sessions without requiring a user login. It is implemented in
[`routes/instrument_client_routes.py`](../routes/instrument_client_routes.py).

A working example client is in
[`dev/client_collection_prototype.py`](../dev/client_collection_prototype.py).

## Authentication

Every request must include an API key header:

```
X-API-Key: <INSTRUMENT_API_KEY>
```

The expected key is configured via the `INSTRUMENT_API_KEY` setting in the
Flask app config. Requests without a valid key receive `401 Unauthorized`.

## Identifying a Project

`InstrumentSession` records can optionally be linked to a `Project`. The
`Project` model has two identifiers:

- `id` - the integer primary key (the value referenced as `project_id` on an
  `InstrumentSession`).
- `project_id` - a free-form string identifier (e.g. an MCCET project code)
  assigned outside the database.

Client scripts typically only know the string project code, so the API
accepts either form (see `project_string_id` below) and will resolve the
string code to the integer `id` automatically. Lookups by `project_id`
string are case-insensitive.

### `GET /api/client/projects`

Look up a `Project` by its string `project_id` to get its integer `id`.

Query parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `project_id` | string | yes | The `Project.project_id` string code (case-insensitive). |

Responses:

- `200 OK` - the matching `Project` (including its integer `id`).
- `404 Not Found` - no `Project` with that string code exists. Body is `null`.
- `400 Bad Request` - `project_id` query parameter was missing.

## Instrument Sessions

### `GET /api/client/instrumentsessions`

Find existing `InstrumentSession`s, e.g. to link a new collection to an
ongoing session instead of creating a new one.

Query parameters (all optional, but typically used together):

| Name | Type | Description |
| --- | --- | --- |
| `instrument_name` | string | Filter to sessions on the instrument with this name. |
| `datetime` | ISO 8601 datetime | Filter to sessions whose `start_date`/`end_date` window contains this time. |

Responses:

- If both `instrument_name` and `datetime` are provided and at least one
  session matches, returns `200 OK` with a single session object (the first
  match).
- Otherwise, returns `200 OK` with a list of matching sessions.
- `404 Not Found` - no sessions matched. Body is `null`.

### `POST /api/client/instrumentsessions`

Create a new `InstrumentSession`.

Request body (JSON):

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `instrument_id` | integer | yes | `Instrument.id`. |
| `facility_id` | integer | yes | `Facility.id`. |
| `start_date` | ISO 8601 datetime | no | Session start time. |
| `end_date` | ISO 8601 datetime | no | Session end time. Must be after `start_date`. |
| `project_id` | integer | no | `Project.id` to link this session to. |
| `project_string_id` | string | no | `Project.project_id` string code, looked up to find `Project.id` (case-insensitive). Use this instead of `project_id` if you only know the project's string code. |

If both `project_id` and `project_string_id` are omitted, the session is
created with no associated project.

Responses:

- `201 Created` - the new `InstrumentSession`.
- `404 Not Found` - `project_string_id` was provided but no matching `Project` exists.
- `400 Bad Request` - missing required fields or invalid data.

### `PATCH /api/client/instrumentsessions/<id>`

Update an existing `InstrumentSession`, e.g. to set `end_date` once a
collection finishes.

Request body (JSON), all fields optional:

| Field | Type | Description |
| --- | --- | --- |
| `start_date` | ISO 8601 datetime | New start time. |
| `end_date` | ISO 8601 datetime | New end time. Must be after `start_date`. |
| `project_id` | integer | `Project.id` to link this session to. |
| `project_string_id` | string | `Project.project_id` string code, looked up to find `Project.id` (case-insensitive). |

Responses:

- `200 OK` - the updated `InstrumentSession`.
- `404 Not Found` - the session does not exist, or `project_string_id` was
  provided but no matching `Project` exists.
- `400 Bad Request` - invalid data.

## Collections

### `POST /api/client/collections`

Create a new `Collection` linked to an `InstrumentSession`.

Request body (JSON):

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `instrument_session_id` | integer | yes | `InstrumentSession.id` this collection belongs to. |
| `data_location` | string | no | Filesystem path to the collection. Must be unique. |
| `start_date` | ISO 8601 datetime | no | Collection start time. |
| `end_date` | ISO 8601 datetime | no | Collection end time. |
| `total_image_count` | integer | no | Number of images in the collection. |
| `collection_type` | string | no | e.g. `Screening`, `SPA`, `CryoET`. |

If `data_location` is provided and a `Collection` with that path already
exists, the existing record is returned with `409 Conflict` instead of
creating a duplicate.

Responses:

- `201 Created` - the new `Collection`.
- `409 Conflict` - a `Collection` with this `data_location` already exists.
- `404 Not Found` - `instrument_session_id` does not refer to an existing session.
- `400 Bad Request` - missing or invalid data.

### `GET /api/client/collections/<id>`

Fetch a single `Collection` by its integer `id`.

Responses:

- `200 OK` - the `Collection`.
- `404 Not Found` - no `Collection` with this `id`.

### `GET /api/client/collections`

List or look up `Collection`s.

Query parameters (optional):

| Name | Type | Description |
| --- | --- | --- |
| `data_location` | string | If set, return the single `Collection` with this path (or `404`/`null` if none exists). |
| `instrument_session_id` | integer | If set (and `data_location` is not), return all `Collection`s belonging to this session. |

If neither parameter is provided, all `Collection`s are returned.

Responses:

- `200 OK` - a single `Collection` (when `data_location` is set) or a list of `Collection`s.
- `404 Not Found` - `data_location` was set but no matching `Collection` exists. Body is `null`.
- `400 Bad Request` - invalid data.
