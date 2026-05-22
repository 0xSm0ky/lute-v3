"Tests for the Anki-inspired stats helpers added in 20260522."

from datetime import datetime, timedelta

from lute.db import db
from lute.models.book import WordsRead, ReadingSession
from lute.models.term import Term, Status, TermTag
from lute.stats import service as svc
from tests.utils import make_text


def _add_read(lang, content, readdate, start_offset_min=None):
    "Save a one-page book and an associated WordsRead/ReadingSession row."
    t = make_text(content, content, lang)
    if start_offset_min is not None:
        t.start_date = readdate - timedelta(minutes=start_offset_min)
    db.session.add(t)
    db.session.commit()
    if readdate is None:
        return t
    db.session.add(WordsRead(t, readdate, t.word_count))
    if start_offset_min is not None:
        db.session.add(ReadingSession(t, t.start_date, readdate, t.word_count))
    db.session.commit()
    return t


def _add_term(lang, text_value, status=Status.WELLKNOWN, created=None, tags=None):
    "Create a saved Term, optionally backdating WoCreated and adding tags."
    t = Term(lang, text_value)
    t.status = status
    if tags:
        for tag_text in tags:
            existing = db.session.query(TermTag).filter(TermTag.text == tag_text).first()
            t.term_tags.append(existing or TermTag(tag_text))
    db.session.add(t)
    db.session.commit()
    if created is not None:
        db.session.execute(
            db.text("update words set WoCreated = :c where WoID = :i"),
            {"c": created.strftime("%Y-%m-%d %H:%M:%S"), "i": t.id},
        )
        db.session.commit()
    return t


def test_today_summary_counts_reading_and_session_time(spanish, app_context):
    "Today summary includes pages, words, session seconds, new terms."
    now = datetime.now().replace(microsecond=0)
    _add_read(spanish, "uno dos tres.", now, start_offset_min=5)
    _add_term(spanish, "uno", status=Status.WELLKNOWN, created=now)
    _add_term(spanish, "dos", status=Status.UNKNOWN, created=now)  # filtered out

    summary = svc.get_today_summary(db.session, spanish.id)
    assert summary["words_today"] == 3
    assert summary["pages_today"] == 1
    assert summary["seconds_today"] == 300
    assert summary["new_terms_today"] == 1
    assert summary["best_day"] == 3
    assert summary["best_week"] == 3


def test_get_streaks_includes_today_and_yesterday(spanish, app_context):
    "Two consecutive days ending today => current streak 2."
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    _add_read(spanish, "uno.", today)
    _add_read(spanish, "dos.", yesterday)
    streaks = svc.get_streaks(db.session, spanish.id)
    assert streaks["current"] == 2
    assert streaks["longest"] >= 2


def test_get_streaks_empty(spanish, app_context):
    assert svc.get_streaks(db.session, spanish.id) == {"current": 0, "longest": 0}


def test_get_reading_milestones(spanish, app_context):
    "Days at or above 1k / 5k / 10k words."
    now = datetime.now()
    # 12000-word day via a single big text
    big = " ".join(["palabra"] * 12000)
    _add_read(spanish, big, now)
    # 2000-word day, one week ago
    medium = " ".join(["palabra"] * 2000)
    _add_read(spanish, medium, now - timedelta(days=7))
    m = svc.get_reading_milestones(db.session, spanish.id)
    assert m == {"days_1k": 2, "days_5k": 1, "days_10k": 1}


def test_get_heatmap_keyed_by_iso_date(spanish, app_context):
    now = datetime.now()
    _add_read(spanish, "uno dos.", now)
    year = now.year
    hm = svc.get_heatmap(db.session, spanish.id, year)
    assert hm.get(now.strftime("%Y-%m-%d")) == 2


def test_get_daily_reading_range_filter(spanish, app_context):
    today = datetime.now()
    _add_read(spanish, "uno dos tres.", today)
    _add_read(spanish, "cuatro cinco.", today - timedelta(days=400))
    one_year = svc.get_daily_reading(db.session, spanish.id, "1y")
    assert len(one_year) == 1
    assert one_year[0]["words"] == 3
    all_time = svc.get_daily_reading(db.session, spanish.id, "all")
    assert len(all_time) == 2


def test_get_hourly_breakdown_buckets_24(spanish, app_context):
    now = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    _add_read(spanish, "uno dos.", now)
    buckets = svc.get_hourly_breakdown(db.session, spanish.id, "all")
    assert len(buckets) == 24
    assert buckets[9] == 2


def test_get_status_distribution_keys_all_status_ids(spanish, app_context):
    _add_term(spanish, "uno", status=Status.WELLKNOWN)
    _add_term(spanish, "dos", status=3)
    dist = svc.get_status_distribution(db.session, spanish.id)
    assert dist["counts"]["99"] == 1
    assert dist["counts"]["3"] == 1
    for k in ("0", "1", "2", "4", "5", "98"):
        assert dist["counts"][k] == 0
    assert "labels" in dist and dist["labels"]["99"] == "Well Known"


def test_get_new_terms_per_day_skips_unknown_and_ignored(spanish, app_context):
    "Only statuses 1..5 and 99 count as 'new terms added'."
    today = datetime.now()
    _add_term(spanish, "uno", status=Status.WELLKNOWN, created=today)
    _add_term(spanish, "dos", status=Status.IGNORED, created=today)
    _add_term(spanish, "tres", status=Status.UNKNOWN, created=today)
    _add_term(spanish, "cuatro", status=3, created=today)
    rows = svc.get_new_terms_per_day(db.session, spanish.id, "all")
    assert rows == [{"date": today.strftime("%Y-%m-%d"), "count": 2}]


def test_get_status_transitions_via_trigger(spanish, app_context):
    "Updating WoStatus should populate wordstatuslog via the trigger."
    t = _add_term(spanish, "uno", status=Status.UNKNOWN)
    t.status = Status.WELLKNOWN
    db.session.add(t)
    db.session.commit()
    rows = svc.get_status_transitions(db.session, spanish.id, "all")
    assert any(r["from"] == 0 and r["to"] == 99 and r["count"] >= 1 for r in rows)


def test_get_terms_by_tag_groups_per_status(spanish, app_context):
    _add_term(spanish, "uno", status=Status.WELLKNOWN, tags=["food"])
    _add_term(spanish, "dos", status=3, tags=["food"])
    _add_term(spanish, "tres", status=Status.WELLKNOWN, tags=["verb"])
    by_tag = svc.get_terms_by_tag(db.session, spanish.id)
    food = next(t for t in by_tag if t["text"] == "food")
    assert food["total"] == 2
    assert food["by_status"]["99"] == 1
    assert food["by_status"]["3"] == 1


def test_get_language_term_summary(spanish, english, app_context):
    _add_term(spanish, "uno", status=Status.WELLKNOWN)
    _add_term(english, "one", status=3)
    summary = svc.get_language_term_summary(db.session)
    by_name = {row["name"]: row for row in summary}
    assert by_name["Spanish"]["total"] == 1
    assert by_name["Spanish"]["by_status"]["99"] == 1
    assert by_name["English"]["total"] == 1
    assert by_name["English"]["by_status"]["3"] == 1
