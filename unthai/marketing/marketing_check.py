#!/usr/bin/env python3
"""Hermes `marketing` profile: read-only IRIS publishing monitor.

Spec: unthai/marketing/DESIGN.md
Run by Hermes cron as a no_agent script. Sends its own Telegram message
(alert bot) and prints nothing, so cron stays silent. Never writes to IRIS.

  marketing_check.py daily    # alerts, only when something is wrong
  marketing_check.py digest   # Monday digest, always sends
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

HOME = os.environ.get("HERMES_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_PATH = os.path.join(HOME, "state", "marketing_alerts.json")
REALERT_AFTER = timedelta(days=7)
NO_CADENCE_QUIET = timedelta(days=7)
PUBLISHED = {"success", "published"}  # publish_log uses "success"
CADENCE_PERIOD = {"daily": timedelta(days=1), "weekly": timedelta(days=7), "monthly": timedelta(days=31)}


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


# ── pure checks (tested) ─────────────────────────────────────────────────────
# Each returns a list of problems: {"key", "brand", "check", "text"}.

def check_failures(brand, failures, now, window=timedelta(days=1)):
    out = []
    for f in failures:
        at = parse_ts(f.get("failedAt"))
        if at and now - at <= window:
            out.append({"key": f"{brand}:failure:{f['id']}", "brand": brand, "check": "failure",
                        "text": f"{f.get('channel')} publish failed: {(f.get('error') or '')[:140]}"})
    return out


def check_duplicates(brand, entries):
    seen, out = {}, []
    for e in entries:
        if e.get("status") not in PUBLISHED:
            continue
        for k in filter(None, [(e.get("channel"), "brief", e.get("briefId"), e.get("language")),
                               (e.get("channel"), "url", e.get("url"))]):
            if k[2] is None:
                continue
            if k in seen and seen[k] != e["id"]:
                out.append({"key": f"{brand}:dup:{k[0]}:{k[2]}", "brand": brand, "check": "duplicate",
                            "text": f"{k[0]} published twice ({k[1]} {k[2]}) {e.get('url') or ''}".strip()})
            seen.setdefault(k, e["id"])
    return list({p["key"]: p for p in out}.values())


def check_shadow_leak(brand, status, entries, now, window=timedelta(days=1)):
    if status != "shadow":
        return []
    leaked = [e for e in entries if e.get("status") in PUBLISHED
              and (at := parse_ts(e.get("publishedAt"))) and now - at <= window]
    return [{"key": f"{brand}:shadow:{e['id']}", "brand": brand, "check": "shadow",
             "text": f"shadow brand published on {e.get('channel')}: {e.get('url') or e['id']}"} for e in leaked]


def check_quiet(brand, status, entries, cadences, now):
    if status != "active":
        return []
    periods = [CADENCE_PERIOD.get(c.get("frequency")) for c in cadences if c.get("enabled")]
    periods = [p for p in periods if p]
    # one slot overdue: no publish within two periods of the fastest cadence
    limit = 2 * min(periods) if periods else NO_CADENCE_QUIET
    last = max((parse_ts(e["publishedAt"]) for e in entries
                if e.get("status") in PUBLISHED and e.get("publishedAt")), default=None)
    if last is None or now - last > limit:
        since = f"since {last:%Y-%m-%d}" if last else "in the log"
        return [{"key": f"{brand}:quiet", "brand": brand, "check": "quiet",
                 "text": f"nothing published {since} (limit {limit.days}d)"}]
    return []


def check_quarantine(brand, kill_switches, now):
    out = []
    for k in kill_switches:
        until = parse_ts(k.get("quarantinedUntil"))
        if until and until > now:
            out.append({"key": f"{brand}:quarantine:{k['channel']}", "brand": brand, "check": "quarantine",
                        "text": f"{k['channel']} quarantined until {until:%Y-%m-%d %H:%M} UTC"})
    return out


def check_social_connection(brand, vs):
    if not vs or not vs.get("connected"):
        return []  # never connected is a setup state, not a breakage
    if vs.get("status") != "active" or vs.get("lastError"):
        return [{"key": f"{brand}:social-conn", "brand": brand, "check": "connection",
                 "text": f"Blotato connection {vs.get('status')}: {(vs.get('lastError') or '')[:120]}"}]
    return []


def select_alerts(problems, state, now):
    """Dedup: alert new problems, worse ones, or ones open REALERT_AFTER. Returns (alerts, new_state)."""
    new_state, alerts = {}, []
    counts = {}
    for p in problems:
        counts[(p["brand"], p["check"])] = counts.get((p["brand"], p["check"]), 0) + 1
    for p in problems:
        prev = state.get(p["key"])
        n = counts[(p["brand"], p["check"])]
        if prev is None or n > prev.get("n", 0) or now - parse_ts(prev["alerted"]) >= REALERT_AFTER:
            alerts.append(p)
            new_state[p["key"]] = {"alerted": now.isoformat(), "n": n, "first": (prev or {}).get("first", now.isoformat())}
        else:
            new_state[p["key"]] = prev
    return alerts, new_state  # problems gone from `problems` drop out of state


# ── IO ───────────────────────────────────────────────────────────────────────

def get(base, token, path):
    req = urllib.request.Request(f"{base.rstrip('/')}/api/content/{path}",
                                 headers={"x-agent-token": token, "accept": "application/json",
                                          "user-agent": "hermes-marketing-monitor/1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def brands_from_env(prefix):
    return {k[len(prefix):]: v for k, v in os.environ.items() if k.startswith(prefix) and v}


def load_conf(path=os.path.join(HOME, "telegram_alert.conf")):
    # KEY=VALUE lines; does not override the environment
    try:
        for line in open(path):
            k, _, v = line.strip().partition("=")
            if k and v and not k.startswith("#"):
                os.environ.setdefault(k, v)
    except OSError:
        pass


def send_telegram(text):
    load_conf()
    tok, chat = os.environ["TELEGRAM_ALERT_BOT_TOKEN"], os.environ["TELEGRAM_ALERT_CHAT_ID"]
    for i in range(0, len(text), 3900):
        data = urllib.parse.urlencode({"chat_id": chat, "text": text[i:i + 3900],
                                       "disable_web_page_preview": "true"}).encode()
        urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", data=data, timeout=30).read()


def collect(now):
    """Returns (problems, per-brand stats, unreachable brands)."""
    problems, stats, broken = [], {}, []
    prod_base = os.environ.get("IRIS_PROD_BASE")
    for brand, tok in sorted(brands_from_env("IRIS_PROD_READ_TOKEN_").items()):
        try:
            status = get(prod_base, tok, "project/settings").get("status")
            log = get(prod_base, tok, "project/publish-log?limit=200").get("entries", [])
            fails = get(prod_base, tok, "project/publish-failures").get("failures", [])
            ks = get(prod_base, tok, "project/kill-switches").get("killSwitches", [])
            cad = get(prod_base, tok, "cadences").get("cadences", [])
        except Exception as e:  # anti-goal: never a silent pass
            broken.append(f"{brand}: {type(e).__name__} {str(e)[:80]}")
            continue
        problems += check_failures(brand, fails, now) + check_duplicates(brand, log)
        problems += check_shadow_leak(brand, status, log, now) + check_quiet(brand, status, log, cad, now)
        problems += check_quarantine(brand, ks, now)
        week = [e for e in log if (t := parse_ts(e.get("publishedAt"))) and now - t <= timedelta(days=7)]
        stats[brand] = {"status": status,
                        "posted": sum(e.get("status") in PUBLISHED for e in week),
                        "failed": sum(1 for f in fails if (t := parse_ts(f.get("failedAt"))) and now - t <= timedelta(days=7))}
    stg_base = os.environ.get("IRIS_BASE")
    for brand, tok in sorted(brands_from_env("IRIS_READ_TOKEN_").items()):
        try:
            problems += check_social_connection(brand, get(stg_base, tok, "video-social"))
        except Exception as e:
            broken.append(f"{brand} (video): {type(e).__name__} {str(e)[:80]}")
    return problems, stats, broken


def fmt(p):
    return f"• {p['brand']} — {p['check']}: {p['text']}"


def main(mode, dry=False):
    load_conf(os.path.join(HOME, ".env"))  # cron loads it already; this covers manual runs
    if dry:
        globals()["send_telegram"] = print
    now = datetime.now(timezone.utc)
    try:
        state = json.load(open(STATE_PATH))
    except (OSError, ValueError):
        state = {}
    problems, stats, broken = collect(now)
    if not stats and not broken:
        broken.append("no IRIS_PROD_READ_TOKEN_* configured")
    alerts, new_state = select_alerts(problems, state, now)
    lines = []
    if mode == "daily":
        lines += [fmt(p) for p in alerts]
        lines += [f"• could not check {b}" for b in broken]
        if lines:
            send_telegram("📣 Marketing monitor\n" + "\n".join(lines))
    else:
        lines.append(f"📊 Weekly marketing digest — {now:%Y-%m-%d}")
        for b, s in sorted(stats.items()):
            lines.append(f"{b} [{s['status']}]: {s['posted']} posted, {s['failed']} failed")
        if problems:
            lines.append("\nOpen problems:")
            lines += [fmt(p) for p in problems]
        lines += [f"• could not check {b}" for b in broken]
        send_telegram("\n".join(lines))
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    if not dry:
        json.dump(new_state if mode == "daily" else state, open(STATE_PATH, "w"), indent=1)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(next((a for a in args if a in ("daily", "digest")), "daily"), dry="--dry" in args)
