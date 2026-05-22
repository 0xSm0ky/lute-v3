"Theme picker route + service tests."

from lute.db import db
from lute.models.repositories import UserSettingRepository
from lute.themes.service import Service


def test_picker_renders(client, app_context):
    r = client.get("/theme/")
    assert r.status_code == 200
    body = r.data.decode("utf-8")
    assert "Theme picker" in body or "theme-grid" in body


def test_apply_theme_updates_setting(client, app_context):
    r = client.post("/theme/apply/Night.css")
    assert r.status_code == 200
    data = r.get_json()
    assert data == {"ok": True, "current": "Night.css"}
    repo = UserSettingRepository(db.session)
    assert repo.get_value("current_theme") == "Night.css"


def test_apply_unknown_theme_404s(client, app_context):
    assert client.post("/theme/apply/does_not_exist.css").status_code == 404


def test_preview_returns_css_for_known_theme(client, app_context):
    r = client.get("/theme/preview/Night.css")
    assert r.status_code == 200
    assert "text/css" in r.headers["Content-Type"]
    # Night theme should be non-empty.
    assert len(r.data) > 0


def test_preview_404_for_unknown_theme(client, app_context):
    assert client.get("/theme/preview/nope.css").status_code == 404


def test_save_custom_styles(client, app_context):
    r = client.post(
        "/theme/custom_styles", data={"custom_styles": "body { color: red }"}
    )
    assert r.status_code == 200
    assert r.get_json() == {"ok": True}
    repo = UserSettingRepository(db.session)
    assert repo.get_value("custom_styles") == "body { color: red }"


def test_get_theme_css_for_default_returns_empty(app_context):
    svc = Service(db.session)
    assert svc.get_theme_css("-") == ""
    assert svc.get_theme_css(None) == ""


def test_get_theme_css_for_known_theme_returns_body(app_context):
    svc = Service(db.session)
    css = svc.get_theme_css("Night.css")
    assert isinstance(css, str)
    assert len(css) > 0
