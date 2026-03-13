"""
Backup routes.

Backup settings form management, and running backups.
"""

import os
import traceback
from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    jsonify,
    redirect,
    send_file,
    flash,
)
from lute.db import db
from lute.models.repositories import UserSettingRepository
from lute.backup.service import Service


bp = Blueprint("backup", __name__, url_prefix="/backup")


def _get_settings():
    "Get backup settings."
    repo = UserSettingRepository(db.session)
    return repo.get_backup_settings()


@bp.route("/index")
def index():
    """
    List all backups.
    """
    settings = _get_settings()
    service = Service(db.session)

    # Protect against invalid backup_dir values (eg. Windows path inside
    # a Linux container). If the directory doesn't exist, show the page
    # with an empty list and a helpful message instead of failing with
    # FileNotFoundError.
    backups = []
    backup_error = None
    if not settings.backup_dir:
        backup_error = (
            "No backup directory configured. Please set one in Settings."
        )
    elif not os.path.exists(settings.backup_dir):
        backup_error = (
            f"Backup directory does not exist: {settings.backup_dir}. "
            "This often happens when a Windows path is used in a Linux container, "
            "or when the directory has been moved. "
            "Please update your backup directory in Settings."
        )
    else:
        backups = service.list_backups(settings.backup_dir)
        backups.sort(reverse=True)

    return render_template(
        "backup/index.html",
        backup_dir=settings.backup_dir,
        backups=backups,
        backup_error=backup_error,
    )


@bp.route("/download/<filename>")
def download_backup(filename):
    "Download the given backup file."
    settings = _get_settings()
    if not settings.backup_dir:
        return (jsonify({"errmsg": "No backup directory configured."}), 404)
    fullpath = os.path.join(settings.backup_dir, filename)
    if not os.path.exists(fullpath):
        return (jsonify({"errmsg": f"Backup file not found: {filename}"}), 404)
    return send_file(fullpath, as_attachment=True)


@bp.route("/backup", methods=["GET"])
def backup():
    """
    Endpoint called from front page.

    With extra arg 'type' for manual.
    """
    backuptype = "automatic"
    if "type" in request.args:
        backuptype = "manual"

    settings = _get_settings()
    return render_template(
        "backup/backup.html", backup_folder=settings.backup_dir, backuptype=backuptype
    )


@bp.route("/do_backup", methods=["POST"])
def do_backup():
    """
    Ajax endpoint called from backup.html.
    """
    backuptype = "automatic"
    prms = request.form.to_dict()
    if "type" in prms:
        backuptype = prms["type"]

    c = current_app.env_config
    settings = _get_settings()
    service = Service(db.session)
    is_manual = backuptype.lower() == "manual"
    try:
        f = service.create_backup(c, settings, is_manual=is_manual)
        flash(f"Backup created: {f}", "notice")
        return jsonify(f)
    except Exception as e:  # pylint: disable=broad-exception-caught
        tb = traceback.format_exc()
        return jsonify({"errmsg": str(e) + " -- " + tb}), 500


@bp.route("/skip_this_backup", methods=["GET"])
def handle_skip_this_backup():
    "Update last backup date so backup not attempted again."
    service = Service(db.session)
    service.skip_this_backup()
    return redirect("/", 302)
