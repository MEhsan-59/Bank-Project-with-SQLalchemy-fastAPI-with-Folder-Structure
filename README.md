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

### Change password

`POST /change_password` requires a valid bearer token and the current password:

```json
{
  "old_password": "12345678",
  "new_password": "newpassword",
  "confirm_password": "newpassword"
}
```

All passwords must contain 8–72 characters. The current password must match
and the new password must match its confirmation. On success, the new password
is stored as a bcrypt hash and can be used to log in.

## Balance and money transfers

All money endpoints require the bearer access token returned by login:

```http
Authorization: Bearer <access_token>
```

### Show balance

`GET /check_balance` returns the authenticated user's current balance.

### Deposit

`POST /deposit`

```json
{
  "amount": 500
}
```

The amount must be a positive whole number no greater than 10,000. The
response includes the updated balance.

### Send money

Transfers use a preview-and-confirm flow. First call `POST
/send_money/preview` with the recipient's account number and a positive amount:

```json
{
  "receiver_account_no": "AC4001",
  "amount": 200
}
```

The preview response includes the recipient name and a one-time
`transaction_id`. Confirm that transfer with `POST /send_money/confirm`:

```json
{
  "transaction_id": "<transaction_id from preview>"
}
```

The recipient must exist, transfers to your own account are rejected, and
available funds are rechecked when confirming. A transaction can only be
confirmed once, and only by the account that previewed it.

## Statements

Statement endpoints require the bearer access token returned by login.

- `GET /statements` returns the account's complete transaction history.
- `GET /mini_statements` returns the latest five transaction entries.

Each transaction includes its type (`deposit`, `transfer_out`, or
`transfer_in`), amount, balance after the transaction, related account when
applicable, and timestamp. Completed transfers are recorded for both accounts.
Failed transactions are not added to the statement.

Run all tests from the project root or the `tests` directory:

```powershell
pytest -v
```

The root `pytest.ini` adds the project root to Python's import path, so both
test invocation locations can import the application packages.
