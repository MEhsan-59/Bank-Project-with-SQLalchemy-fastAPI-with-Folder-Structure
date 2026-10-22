import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from main import app
from models import Account
from utils.security import decode_access_token


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.state.test_session_local = TestingSessionLocal
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    del app.state.test_session_local
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_create_account_persists_hashed_password_and_account_number(client):
    response = client.post(
        "/create_account",
        json={
            "user_id": "ihsan",
            "user_name": "M. Ihsan",
            "password": "12345678",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": True,
        "message": (
            "Account Successfully created Your account_no is AC4000."
        ),
    }

    db = client.app.state.test_session_local()
    try:
        account = db.query(Account).filter_by(user_id="ihsan").one()
        assert account.password != "12345678"
        assert account.account_no == "AC4000"
        assert account.balance == 0
    finally:
        db.close()


def test_create_account_rejects_duplicate_user_id(client):
    payload = {
        "user_id": "ihsan",
        "user_name": "M. Ihsan",
        "password": "12345678",
    }
    assert client.post("/create_account", json=payload).status_code == 200

    response = client.post("/create_account", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Account already exists."


def test_login_returns_bearer_token_for_valid_credentials(client):
    client.post(
        "/create_account",
        json={
            "user_id": "ihsan",
            "user_name": "M. Ihsan",
            "password": "12345678",
        },
    )

    response = client.post(
        "/login_account",
        json={"user_id": "ihsan", "password": "12345678"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    token_payload = decode_access_token(response.json()["access_token"])
    assert token_payload is not None
    assert token_payload["sub"] == "ihsan"
    assert token_payload["role"] == "user"


def test_login_rejects_invalid_password(client):
    client.post(
        "/create_account",
        json={
            "user_id": "ihsan",
            "user_name": "M. Ihsan",
            "password": "12345678",
        },
    )

    response = client.post(
        "/login_account",
        json={"user_id": "ihsan", "password": "wrongpass"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid user_id or password"


def test_create_account_validates_required_fields(client):
    response = client.post(
        "/create_account",
        json={"user_id": "ab", "user_name": "", "password": "short"},
    )

    assert response.status_code == 422
