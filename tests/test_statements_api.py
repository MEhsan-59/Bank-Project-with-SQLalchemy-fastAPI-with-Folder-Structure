def test_statement_endpoints_require_authentication(client):
    full_statement = client.get("/statements")
    mini_statement = client.get("/mini_statements")

    assert full_statement.status_code == 401
    assert mini_statement.status_code == 401


def test_full_statement_contains_deposit_and_transfer_history(
    client, create_account_and_get_headers, get_account_number
):
    sender_headers = create_account_and_get_headers(
        client, "sender", "Sender"
    )
    receiver_headers = create_account_and_get_headers(
        client, "receiver", "Receiver"
    )
    client.post("/deposit", headers=sender_headers, json={"amount": 500})
    preview = client.post(
        "/send_money/preview",
        headers=sender_headers,
        json={
            "receiver_account_no": get_account_number(client, "receiver"),
            "amount": 150,
        },
    )
    client.post(
        "/send_money/confirm",
        headers=sender_headers,
        json={"transaction_id": preview.json()["transaction_id"]},
    )

    sender_statement = client.get("/statements", headers=sender_headers)
    receiver_statement = client.get("/statements", headers=receiver_headers)

    assert sender_statement.status_code == 200
    assert [item["type"] for item in sender_statement.json()["transactions"]] == [
        "transfer_out",
        "deposit",
    ]
    sender_transfer = sender_statement.json()["transactions"][0]
    assert sender_transfer["amount"] == 150
    assert sender_transfer["balance_after"] == 350
    assert sender_transfer["related_account"] == get_account_number(
        client, "receiver"
    )
    assert sender_transfer["created_at"] is not None

    receiver_transactions = receiver_statement.json()["transactions"]
    assert len(receiver_transactions) == 1
    assert receiver_transactions[0]["type"] == "transfer_in"
    assert receiver_transactions[0]["amount"] == 150
    assert receiver_transactions[0]["balance_after"] == 150
    assert receiver_transactions[0]["related_account"] == get_account_number(
        client, "sender"
    )


def test_mini_statement_returns_only_latest_five_transactions(
    client, create_account_and_get_headers
):
    headers = create_account_and_get_headers(client, "sender", "Sender")
    for amount in range(1, 8):
        response = client.post(
            "/deposit", headers=headers, json={"amount": amount}
        )
        assert response.status_code == 200

    response = client.get("/mini_statements", headers=headers)

    assert response.status_code == 200
    transactions = response.json()["transactions"]
    assert len(transactions) == 5
    assert [item["amount"] for item in transactions] == [7, 6, 5, 4, 3]
    assert [item["balance_after"] for item in transactions] == [
        28,
        21,
        15,
        10,
        6,
    ]


def test_failed_transfer_does_not_create_statement_entries(
    client, create_account_and_get_headers, get_account_number
):
    sender_headers = create_account_and_get_headers(
        client, "sender", "Sender"
    )
    create_account_and_get_headers(client, "receiver", "Receiver")
    preview = client.post(
        "/send_money/preview",
        headers=sender_headers,
        json={
            "receiver_account_no": get_account_number(client, "receiver"),
            "amount": 10,
        },
    )

    assert preview.status_code == 400
    statement = client.get("/statements", headers=sender_headers)
    assert statement.status_code == 200
    assert statement.json()["transactions"] == []
