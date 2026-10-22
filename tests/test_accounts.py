from models import Account
from utils.security import decode_access_token


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


def test_create_account_validates_required_fields(client):
    response = client.post(
        "/create_account",
        json={"user_id": "ab", "user_name": "", "password": "short"},
    )

    assert response.status_code == 422


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


def test_change_password_updates_hash_and_login_credentials(
    client, create_account_and_get_headers
):
    headers = create_account_and_get_headers(client, "ihsan", "Ihsan")
    response = client.post(
        "/change_password",
        headers=headers,
        json={
            "old_password": "12345678",
            "new_password": "newpassword",
            "confirm_password": "newpassword",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Password successfully changed.",
    }
    assert client.post(
        "/login_account",
        json={"user_id": "ihsan", "password": "12345678"},
    ).status_code == 401
    assert client.post(
        "/login_account",
        json={"user_id": "ihsan", "password": "newpassword"},
    ).status_code == 200


def test_change_password_rejects_incorrect_old_password(
    client, create_account_and_get_headers
):
    headers = create_account_and_get_headers(client, "ihsan", "Ihsan")

    response = client.post(
        "/change_password",
        headers=headers,
        json={
            "old_password": "wrongpass",
            "new_password": "newpassword",
            "confirm_password": "newpassword",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Old password does not match."
    assert client.post(
        "/login_account",
        json={"user_id": "ihsan", "password": "12345678"},
    ).status_code == 200


def test_change_password_rejects_unmatched_confirmation(
    client, create_account_and_get_headers
):
    headers = create_account_and_get_headers(client, "ihsan", "Ihsan")

    response = client.post(
        "/change_password",
        headers=headers,
        json={
            "old_password": "12345678",
            "new_password": "newpassword",
            "confirm_password": "differentpass",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "New password and confirm password do not match."
    )


def test_change_password_requires_authentication(client):
    response = client.post(
        "/change_password",
        json={
            "old_password": "12345678",
            "new_password": "newpassword",
            "confirm_password": "newpassword",
        },
    )

    assert response.status_code == 401


def test_change_password_validates_password_lengths(
    client, create_account_and_get_headers
):
    headers = create_account_and_get_headers(client, "ihsan", "Ihsan")

    response = client.post(
        "/change_password",
        headers=headers,
        json={
            "old_password": "12345678",
            "new_password": "short",
            "confirm_password": "short",
        },
    )

    assert response.status_code == 422
