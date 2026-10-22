from models import Account


def test_check_balance_requires_authentication(client):
    response = client.get("/check_balance")

    assert response.status_code == 401


def test_check_balance_returns_current_balance(
    client, create_account_and_get_headers
):
    headers = create_account_and_get_headers(client, "sender", "Sender")
    client.post("/deposit", headers=headers, json={"amount": 250})

    response = client.get("/check_balance", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"success": True, "balance": 250}


def test_deposit_updates_balance_and_validates_amount(
    client, create_account_and_get_headers
):
    headers = create_account_and_get_headers(client, "sender", "Sender")

    deposit = client.post("/deposit", headers=headers, json={"amount": 500})
    over_limit = client.post("/deposit", headers=headers, json={"amount": 10001})
    zero_amount = client.post("/deposit", headers=headers, json={"amount": 0})

    assert deposit.status_code == 200
    assert deposit.json() == {
        "success": True,
        "message": "500 successfully deposited.",
        "balance": 500,
    }
    assert over_limit.status_code == 422
    assert zero_amount.status_code == 422
    assert client.get("/check_balance", headers=headers).json()["balance"] == 500


def test_deposit_requires_authentication(client):
    response = client.post("/deposit", json={"amount": 500})

    assert response.status_code == 401


def test_transfer_preview_and_confirmation_update_both_balances(
    client, create_account_and_get_headers, get_account_number
):
    sender_headers = create_account_and_get_headers(
        client, "sender", "Sender"
    )
    receiver_headers = create_account_and_get_headers(
        client, "receiver", "Receiver"
    )
    client.post("/deposit", headers=sender_headers, json={"amount": 800})
    receiver_account_no = get_account_number(client, "receiver")

    preview = client.post(
        "/send_money/preview",
        headers=sender_headers,
        json={"receiver_account_no": receiver_account_no, "amount": 300},
    )

    assert preview.status_code == 200
    assert preview.json()["receiver_name"] == "Receiver"
    assert preview.json()["receiver_account_no"] == receiver_account_no
    assert preview.json()["amount"] == 300
    assert client.get(
        "/check_balance", headers=receiver_headers
    ).json()["balance"] == 0

    confirmation = client.post(
        "/send_money/confirm",
        headers=sender_headers,
        json={"transaction_id": preview.json()["transaction_id"]},
    )

    assert confirmation.status_code == 200
    assert client.get(
        "/check_balance", headers=sender_headers
    ).json()["balance"] == 500
    assert client.get(
        "/check_balance", headers=receiver_headers
    ).json()["balance"] == 300


def test_transfer_cannot_be_confirmed_twice(
    client, create_account_and_get_headers, get_account_number
):
    sender_headers = create_account_and_get_headers(
        client, "sender", "Sender"
    )
    create_account_and_get_headers(client, "receiver", "Receiver")
    client.post("/deposit", headers=sender_headers, json={"amount": 100})
    preview = client.post(
        "/send_money/preview",
        headers=sender_headers,
        json={
            "receiver_account_no": get_account_number(client, "receiver"),
            "amount": 50,
        },
    )
    payload = {"transaction_id": preview.json()["transaction_id"]}

    first_confirmation = client.post(
        "/send_money/confirm", headers=sender_headers, json=payload
    )
    replay = client.post(
        "/send_money/confirm", headers=sender_headers, json=payload
    )

    assert first_confirmation.status_code == 200
    assert replay.status_code == 404
    assert client.get(
        "/check_balance", headers=sender_headers
    ).json()["balance"] == 50


def test_transfer_preview_rejects_self_transfer(
    client, create_account_and_get_headers, get_account_number
):
    headers = create_account_and_get_headers(client, "sender", "Sender")
    account_no = get_account_number(client, "sender")

    response = client.post(
        "/send_money/preview",
        headers=headers,
        json={"receiver_account_no": account_no, "amount": 10},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "You cannot send money to your own account."
    )


def test_transfer_preview_rejects_missing_receiver(
    client, create_account_and_get_headers
):
    headers = create_account_and_get_headers(client, "sender", "Sender")

    response = client.post(
        "/send_money/preview",
        headers=headers,
        json={"receiver_account_no": "AC999999", "amount": 10},
    )

    assert response.status_code == 404


def test_transfer_preview_rejects_insufficient_balance(
    client, create_account_and_get_headers, get_account_number
):
    sender_headers = create_account_and_get_headers(
        client, "sender", "Sender"
    )
    create_account_and_get_headers(client, "receiver", "Receiver")

    response = client.post(
        "/send_money/preview",
        headers=sender_headers,
        json={
            "receiver_account_no": get_account_number(client, "receiver"),
            "amount": 10,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient balance."


def test_transfer_preview_and_confirmation_require_authentication(client):
    preview = client.post(
        "/send_money/preview",
        json={"receiver_account_no": "AC4000", "amount": 10},
    )
    confirm = client.post(
        "/send_money/confirm",
        json={"transaction_id": "0" * 36},
    )

    assert preview.status_code == 401
    assert confirm.status_code == 401


def test_only_sender_can_confirm_pending_transfer(
    client, create_account_and_get_headers, get_account_number
):
    sender_headers = create_account_and_get_headers(
        client, "sender", "Sender"
    )
    receiver_headers = create_account_and_get_headers(
        client, "receiver", "Receiver"
    )
    client.post("/deposit", headers=sender_headers, json={"amount": 50})
    preview = client.post(
        "/send_money/preview",
        headers=sender_headers,
        json={
            "receiver_account_no": get_account_number(client, "receiver"),
            "amount": 10,
        },
    )

    confirmation = client.post(
        "/send_money/confirm",
        headers=receiver_headers,
        json={"transaction_id": preview.json()["transaction_id"]},
    )

    assert confirmation.status_code == 403
    assert client.get(
        "/check_balance", headers=sender_headers
    ).json()["balance"] == 50


def test_transfer_confirmation_rechecks_available_balance(
    client, create_account_and_get_headers, get_account_number
):
    sender_headers = create_account_and_get_headers(
        client, "sender", "Sender"
    )
    receiver_headers = create_account_and_get_headers(
        client, "receiver", "Receiver"
    )
    client.post("/deposit", headers=sender_headers, json={"amount": 100})
    preview = client.post(
        "/send_money/preview",
        headers=sender_headers,
        json={
            "receiver_account_no": get_account_number(client, "receiver"),
            "amount": 100,
        },
    )

    db = client.app.state.test_session_local()
    try:
        sender = db.query(Account).filter_by(user_id="sender").one()
        sender.balance = 0
        db.commit()
    finally:
        db.close()

    confirmation = client.post(
        "/send_money/confirm",
        headers=sender_headers,
        json={"transaction_id": preview.json()["transaction_id"]},
    )

    assert confirmation.status_code == 400
    assert confirmation.json()["detail"] == "Insufficient balance."
    assert client.get(
        "/check_balance", headers=receiver_headers
    ).json()["balance"] == 0


def test_transfer_confirmation_validates_transaction_id(
    client, create_account_and_get_headers
):
    headers = create_account_and_get_headers(client, "sender", "Sender")
    response = client.post(
        "/send_money/confirm",
        headers=headers,
        json={"transaction_id": "not-a-uuid"},
    )

    assert response.status_code == 422
