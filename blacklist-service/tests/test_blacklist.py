import uuid

from app.extensions import db
from app.models import BlacklistEntry

APP_UUID = str(uuid.uuid4())


def _payload(**overrides):
    data = {"email": "spam@example.com", "app_uuid": APP_UUID, "blocked_reason": "spam"}
    data.update(overrides)
    return data


# --- POST /blacklists ---

def test_post_adds_email_and_stores_ip_and_timestamp(client, auth_headers, app):
    resp = client.post("/blacklists", json=_payload(), headers=auth_headers)

    assert resp.status_code == 201
    assert "agregado" in resp.get_json()["message"]

    with app.app_context():
        entry = db.session.scalar(db.select(BlacklistEntry).filter_by(email="spam@example.com"))
        assert entry is not None
        assert entry.app_uuid == APP_UUID
        assert entry.blocked_reason == "spam"
        assert entry.ip_address == "127.0.0.1"
        assert entry.created_at is not None


def test_post_without_blocked_reason_is_allowed(client, auth_headers):
    resp = client.post(
        "/blacklists",
        json={"email": "a@example.com", "app_uuid": APP_UUID},
        headers=auth_headers,
    )
    assert resp.status_code == 201


def test_post_blocked_reason_of_255_chars_is_allowed(client, auth_headers):
    resp = client.post(
        "/blacklists",
        json=_payload(blocked_reason="x" * 255),
        headers=auth_headers,
    )
    assert resp.status_code == 201


def test_post_blocked_reason_longer_than_255_is_rejected(client, auth_headers):
    resp = client.post(
        "/blacklists",
        json=_payload(blocked_reason="x" * 256),
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "blocked_reason" in resp.get_json()["message"]


def test_post_missing_app_uuid_is_rejected(client, auth_headers):
    resp = client.post(
        "/blacklists",
        json={"email": "a@example.com"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "app_uuid" in resp.get_json()["message"]


def test_post_invalid_app_uuid_is_rejected(client, auth_headers):
    resp = client.post("/blacklists", json=_payload(app_uuid="no-es-uuid"), headers=auth_headers)
    assert resp.status_code == 400


def test_post_invalid_email_is_rejected(client, auth_headers):
    resp = client.post("/blacklists", json=_payload(email="no-es-email"), headers=auth_headers)
    assert resp.status_code == 400
    assert "email" in resp.get_json()["message"]


def test_post_duplicate_email_returns_conflict(client, auth_headers):
    assert client.post("/blacklists", json=_payload(), headers=auth_headers).status_code == 201
    resp = client.post("/blacklists", json=_payload(), headers=auth_headers)
    assert resp.status_code == 409


def test_post_non_json_body_is_rejected(client, auth_headers):
    resp = client.post(
        "/blacklists",
        data="esto no es json",
        headers={**auth_headers, "Content-Type": "text/plain"},
    )
    assert resp.status_code == 400


def test_post_without_token_is_unauthorized(client):
    resp = client.post("/blacklists", json=_payload())
    assert resp.status_code == 401


def test_post_with_invalid_token_is_unauthorized(client):
    resp = client.post(
        "/blacklists",
        json=_payload(),
        headers={"Authorization": "Bearer token-falso"},
    )
    assert resp.status_code == 401


# --- GET /blacklists/<email> ---

def test_get_existing_email_returns_true_and_reason(client, auth_headers):
    client.post("/blacklists", json=_payload(), headers=auth_headers)

    resp = client.get("/blacklists/spam@example.com", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.get_json() == {
        "email": "spam@example.com",
        "is_blacklisted": True,
        "blocked_reason": "spam",
    }


def test_get_unknown_email_returns_false(client, auth_headers):
    resp = client.get("/blacklists/nadie@example.com", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.get_json() == {
        "email": "nadie@example.com",
        "is_blacklisted": False,
        "blocked_reason": None,
    }


def test_get_is_case_insensitive(client, auth_headers):
    client.post("/blacklists", json=_payload(email="Juan@Mail.com"), headers=auth_headers)

    resp = client.get("/blacklists/juan@mail.com", headers=auth_headers)

    assert resp.get_json()["is_blacklisted"] is True


def test_get_without_token_is_unauthorized(client):
    resp = client.get("/blacklists/spam@example.com")
    assert resp.status_code == 401


def test_get_with_malformed_token_is_unauthorized(client):
    resp = client.get(
        "/blacklists/spam@example.com",
        headers={"Authorization": "Bearer falso"},
    )
    assert resp.status_code == 401


# --- Infraestructura ---

def test_health_endpoint_does_not_require_token(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
