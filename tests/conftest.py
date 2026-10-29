import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

load_dotenv(Path(__file__).resolve().parent.parent / "core" / ".env")
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "Add this line to core/.env first: "
        "TEST_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/bank_test"
    )
if "test" not in (make_url(TEST_DATABASE_URL).database or "").lower():
    raise RuntimeError(
        "The database name in TEST_DATABASE_URL must contain 'test' "
        "(the tests delete all tables in it)."
    )
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from core.database import Base, get_db
from core.config import settings
from main import app
from models import Account
from routers.accounts import limiter
from utils.security import hash_password


@pytest.fixture
def client():
    limiter.reset()
    engine = create_engine(TEST_DATABASE_URL)
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.state.test_session_local = testing_session_local
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        del app.state.test_session_local
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def create_account_and_get_headers():
    def create(client, user_id, user_name):
        created = client.post(
            "/create_account",
            json={
                "user_id": user_id,
                "user_name": user_name,
                "password": "12345678",
            },
        )
        assert created.status_code == 200, created.text
        login = client.post(
            "/login_account",
            json={"user_id": user_id, "password": "12345678"},
        )
        assert login.status_code == 200, login.text
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


@pytest.fixture
def get_account_number():
    def get_number(client, user_id):
        db = client.app.state.test_session_local()
        try:
            account = db.query(Account).filter_by(user_id=user_id).one()
            return account.account_no
        finally:
            db.close()

    return get_number


@pytest.fixture
def configure_admins(tmp_path, monkeypatch):
    def configure(admins):
        admin_file = tmp_path / "admins.json"
        admin_file.write_text(
            json.dumps({"admins": admins}),
            encoding="utf-8",
        )
        monkeypatch.setattr(settings, "ADMIN_FILE", str(admin_file))
        return admin_file

    return configure


@pytest.fixture
def admin_credentials(configure_admins):
    username = "test-admin"
    password = "admin-password"
    configure_admins(
        [
            {
                "username": username,
                "password": hash_password(password),
                "permissions": [
                    "freeze_account",
                    "unfreeze_account",
                    "view_statements",
                ],
            }
        ]
    )
    return username, password