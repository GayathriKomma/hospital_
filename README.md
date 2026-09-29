# Healthcare Backend API

A small Django REST Framework backend for user authentication, patients, doctors,
and patient-doctor assignments. PostgreSQL is the configured application database;
JWT access tokens protect the healthcare endpoints.

## Requirements

- Python 3.10+
- PostgreSQL 13+

## Run locally

1. Create and activate a virtual environment, then install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Create a PostgreSQL database named `healthcare_db` (or choose another name).
   Copy `.env.example` to `.env` and set the values for your environment. The
   `.env` file is ignored by Git and loaded by Django at startup.

   ```powershell
   Copy-Item .env.example .env
   ```

3. Create tables and start the development server:

   ```powershell
   py manage.py migrate
   py manage.py runserver
   ```

   The API is available at `http://127.0.0.1:8000/api/`.

## Authentication flow

1. `POST /api/auth/register/`

   ```json
   {
     "name": "Sam Example",
     "email": "sam@example.com",
     "password": "A-strong-password-123!"
   }
   ```

2. `POST /api/auth/login/` with the same email and password. The response contains
   `access` and `refresh` tokens. Send the access token on protected requests:

   ```text
   Authorization: Bearer <access>
   ```

3. When the access token expires, send the refresh token to
   `POST /api/auth/refresh/` to get a new access token.

## Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register/` | Create a user |
| POST | `/api/auth/login/` | Get access and refresh JWTs |
| POST | `/api/auth/refresh/` | Refresh an access token |
| GET, POST | `/api/patients/` | List your patients or create a patient |
| GET, PUT, PATCH, DELETE | `/api/patients/<id>/` | Read or manage one of your patients |
| GET, POST | `/api/doctors/` | List doctors or create a doctor |
| GET, PUT, PATCH, DELETE | `/api/doctors/<id>/` | Read or manage a doctor |
| GET, POST | `/api/mappings/` | List your mappings or assign a doctor |
| GET | `/api/mappings/<patient_id>/` | List doctors assigned to your patient |
| DELETE | `/api/mappings/<mapping_id>/` | Remove an assignment from your patient |

Doctor and patient endpoints require authentication. Patient records and mappings
are scoped to the user who created the patient. Doctor records are visible to
authenticated users, as required for doctor discovery.

To assign a doctor, send `patient_id` and `doctor_id` to `/api/mappings/`.
Duplicate assignments and assignments to another user's patient are rejected.
Deleting a patient also removes its mappings; deleting a doctor removes its
assignments.

## Tests

The automated API tests use an in-memory SQLite database for convenient local
execution; normal application settings use PostgreSQL.

```powershell
py manage.py test healthcare --settings=config.test_settings
```
