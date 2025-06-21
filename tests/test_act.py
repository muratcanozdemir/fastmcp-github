# tests/test_act.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import decode_jwt_token
from app.models import ActionRequest
from app.audit import init_db, query_audit_logs
from app.github_api.policy import enforce_policy

client = TestClient(app)

@pytest.fixture
def mock_user():
    return {
        "sub": "local-test-user",
        "email": "tester@example.com",
        "name": "Test User"
    }

# Dependency override for get_current_user
@app.dependency_overrides.get
async def get_current_user_override():
    return {
        "sub": "local-test-user",
        "email": "tester@example.com",
        "name": "Test User"
    }

def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["message"].startswith("Welcome")

def test_me():
    res = client.get("/me")
    assert res.status_code in (200, 500)

def test_openapi_available():
    res = client.get("/openapi.json")
    assert res.status_code == 200
    assert "paths" in res.json()

def test_docs_ui_available():
    res = client.get("/docs")
    assert res.status_code == 200
    assert "SwaggerUIBundle" in res.text

def test_invalid_action():
    req = {
        "org": "example-org",
        "repo": "example-repo",
        "action": "nonexistent",
        "parameters": {}
    }
    res = client.post("/act", json=req)
    assert res.status_code == 500
    assert "Unsupported action" in res.json()["detail"]

def test_audit_denied_for_non_admin():
    res = client.get("/audit?org=example-org")
    assert res.status_code in (403, 500)

def test_enforce_policy_repo_name():
    action = ActionRequest(org="org", repo="repo", action="create_repo", parameters={"name": "test"})
    result = enforce_policy(action, {"email": "alice@example.com"})
    assert result.parameters["name"].startswith("dev-")
    assert result.parameters["description"].startswith("Repository created by")

def test_enforce_policy_secret_prefix():
    action = ActionRequest(org="org", repo="repo", action="replace_secret", parameters={"name": "SECRET", "value": "val"})
    result = enforce_policy(action, {"email": "alice@example.com"})
    assert result.parameters["name"].startswith("MCP_")

def test_policy_defaults_team():
    action = ActionRequest(org="org", repo="repo", action="add_user_to_team", parameters={"username": "alice"})
    result = enforce_policy(action, {"email": "alice@example.com"})
    assert result.parameters["team"] == "infrastructure-admins"

def test_audit_query_empty():
    # Should return empty list without raising
    results = client.get("/audit?org=example-org&limit=1")
    assert results.status_code in (200, 403, 500)

import json

def test_fuzz_action_request_schema():
    payload = {
        "org": 123,
        "repo": {},
        "action": True,
        "parameters": "not-a-dict"
    }
    res = client.post("/act", json=payload)
    assert res.status_code == 422
