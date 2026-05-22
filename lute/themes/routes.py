"Theming routes."

from flask import Blueprint, Response, jsonify, render_template, request, abort

from lute.themes.service import Service
from lute.models.repositories import UserSettingRepository
from lute.settings.current import current_settings, refresh_global_settings
from lute.db import db

bp = Blueprint("themes", __name__, url_prefix="/theme")


@bp.route("/current", methods=["GET"])
def current_theme():
    "Return current css."
    service = Service(db.session)
    response = Response(service.get_current_css(), 200)
    response.content_type = "text/css; charset=utf-8"
    return response


@bp.route("/custom_styles", methods=["GET"])
def custom_styles():
    """
    Return the custom settings for inclusion in the base.html.
    """
    repo = UserSettingRepository(db.session)
    css = repo.get_value("custom_styles")
    response = Response(css, 200)
    response.content_type = "text/css; charset=utf-8"
    return response


@bp.route("/next", methods=["POST"])
def set_next_theme():
    "Go to next theme."
    service = Service(db.session)
    service.next_theme()
    return jsonify("ok")


@bp.route("/toggle_highlight", methods=["POST"])
def toggle_highlight():
    "Fix the highlight."
    new_setting = not current_settings["show_highlights"]
    repo = UserSettingRepository(db.session)
    repo.set_value("show_highlights", new_setting)
    db.session.commit()
    current_settings["show_highlights"] = new_setting
    return jsonify("ok")


# ---------------------------------------------------------------------------
# Dedicated theme picker page.
# ---------------------------------------------------------------------------


@bp.route("/", methods=["GET"])
def picker():
    "Theme picker page: card grid + custom styles textarea."
    service = Service(db.session)
    repo = UserSettingRepository(db.session)
    return render_template(
        "themes/picker.html",
        themes=service.list_themes(),
        current=repo.get_value("current_theme"),
        custom_styles=repo.get_value("custom_styles") or "",
    )


def _theme_names(service):
    "Set of known theme filenames (including the default '-')."
    return {t[0] for t in service.list_themes()}


@bp.route("/apply/<path:name>", methods=["POST"])
def apply_theme(name):
    "Set current_theme = name and refresh settings."
    service = Service(db.session)
    if name not in _theme_names(service):
        abort(404)
    repo = UserSettingRepository(db.session)
    repo.set_value("current_theme", name)
    db.session.commit()
    refresh_global_settings(db.session)
    return jsonify({"ok": True, "current": name})


@bp.route("/custom_styles", methods=["POST"])
def save_custom_styles():
    "Save the custom_styles UserSetting from a POST body."
    css = request.form.get("custom_styles", "")
    repo = UserSettingRepository(db.session)
    repo.set_value("custom_styles", css)
    db.session.commit()
    refresh_global_settings(db.session)
    return jsonify({"ok": True})


@bp.route("/preview/<path:name>", methods=["GET"])
def preview_css(name):
    "Return the CSS for an arbitrary theme name; used by preview iframes."
    service = Service(db.session)
    if name not in _theme_names(service):
        abort(404)
    response = Response(service.get_theme_css(name), 200)
    response.content_type = "text/css; charset=utf-8"
    return response
