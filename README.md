# Healthcare API

A small Django REST Framework API for email-based registration, JWT login,
patients, doctors, and patient-doctor assignments. PostgreSQL is used by the
application; the test settings use SQLite so API tests do not need a database
server. The project root (`http://127.0.0.1:8000/`) also serves a basic browser
interface for trying the API.

## Architecture

- `config/` is the single Django project. It contains settings and root URLs.
- `healthcare/` is the single app. It contains models, serializers, views, and URLs.
- Patients belong to the account that created them. Patient lists, details, and
  mappings are restricted to that account.
- Doctors are a shared directory; any authenticated user can manage its entries.
- A mapping connects one patient to one doctor. The same doctor cannot be
  assigned to the same patient twice.

## Folder structure

```text
config/
    settings.py
    test_settings.py
    urls.py
    asgi.py
    wsgi.py
healthcare/
    migrations/
    templates/healthcare/
    static/healthcare/
    models.py
    serializers.py
    views.py
    urls.py
    tests.py
manage.py
requirements.txt
.env.example
```

## Models

- `User` uses a unique email address to log in.
- `Patient` has a `created_by` foreign key to `User`.
- `Doctor` is a shared directory entry.
- `PatientDoctorMapping` links a patient and a doctor, with a database constraint
  preventing duplicate assignments.

Patient, doctor, and mapping records include creation/update timestamps where
appropriate.

## API routes

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register/` | Create an account |
| POST | `/api/auth/login/` | Get access and refresh tokens |
| POST | `/api/auth/refresh/` | Refresh an access token |
| GET, POST | `/api/patients/` | List your patients or create one |
| GET, PUT, PATCH, DELETE | `/api/patients/<id>/` | Manage one of your patients |
| GET, POST | `/api/doctors/` | List or create doctors |
| GET, PUT, PATCH, DELETE | `/api/doctors/<id>/` | Manage a doctor |
| GET, POST | `/api/mappings/` | List your assignments or assign a doctor |
| GET, PUT, PATCH, DELETE | `/api/mappings/<id>/` | Manage one of your assignments |

List endpoints use page-number pagination with 10 results per page. All routes
except registration, login, and token refresh require a JWT access token.

## Sample requests

Register:

```json
{
  "name": "Sam Example",
  "email": "sam@example.com",
  "password": "Strong-password-123!"
}
```

Login with `email` and `password`:

```json
{
  "email": "sam@example.com",
  "password": "Strong-password-123!"
}
```

The response contains `access`, `refresh`, and basic user information. Use the
access token in the `Authorization: Bearer <access>` header.

Example login response:

```json
{
  "access": "<access-token>",
  "refresh": "<refresh-token>",
  "user": {
    "id": 1,
    "name": "Sam Example",
    "email": "sam@example.com"
  }
}
```

Create a patient:

```json
{
  "name": "Alex Example",
  "age": 34,
  "gender": "other",
  "email": "alex@example.com",
  "phone": "555-0100",
  "address": "10 Main Street"
}
```

Create a doctor:

```json
{
  "name": "Dr. Lee",
  "specialization": "Cardiology",
  "email": "lee@example.com",
  "phone": "555-0110"
}
```

Assign a doctor:

```json
{
  "patient_id": 1,
  "doctor_id": 1
}
```

Example assignment response:

```json
{
  "id": 1,
  "patient_id": 1,
  "doctor_id": 1,
  "created_at": "2026-09-29T12:00:00Z"
}
```

## Run locally

1. Install Python 3.10+ and PostgreSQL. Create a database (for example,
   `healthcare_db`).
2. In PowerShell, create a virtual environment and install packages:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set your PostgreSQL password and a private
   Django secret key:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Apply migrations and start Django:

   ```powershell
   py manage.py migrate
   py manage.py seed_demo
   py manage.py runserver
   ```

   `seed_demo` adds three synthetic patients, three synthetic doctors, and four
   assignments for `demo@healthcare.example`. If it creates that account, the
   initial password is `CareDemo#2026!`. It does not reset an existing account's
   password. The command is safe to run more than once.

5. Open `http://127.0.0.1:8000/`, sign in with the demo account, and view the
   sample records. The sample people, `.test` email addresses, and phone numbers
   are fictional.

6. Run the tests (they use in-memory SQLite):

   ```powershell
   py manage.py test healthcare --settings=config.test_settings
   ```

The basic browser UI at `http://127.0.0.1:8000/` is only a small convenience for
trying the API; the API is the primary interface.

## Postman test steps

1. Send `POST http://127.0.0.1:8000/api/auth/register/` with the registration
   JSON above.
2. Send `POST http://127.0.0.1:8000/api/auth/login/` with that email/password.
   Copy the `access` value from the response.
3. For protected requests, set **Authorization** to **Bearer Token** and paste
   the access token.
4. Create a patient and doctor using the sample requests.
5. Send the mapping request with their returned IDs, then check
   `GET /api/mappings/`.
6. Register and log in as another account. Its patient list and mappings should
   not show the first account's records.
