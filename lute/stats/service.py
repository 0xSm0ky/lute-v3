"""
Calculating stats.
"""

from datetime import datetime, timedelta
from sqlalchemy import text


# ---------------------------------------------------------------------------
# Existing helpers: per-language daily read counts + cumulative chart data.
# ---------------------------------------------------------------------------


def _get_data_per_lang(session):
    "Return dict of lang name to dict[date_yyyymmdd}: count"
    ret = {}
    sql = """
    select lang, dt, sum(WrWordCount) as count
    from (
      select LgName as lang, strftime('%Y-%m-%d', WrReadDate) as dt, WrWordCount
      from wordsread
      inner join languages on LgID = WrLgID
    ) raw
    group by lang, dt
    """
    result = session.execute(text(sql)).all()
    for row in result:
        langname = row[0]
        if langname not in ret:
            ret[langname] = {}
        ret[langname][row[1]] = int(row[2])
    return ret


def _charting_data(readbydate):
    "Calc data and running total."
    dates = sorted(readbydate.keys())
    if len(dates) == 0:
        return []

    # The line graph needs somewhere to start from for a line
    # to be drawn on the first day.
    first_date = datetime.strptime(dates[0], "%Y-%m-%d")
    day_before_first = first_date - timedelta(days=1)
    dbf = day_before_first.strftime("%Y-%m-%d")
    data = [{"readdate": dbf, "wordcount": 0, "runningTotal": 0}]

    total = 0
    for d in dates:
        dcount = readbydate.get(d)
        total += dcount
        hsh = {"readdate": d, "wordcount": dcount, "runningTotal": total}
        data.append(hsh)
    return data


def get_chart_data(session):
    "Get data for chart for each language."
    raw_data = _get_data_per_lang(session)
    chartdata = {}
    for k, v in raw_data.items():
        chartdata[k] = _charting_data(v)
    return chartdata


def _readcount_by_date(readbydate):
    """
    Return data as array: [ today, week, month, year, all time ]

    This may be inefficient, but will do for now.
    """
    today = datetime.now().date()

    def _in_range(i):
        start_date = today - timedelta(days=i)
        dates = [
            start_date + timedelta(days=x) for x in range((today - start_date).days + 1)
        ]
        ret = 0
        for d in dates:
            df = d.strftime("%Y-%m-%d")
            ret += readbydate.get(df, 0)
        return ret

    return {
        "day": _in_range(0),
        "week": _in_range(6),
        "month": _in_range(29),
        "year": _in_range(364),
        "total": _in_range(3650),  # 10 year drop off :-P
    }


def get_table_data(session):
    "Wordcounts by lang in time intervals."
    raw_data = _get_data_per_lang(session)

    ret = []
    for langname, readbydate in raw_data.items():
        ret.append({"name": langname, "counts": _readcount_by_date(readbydate)})
    return ret


# ---------------------------------------------------------------------------
# New helpers: per-language daily/hourly/term aggregations for the
# Anki-inspired stats expansion.
# ---------------------------------------------------------------------------


_RANGE_DAYS = {"1m": 30, "3m": 90, "1y": 365, "all": None}


# Statuses that count as "tracked terms" — matches LuteForMobile's filter
# (skip Unknown=0 and Ignored=98).
TRACKED_STATUSES = (1, 2, 3, 4, 5, 99)


def _range_start_date(rng):
    "Return YYYY-MM-DD start date for the given range, or None for 'all'."
    days = _RANGE_DAYS.get(rng)
    if days is None:
        return None
    return (datetime.now().date() - timedelta(days=days - 1)).strftime("%Y-%m-%d")


def _today_str():
    return datetime.now().date().strftime("%Y-%m-%d")


def get_today_summary(session, lang_id):
    """
    Today's reading + best-day/best-7-day records for a single language.

    Returns dict keyed by metric name.  All values are ints.
    """
    today = _today_str()
    params = {"lg": int(lang_id), "today": today}

    # words read and pages read today
    row = session.execute(
        text(
            """
            select coalesce(sum(WrWordCount), 0) as words,
                   count(distinct WrTxID) as pages
            from wordsread
            where WrLgID = :lg
              and strftime('%Y-%m-%d', WrReadDate) = :today
            """
        ),
        params,
    ).first()
    words_today = int(row[0] or 0)
    pages_today = int(row[1] or 0)

    # seconds studied today (sum of session durations)
    seconds_today = int(
        session.execute(
            text(
                """
                select coalesce(sum(RsDurationSec), 0)
                from readingsessions
                where RsLgID = :lg
                  and strftime('%Y-%m-%d', RsEndDate) = :today
                """
            ),
            params,
        ).scalar()
        or 0
    )

    # new tracked terms added today (skip status 0 = Unknown and 98 = Ignored)
    new_terms_today = int(
        session.execute(
            text(
                """
                select count(*) from words
                where WoLgID = :lg
                  and WoStatus in (1, 2, 3, 4, 5, 99)
                  and strftime('%Y-%m-%d', WoCreated) = :today
                """
            ),
            params,
        ).scalar()
        or 0
    )

    # status changes today (from log table; empty until users start
    # changing statuses after this migration)
    status_changes_today = int(
        session.execute(
            text(
                """
                select count(*) from wordstatuslog
                where WslLgID = :lg
                  and strftime('%Y-%m-%d', WslChangedDate) = :today
                """
            ),
            params,
        ).scalar()
        or 0
    )

    # daily totals (all-time, for best-day/best-7-day records)
    daily_totals = session.execute(
        text(
            """
            select strftime('%Y-%m-%d', WrReadDate) as dt,
                   sum(WrWordCount) as cnt
            from wordsread
            where WrLgID = :lg
            group by dt
            order by dt
            """
        ),
        {"lg": int(lang_id)},
    ).all()
    best_day = max((int(r[1]) for r in daily_totals), default=0)
    best_week = _max_rolling_window(daily_totals, window_days=7)

    # days studied this month / this year (distinct read days)
    now = datetime.now().date()
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    year_start = now.replace(month=1, day=1).strftime("%Y-%m-%d")
    days_this_month = int(
        session.execute(
            text(
                """
                select count(distinct strftime('%Y-%m-%d', WrReadDate))
                from wordsread
                where WrLgID = :lg
                  and strftime('%Y-%m-%d', WrReadDate) >= :start
                """
            ),
            {"lg": int(lang_id), "start": month_start},
        ).scalar()
        or 0
    )
    days_this_year = int(
        session.execute(
            text(
                """
                select count(distinct strftime('%Y-%m-%d', WrReadDate))
                from wordsread
                where WrLgID = :lg
                  and strftime('%Y-%m-%d', WrReadDate) >= :start
                """
            ),
            {"lg": int(lang_id), "start": year_start},
        ).scalar()
        or 0
    )

    return {
        "words_today": words_today,
        "pages_today": pages_today,
        "seconds_today": seconds_today,
        "new_terms_today": new_terms_today,
        "status_changes_today": status_changes_today,
        "best_day": best_day,
        "best_week": best_week,
        "days_this_month": days_this_month,
        "days_this_year": days_this_year,
    }


def _max_rolling_window(daily_totals, window_days):
    """
    Given a list of (date_str, count) rows ordered by date_str, return the
    highest sum over any contiguous calendar window of `window_days`.
    """
    if not daily_totals:
        return 0
    # Convert to (date, count) and fill in missing days with 0 to keep
    # the window calendar-accurate (not just N consecutive rows).
    parsed = [
        (datetime.strptime(r[0], "%Y-%m-%d").date(), int(r[1]))
        for r in daily_totals
    ]
    bydate = {d: c for d, c in parsed}
    first = parsed[0][0]
    last = parsed[-1][0]
    best = 0
    cur = 0
    window = []
    d = first
    while d <= last:
        c = bydate.get(d, 0)
        window.append(c)
        cur += c
        if len(window) > window_days:
            cur -= window.pop(0)
        if cur > best:
            best = cur
        d = d + timedelta(days=1)
    return best


def get_streaks(session, lang_id):
    """
    Current streak (consecutive days ending today or yesterday with reading
    activity), longest streak ever, and a couple of context counts.
    """
    rows = session.execute(
        text(
            """
            select distinct strftime('%Y-%m-%d', WrReadDate) as dt
            from wordsread
            where WrLgID = :lg
            order by dt
            """
        ),
        {"lg": int(lang_id)},
    ).all()
    active = {datetime.strptime(r[0], "%Y-%m-%d").date() for r in rows}
    if not active:
        return {"current": 0, "longest": 0}

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    current = 0
    if today in active:
        cursor = today
    elif yesterday in active:
        cursor = yesterday
    else:
        cursor = None
    while cursor is not None and cursor in active:
        current += 1
        cursor = cursor - timedelta(days=1)

    sorted_dates = sorted(active)
    longest = 1
    run = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            run += 1
        else:
            longest = max(longest, run)
            run = 1
    longest = max(longest, run)

    return {"current": current, "longest": longest}


def get_reading_milestones(session, lang_id):
    """
    Count of days at or above 1000 / 5000 / 10000 words read.
    Pattern borrowed from LuteForMobile's ReadingMilestonesCard.
    """
    rows = session.execute(
        text(
            """
            select strftime('%Y-%m-%d', WrReadDate) as dt,
                   sum(WrWordCount) as cnt
            from wordsread
            where WrLgID = :lg
            group by dt
            """
        ),
        {"lg": int(lang_id)},
    ).all()
    totals = [int(r[1]) for r in rows]
    return {
        "days_1k": sum(1 for c in totals if c >= 1000),
        "days_5k": sum(1 for c in totals if c >= 5000),
        "days_10k": sum(1 for c in totals if c >= 10000),
    }


def get_heatmap(session, lang_id, year):
    """
    {YYYY-MM-DD: words_read} for the given calendar year and language.
    """
    rows = session.execute(
        text(
            """
            select strftime('%Y-%m-%d', WrReadDate) as dt,
                   sum(WrWordCount) as cnt
            from wordsread
            where WrLgID = :lg
              and strftime('%Y', WrReadDate) = :yr
            group by dt
            """
        ),
        {"lg": int(lang_id), "yr": str(int(year))},
    ).all()
    return {r[0]: int(r[1]) for r in rows}


def get_daily_reading(session, lang_id, rng):
    """
    [{date, words, pages}] per day in the given range.
    """
    start = _range_start_date(rng)
    sql = """
        select strftime('%Y-%m-%d', WrReadDate) as dt,
               sum(WrWordCount) as words,
               count(distinct WrTxID) as pages
        from wordsread
        where WrLgID = :lg
        """
    params = {"lg": int(lang_id)}
    if start is not None:
        sql += " and strftime('%Y-%m-%d', WrReadDate) >= :start"
        params["start"] = start
    sql += " group by dt order by dt"
    rows = session.execute(text(sql), params).all()
    return [
        {"date": r[0], "words": int(r[1] or 0), "pages": int(r[2] or 0)}
        for r in rows
    ]


def get_hourly_breakdown(session, lang_id, rng):
    """
    24-element list of summed WrWordCount bucketed by hour of day.
    """
    start = _range_start_date(rng)
    sql = """
        select strftime('%H', WrReadDate) as hr,
               sum(WrWordCount) as words
        from wordsread
        where WrLgID = :lg
        """
    params = {"lg": int(lang_id)}
    if start is not None:
        sql += " and strftime('%Y-%m-%d', WrReadDate) >= :start"
        params["start"] = start
    sql += " group by hr"
    rows = session.execute(text(sql), params).all()
    buckets = [0] * 24
    for hr, words in rows:
        if hr is None:
            continue
        idx = int(hr)
        if 0 <= idx < 24:
            buckets[idx] = int(words or 0)
    return buckets


_STATUS_LABELS = {
    "0": "Unknown",
    "1": "Learning 1",
    "2": "Learning 2",
    "3": "Learning 3",
    "4": "Learning 4",
    "5": "Learning 5",
    "98": "Ignored",
    "99": "Well Known",
}


def get_status_distribution(session, lang_id):
    """
    Term counts grouped by WoStatus for the given language.  Response
    keyed by status-id string ("1".."5","98","99") so the response shape
    matches what LuteForMobile's TermStatusChart expects.
    """
    rows = session.execute(
        text(
            """
            select WoStatus, count(*) as cnt
            from words
            where WoLgID = :lg
            group by WoStatus
            """
        ),
        {"lg": int(lang_id)},
    ).all()
    counts = {k: 0 for k in _STATUS_LABELS}
    for status, cnt in rows:
        key = str(int(status))
        if key in counts:
            counts[key] = int(cnt)
    return {
        "counts": counts,
        "labels": _STATUS_LABELS,
    }


def get_new_terms_per_day(session, lang_id, rng):
    """
    [{date, count}] per day, only counting terms that have moved past
    status 0 (Unknown) and that aren't Ignored.
    """
    start = _range_start_date(rng)
    sql = """
        select strftime('%Y-%m-%d', WoCreated) as dt,
               count(*) as cnt
        from words
        where WoLgID = :lg
          and WoStatus in (1, 2, 3, 4, 5, 99)
        """
    params = {"lg": int(lang_id)}
    if start is not None:
        sql += " and strftime('%Y-%m-%d', WoCreated) >= :start"
        params["start"] = start
    sql += " group by dt order by dt"
    rows = session.execute(text(sql), params).all()
    return [{"date": r[0], "count": int(r[1])} for r in rows]


def get_status_transitions(session, lang_id, rng):
    """
    Counts of status transitions from wordstatuslog, grouped as
    {"from->to": count}.  Anki's "Answer Buttons" equivalent for a
    reading app: how often did the user move terms between statuses?
    """
    start = _range_start_date(rng)
    sql = """
        select WslOldStatus, WslNewStatus, count(*) as cnt
        from wordstatuslog
        where WslLgID = :lg
        """
    params = {"lg": int(lang_id)}
    if start is not None:
        sql += " and strftime('%Y-%m-%d', WslChangedDate) >= :start"
        params["start"] = start
    sql += " group by WslOldStatus, WslNewStatus"
    rows = session.execute(text(sql), params).all()
    return [
        {
            "from": int(old),
            "to": int(new),
            "count": int(cnt),
        }
        for old, new, cnt in rows
    ]


def get_terms_by_tag(session, lang_id, top_n=20):
    """
    Top-N tags by term count for the given language, with a per-status
    breakdown for each tag.  Pattern adapted from termtag/datatables.py.
    """
    rows = session.execute(
        text(
            """
            select TgID, TgText, WoStatus, count(*) as cnt
            from wordtags
            inner join tags on TgID = WtTgID
            inner join words on WoID = WtWoID
            where WoLgID = :lg
            group by TgID, TgText, WoStatus
            """
        ),
        {"lg": int(lang_id)},
    ).all()

    by_tag = {}
    for tg_id, tg_text, status, cnt in rows:
        entry = by_tag.setdefault(
            int(tg_id),
            {
                "id": int(tg_id),
                "text": tg_text,
                "total": 0,
                "by_status": {k: 0 for k in _STATUS_LABELS},
            },
        )
        entry["total"] += int(cnt)
        key = str(int(status))
        if key in entry["by_status"]:
            entry["by_status"][key] += int(cnt)

    sorted_tags = sorted(by_tag.values(), key=lambda e: e["total"], reverse=True)
    return sorted_tags[: int(top_n)]


def get_language_term_summary(session):
    """
    Cross-language term breakdown.  One row per language, columns are
    total terms + counts per tracked status.
    """
    rows = session.execute(
        text(
            """
            select LgID, LgName, WoStatus, count(*) as cnt
            from words
            inner join languages on LgID = WoLgID
            group by LgID, LgName, WoStatus
            """
        )
    ).all()
    by_lang = {}
    for lg_id, lg_name, status, cnt in rows:
        entry = by_lang.setdefault(
            int(lg_id),
            {
                "id": int(lg_id),
                "name": lg_name,
                "total": 0,
                "by_status": {k: 0 for k in _STATUS_LABELS},
            },
        )
        entry["total"] += int(cnt)
        key = str(int(status))
        if key in entry["by_status"]:
            entry["by_status"][key] += int(cnt)

    return sorted(by_lang.values(), key=lambda e: e["name"].lower())
