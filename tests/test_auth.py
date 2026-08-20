import pytest
from app.security import hash_password, verify_password, create_access_token, decode_token

def test_password_hashing():
    pwd = "MySecretPassword123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_flow():
    token = create_access_token("123e4567-e89b-12d3-a456-426614174000", "user@test.com")
    payload = decode_token(token)
    assert payload is not None
    assert payload.sub == "123e4567-e89b-12d3-a456-426614174000"
    assert payload.email == "user@test.com"
    assert payload.type == "access"

def test_register_and_login_flow(client):
    # 1. Register
    reg_payload = {
        "email": "newuser@travel.com",
        "password": "SecurePassword999",
        "home_locale": "en",
        "full_name": "Captain Alex"
    }
    res_reg = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 201
    data = res_reg.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@travel.com"
    assert data["user"]["full_name"] == "Captain Alex"

    # 2. Login
    login_payload = {
        "email": "newuser@travel.com",
        "password": "SecurePassword999"
    }
    res_login = client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    # 3. Get /me
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "newuser@travel.com"
    assert res_me.json()["full_name"] == "Captain Alex"

def test_update_user_profile(client, auth_headers):
    profile_payload = {
        "full_name": "Zara Explorer",
        "phone_number": "+1 (555) 987-6543",
        "age": 29,
        "country": "Pakistan",
        "city": "Lahore",
        "bio": "Avid mountain trekker and culinary enthusiast.",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&q=80"
    }
    res = client.put("/api/v1/auth/profile", json=profile_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Zara Explorer"
    assert data["phone_number"] == "+1 (555) 987-6543"
    assert data["age"] == 29
    assert data["country"] == "Pakistan"
    assert data["city"] == "Lahore"
    assert "mountain trekker" in data["bio"]
    assert "unsplash" in data["avatar_url"]

def test_update_preferences(client, auth_headers):
    pref_payload = {
        "interests": ["nature", "adventure"],
        "pace_preference": "packed",
        "default_budget_tier": 3
    }
    res = client.put("/api/v1/auth/preferences", json=pref_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["pace_preference"] == "packed"
    assert "adventure" in data["interests"]
    assert data["default_budget_tier"] == 3
