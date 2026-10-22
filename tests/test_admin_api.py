from utils.security import decode_access_token


def login_admin(client, username, password):
    response = client.post(
        "/login_account",
        json={"user_id": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_login_token_includes_role_and_permissions(
    client, admin_credentials
):
    username, password = admin_credentials

    response = client.post(
        "/login_account",
        json={"user_id": username, "password": password},
    )

    assert response.status_code == 200
    payload = decode_access_token(response.json()["access_token"])
    assert payload is not None
    assert payload["sub"] == username
    assert payload["role"] == "admin"
    assert payload["permissions"] == [
        "freeze_account",
        "unfreeze_account",
        "view_statements",
    ]


def test_admin_login_rejects_invalid_password(client, admin_credentials):
    username, _ = admin_credentials

    response = client.post(
        "/login_account",
        json={"user_id": username, "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_admin_username_cannot_be_registered_as_user(
    client, admin_credentials
):
    username, _ = admin_credentials

    response = client.post(
        "/create_account",
        json={
            "user_id": username,
            "user_name": "Fake Admin",
            "password": "user-password",
        },
    )

    assert response.status_code == 409


def test_freeze_account_requires_admin_token(
    client, create_account_and_get_headers, get_account_number
):
    user_headers = create_account_and_get_headers(client, "customer", "Customer")
    account_no = get_account_number(client, "customer")

    response = client.post(
        f"/admin/freeze_account/{account_no}",
        headers=user_headers,
    )

    assert response.status_code == 403


def test_admin_freezes_account_and_blocks_transfers(
    client,
    admin_credentials,
    create_account_and_get_headers,
    get_account_number,
):
    username, password = admin_credentials
    admin_headers = login_admin(client, username, password)
    sender_headers = create_account_and_get_headers(
        client, "sender", "Sender"
    )
    create_account_and_get_headers(client, "receiver", "Receiver")
    client.post("/deposit", headers=sender_headers, json={"amount": 100})
    sender_account_no = get_account_number(client, "sender")

    freeze = client.post(
        f"/admin/freeze_account/{sender_account_no}",
        headers=admin_headers,
    )
    preview = client.post(
        "/send_money/preview",
        headers=sender_headers,
        json={
            "receiver_account_no": get_account_number(client, "receiver"),
            "amount": 10,
        },
    )

    assert freeze.status_code == 200
    assert freeze.json() == {
        "success": True,
        "message": "Account has been frozen successfully.",
    }
    assert preview.status_code == 403
    assert preview.json()["detail"] == (
        "Your account is frozen. Please contact the admin."
    )


def test_freezing_account_twice_returns_not_found(
    client,
    admin_credentials,
    create_account_and_get_headers,
    get_account_number,
):
    username, password = admin_credentials
    admin_headers = login_admin(client, username, password)
    create_account_and_get_headers(client, "customer", "Customer")
    account_no = get_account_number(client, "customer")

    first = client.post(
        f"/admin/freeze_account/{account_no}",
        headers=admin_headers,
    )
    second = client.post(
        f"/admin/freeze_account/{account_no}",
        headers=admin_headers,
    )

    assert first.status_code == 200
    assert second.status_code == 404


def test_admin_unfreezes_account_and_transfers_are_allowed_again(
    client,
    admin_credentials,
    create_account_and_get_headers,
    get_account_number,
):
    username, password = admin_credentials
    admin_headers = login_admin(client, username, password)
    sender_headers = create_account_and_get_headers(
        client, "sender", "Sender"
    )
    create_account_and_get_headers(client, "receiver", "Receiver")
    client.post("/deposit", headers=sender_headers, json={"amount": 100})
    sender_account_no = get_account_number(client, "sender")

    freeze = client.post(
        f"/admin/freeze_account/{sender_account_no}",
        headers=admin_headers,
    )
    unfreeze = client.post(
        f"/admin/unfreeze_account/{sender_account_no}",
        headers=admin_headers,
    )
    preview = client.post(
        "/send_money/preview",
        headers=sender_headers,
        json={
            "receiver_account_no": get_account_number(client, "receiver"),
            "amount": 10,
        },
    )

    assert freeze.status_code == 200
    assert unfreeze.status_code == 200
    assert unfreeze.json() == {
        "success": True,
        "message": "Account has been unfrozen successfully.",
    }
    assert preview.status_code == 200


def test_unfreeze_returns_not_found_for_account_not_frozen(
    client,
    admin_credentials,
    create_account_and_get_headers,
    get_account_number,
):
    username, password = admin_credentials
    admin_headers = login_admin(client, username, password)
    create_account_and_get_headers(client, "customer", "Customer")
    account_no = get_account_number(client, "customer")

    response = client.post(
        f"/admin/unfreeze_account/{account_no}",
        headers=admin_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found or not frozen."


def test_admin_without_unfreeze_permission_cannot_unfreeze_account(
    client,
    configure_admins,
    create_account_and_get_headers,
    get_account_number,
):
    from utils.security import hash_password

    configure_admins(
        [
            {
                "username": "freeze-admin",
                "password": hash_password("admin-password"),
                "permissions": ["freeze_account"],
            }
        ]
    )
    admin_headers = login_admin(client, "freeze-admin", "admin-password")
    create_account_and_get_headers(client, "customer", "Customer")
    account_no = get_account_number(client, "customer")

    response = client.post(
        f"/admin/unfreeze_account/{account_no}",
        headers=admin_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Admin permission required: unfreeze_account."
    )


def test_admin_can_view_account_statement(
    client,
    admin_credentials,
    create_account_and_get_headers,
    get_account_number,
):
    username, password = admin_credentials
    admin_headers = login_admin(client, username, password)
    customer_headers = create_account_and_get_headers(
        client, "customer", "Customer"
    )
    client.post("/deposit", headers=customer_headers, json={"amount": 120})
    account_no = get_account_number(client, "customer")

    response = client.get(
        f"/admin/statements/{account_no}",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert len(response.json()["transactions"]) == 1
    assert response.json()["transactions"][0]["type"] == "deposit"


def test_admin_statement_requires_admin_role(
    client, create_account_and_get_headers, get_account_number
):
    user_headers = create_account_and_get_headers(
        client, "customer", "Customer"
    )
    account_no = get_account_number(client, "customer")

    response = client.get(
        f"/admin/statements/{account_no}",
        headers=user_headers,
    )

    assert response.status_code == 403


def test_admin_without_freeze_permission_cannot_freeze_account(
    client,
    configure_admins,
    create_account_and_get_headers,
    get_account_number,
):
    from utils.security import hash_password

    configure_admins(
        [
            {
                "username": "statement-admin",
                "password": hash_password("admin-password"),
                "permissions": ["view_statements"],
            }
        ]
    )
    admin_headers = login_admin(client, "statement-admin", "admin-password")
    create_account_and_get_headers(client, "customer", "Customer")
    account_no = get_account_number(client, "customer")

    response = client.post(
        f"/admin/freeze_account/{account_no}",
        headers=admin_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Admin permission required: freeze_account."
    )


def test_admin_without_statement_permission_cannot_view_statement(
    client,
    configure_admins,
    create_account_and_get_headers,
    get_account_number,
):
    from utils.security import hash_password

    configure_admins(
        [
            {
                "username": "freeze-admin",
                "password": hash_password("admin-password"),
                "permissions": ["freeze_account"],
            }
        ]
    )
    admin_headers = login_admin(client, "freeze-admin", "admin-password")
    create_account_and_get_headers(client, "customer", "Customer")
    account_no = get_account_number(client, "customer")

    response = client.get(
        f"/admin/statements/{account_no}",
        headers=admin_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Admin permission required: view_statements."
    )
