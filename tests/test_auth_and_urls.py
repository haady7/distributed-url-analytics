def create_user_and_token(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={"email": "developer@example.com", "password": "StrongPass!234"},
    )
    assert registration.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "developer@example.com", "password": "StrongPass!234"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_register_login_and_current_user(client):
    headers = create_user_and_token(client)
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "developer@example.com"


def test_duplicate_registration_is_rejected(client):
    create_user_and_token(client)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "developer@example.com", "password": "AnotherPass!234"},
    )
    assert response.status_code == 409


def test_create_short_url_and_ownership(client):
    headers = create_user_and_token(client)
    response = client.post(
        "/api/v1/urls",
        headers=headers,
        json={"original_url": "https://example.com/docs", "custom_code": "docs123"},
    )
    assert response.status_code == 201
    assert response.json()["code"] == "docs123"
    assert response.json()["short_url"].endswith("/docs123")

    detail = client.get("/api/v1/urls/docs123", headers=headers)
    assert detail.status_code == 200


def test_custom_code_collision_returns_conflict(client):
    headers = create_user_and_token(client)
    payload = {"original_url": "https://example.com", "custom_code": "samecode"}
    assert client.post("/api/v1/urls", headers=headers, json=payload).status_code == 201
    response = client.post("/api/v1/urls", headers=headers, json=payload)
    assert response.status_code == 409


def test_unauthenticated_url_creation_is_rejected(client):
    response = client.post("/api/v1/urls", json={"original_url": "https://example.com"})
    assert response.status_code == 401
