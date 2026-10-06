from app.security import create_access_token, hash_password, verify_password


def test_register_returns_user(client):
    res = client.post("/auth/register", json={"email": "Ali@Example.com", "password": "secret123"})
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "ali@example.com"
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_email(client):
    payload = {"email": "ali@example.com", "password": "secret123"}
    client.post("/auth/register", json=payload)
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 409


def test_register_rejects_short_password(client):
    res = client.post("/auth/register", json={"email": "ali@example.com", "password": "123"})
    assert res.status_code == 422


def test_login_and_me(client):
    client.post("/auth/register", json={"email": "ali@example.com", "password": "secret123"})
    res = client.post("/auth/login", data={"username": "ali@example.com", "password": "secret123"})
    assert res.status_code == 200
    token = res.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ali@example.com"


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "ali@example.com", "password": "secret123"})
    res = client.post("/auth/login", data={"username": "ali@example.com", "password": "wrongpass"})
    assert res.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/tasks").status_code == 401
    bad = client.get("/tasks", headers={"Authorization": "Bearer not-a-token"})
    assert bad.status_code == 401


def test_expired_token_is_rejected(client):
    client.post("/auth/register", json={"email": "ali@example.com", "password": "secret123"})
    token = create_access_token("1", expires_minutes=-1)
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_password_hashing():
    stored = hash_password("secret123")
    assert stored != "secret123"
    assert verify_password("secret123", stored)
    assert not verify_password("other", stored)
    assert hash_password("secret123") != stored  # random salt
