import base64
import json
import stat
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from starlette.middleware.sessions import SessionMiddleware

from app.common.session_secret import load_session_secret
from app.config import Config


def test_generated_key_survives_restarts_and_concurrent_workers(tmp_path):
    path = tmp_path / "system/session-secret"
    with ThreadPoolExecutor(max_workers=8) as pool:
        keys = list(pool.map(lambda _: load_session_secret(path), range(16)))
    assert len(set(keys)) == 1
    assert len(keys[0]) >= 32
    assert load_session_secret(path) == keys[0]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert list(path.parent.glob(".session-*")) == []
    assert load_session_secret(tmp_path / "other/key") != keys[0]


def test_corrupt_key_is_not_replaced_silently(tmp_path):
    path = tmp_path / "key"
    path.write_text("")
    with pytest.raises(ValueError, match="kulcs"):
        load_session_secret(path)
    assert path.read_text() == ""


def test_explicit_session_secret_remains_compatible(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "explicit-existing-signing-key")
    config = Config(host_ip="192.168.1.100")
    assert config.session_secret == "explicit-existing-signing-key"


def test_actual_session_middleware_rejects_public_key_forgery_and_limits_age():
    from app.main import app as application

    middleware = next(
        item for item in application.user_middleware if item.cls is SessionMiddleware
    )
    app = FastAPI()
    options: dict[str, Any] = dict(middleware.kwargs)
    key = options.pop("secret_key")
    app.add_middleware(SessionMiddleware, secret_key=key, **options)

    @app.get("/session")
    def session(request: Request):
        return {"user_id": request.session.get("user_id")}

    @app.post("/session")
    def login(request: Request):
        request.session["user_id"] = "legitimate-user"
        return {"ok": True}

    forged = (
        TimestampSigner("stremhu-source")
        .sign(base64.b64encode(json.dumps({"user_id": "admin"}).encode()))
        .decode()
    )
    with TestClient(app) as client:
        client.cookies.set("stremhu.source", forged)
        assert client.get("/session").json() == {"user_id": None}
        response = client.post("/session")
        assert "Max-Age=2592000" in response.headers["set-cookie"]
        assert client.get("/session").json() == {"user_id": "legitimate-user"}
