"""
/stats endpoints.
"""

from flask import Blueprint, render_template, jsonify, abort
from lute.stats import service as stats_service
from lute.models.language import Language
from lute.db import db

bp = Blueprint("stats", __name__, url_prefix="/stats")


_VALID_RANGES = {"1m", "3m", "1y", "all"}


def _validate_range(rng):
    if rng not in _VALID_RANGES:
        abort(404)


@bp.route("/")
def index():
    "Main page."
    read_table_data = stats_service.get_table_data(db.session)
    languages = (
        db.session.query(Language).order_by(Language.name).all()
    )
    language_summary = stats_service.get_language_term_summary(db.session)
    return render_template(
        "stats/index.html",
        read_table_data=read_table_data,
        languages=languages,
        language_summary=language_summary,
        status_labels=stats_service._STATUS_LABELS,
    )


@bp.route("/data")
def get_data():
    "Ajax call -- existing endpoint, kept for back-compat."
    chartdata = stats_service.get_chart_data(db.session)
    return jsonify(chartdata)


# ---------------------------------------------------------------------------
# New JSON endpoints (per language).  Each path takes <lang_id> and, where
# applicable, a <rng> in {1m, 3m, 1y, all}.
# ---------------------------------------------------------------------------


@bp.route("/today/<int:lang_id>")
def today(lang_id):
    return jsonify(stats_service.get_today_summary(db.session, lang_id))


@bp.route("/streaks/<int:lang_id>")
def streaks(lang_id):
    return jsonify(stats_service.get_streaks(db.session, lang_id))


@bp.route("/milestones/<int:lang_id>")
def milestones(lang_id):
    return jsonify(stats_service.get_reading_milestones(db.session, lang_id))


@bp.route("/heatmap/<int:lang_id>/<int:year>")
def heatmap(lang_id, year):
    return jsonify(stats_service.get_heatmap(db.session, lang_id, year))


@bp.route("/daily/<int:lang_id>/<rng>")
def daily(lang_id, rng):
    _validate_range(rng)
    return jsonify(stats_service.get_daily_reading(db.session, lang_id, rng))


@bp.route("/hourly/<int:lang_id>/<rng>")
def hourly(lang_id, rng):
    _validate_range(rng)
    return jsonify(stats_service.get_hourly_breakdown(db.session, lang_id, rng))


@bp.route("/status_distribution/<int:lang_id>")
def status_distribution(lang_id):
    return jsonify(stats_service.get_status_distribution(db.session, lang_id))


@bp.route("/new_terms/<int:lang_id>/<rng>")
def new_terms(lang_id, rng):
    _validate_range(rng)
    return jsonify(stats_service.get_new_terms_per_day(db.session, lang_id, rng))


@bp.route("/transitions/<int:lang_id>/<rng>")
def transitions(lang_id, rng):
    _validate_range(rng)
    return jsonify(stats_service.get_status_transitions(db.session, lang_id, rng))


@bp.route("/terms_by_tag/<int:lang_id>")
def terms_by_tag(lang_id):
    return jsonify(stats_service.get_terms_by_tag(db.session, lang_id))


@bp.route("/language_summary")
def language_summary():
    return jsonify(stats_service.get_language_term_summary(db.session))
