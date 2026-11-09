from datetime import datetime, timedelta, timezone

import marketing_check as m

NOW = datetime(2026, 11, 10, 2, 0, tzinfo=timezone.utc)


def iso(d):
    return (NOW - d).isoformat()


def pub(i, ch="blog", brief="1", url=None, ago=timedelta(hours=1), status="success"):
    return {"id": str(i), "channel": ch, "briefId": brief, "language": "en", "url": url,
            "status": status, "publishedAt": iso(ago)}


def test_failures_only_last_24h():
    f = [{"id": "1", "channel": "blog", "error": "x", "failedAt": iso(timedelta(hours=2))},
         {"id": "2", "channel": "blog", "error": "y", "failedAt": iso(timedelta(days=3))}]
    assert [p["key"] for p in m.check_failures("TSS", f, NOW)] == ["TSS:failure:1"]


def test_duplicate_same_brief_same_channel():
    out = m.check_duplicates("XHEART", [pub(1, "youtube", "7"), pub(2, "youtube", "7"), pub(3, "blog", "7")])
    assert len(out) == 1 and out[0]["check"] == "duplicate"


def test_duplicate_ignores_skipped():
    assert m.check_duplicates("X", [pub(1), pub(2, status="skipped")]) == []


def test_shadow_leak():
    assert len(m.check_shadow_leak("NORIE", "shadow", [pub(1)], NOW)) == 1
    assert m.check_shadow_leak("NORIE", "active", [pub(1)], NOW) == []


def test_quiet_uses_cadence():
    daily = [{"enabled": True, "frequency": "daily"}]
    assert m.check_quiet("A", "active", [pub(1, ago=timedelta(days=3))], daily, NOW)
    assert not m.check_quiet("A", "active", [pub(1, ago=timedelta(days=1))], daily, NOW)
    weekly = [{"enabled": True, "frequency": "weekly"}]
    assert not m.check_quiet("A", "active", [pub(1, ago=timedelta(days=10))], weekly, NOW)


def test_quiet_no_cadence_seven_days_and_skips_shadow():
    assert m.check_quiet("A", "active", [pub(1, ago=timedelta(days=8))], [], NOW)
    assert not m.check_quiet("A", "shadow", [], [], NOW)


def test_quarantine():
    ks = [{"channel": "blog", "quarantinedUntil": (NOW + timedelta(hours=5)).isoformat()},
          {"channel": "x", "quarantinedUntil": None}]
    assert [p["key"] for p in m.check_quarantine("B", ks, NOW)] == ["B:quarantine:blog"]


def test_social_connection():
    assert m.check_social_connection("X", {"connected": True, "status": "needs_reauth", "lastError": "401"})
    assert not m.check_social_connection("X", {"connected": True, "status": "active", "lastError": None})
    assert not m.check_social_connection("X", {"connected": False})


def test_dedup_new_same_worse_stale():
    p = {"key": "A:quiet", "brand": "A", "check": "quiet", "text": "t"}
    alerts, st = m.select_alerts([p], {}, NOW)
    assert alerts == [p]
    alerts, st2 = m.select_alerts([p], st, NOW + timedelta(days=1))
    assert alerts == []
    q = {**p, "key": "A:quiet2"}
    alerts, _ = m.select_alerts([p, q], st2, NOW + timedelta(days=1))
    assert len(alerts) == 2  # worse: count for (A, quiet) went up
    alerts, _ = m.select_alerts([p], st2, NOW + timedelta(days=8))
    assert alerts == [p]  # open 7+ days
    _, st3 = m.select_alerts([], st2, NOW)
    assert st3 == {}  # resolved problems drop out
