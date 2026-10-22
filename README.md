# Bank Project API

A FastAPI and SQLAlchemy banking API with account registration and JWT login.

## Setup

Install dependencies with `pip install -r requirements.txt`, then configure
`core/.env` (or environment variables) with:

```dotenv
SECRET_KEY=<a-long-random-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./bank.db
```

Create the database table once and start the API:

```powershell
python -c "from core.database import Base, engine; import models; Base.metadata.create_all(bind=engine)"
uvicorn main:app --reload
```

Interactive API documentation is available at `/docs`.

## Account endpoints

### Create account

`POST /create_account`

```json
{
  "user_id": "ihsan",
  "user_name": "M. Ihsan",
  "password": "12345678"
}
```

`user_id` must be 3–30 characters, `user_name` 1–50 characters, and
`password` 8–72 characters. Success returns a status and generated account
number; an existing user ID returns HTTP 409. Passwords are stored as bcrypt
hashes and new accounts start with a zero balance.

### Login

`POST /login_account`

```json
{
  "user_id": "ihsan",
  "password": "12345678"
}
```

Success returns an `access_token` and `token_type: "bearer"`. Invalid
credentials return HTTP 401. Tokens contain the user ID as `sub` and expire
after the configured number of minutes.

Run the focused tests with `python -m pytest`.
