# tests/test_security_admin.py
from fastapi import FastAPI
from fastapi.testclient import TestClient

def make_app():
    from backend.app.routers.admin import router as admin_router
    app = FastAPI()
    app.include_router(admin_router)
    return app

def test_admin_unauthorized(monkeypatch):
    # пустые креды → всегда 401
    monkeypatch.setenv("ADMIN_USER", "")
    monkeypatch.setenv("ADMIN_PASS", "")
    app = make_app()
    c = TestClient(app)
    r = c.get("/admin/ping")
    assert r.status_code == 401
    assert r.headers.get("www-authenticate", "").lower().startswith("basic")

def test_admin_wrong(monkeypatch):
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv("ADMIN_PASS", "secret")
    app = make_app()
    c = TestClient(app)
    r = c.get("/admin/ping", auth=("admin", "wrong"))
    assert r.status_code == 401

def test_admin_ok(monkeypatch):
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv("ADMIN_PASS", "secret")
    app = make_app()
    c = TestClient(app)
    r = c.get("/admin/ping", auth=("admin", "secret"))
    assert r.status_code == 200
    assert r.json() == {"ok": True}
