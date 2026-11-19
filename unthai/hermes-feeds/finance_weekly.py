#!/usr/bin/env python3
"""Weekly finance digest for Hermes: Stripe, last 7 days vs the 7 days before -> /root/.hermes/feeds/finance-weekly.json.
Runs on the vps2 host, never inside Hermes. GET requests to api.stripe.com only; report only.

Config: /root/hermes-feeds/.env  STRIPE_READ_KEY_UNTHAI, STRIPE_READ_KEY_FRIENDSSTATION
(restricted keys, must start with rk_; a full secret key is refused). An account without a key is
"source missing". No key at all: one-line message, nothing written.
Totals and counts only; ids for failed payments and disputes. No names, emails or card data.
Run `--selftest` to check the maths without any network call.
"""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from decimal import Decimal

ENV = "/root/hermes-feeds/.env"
OUT = "/root/.hermes/feeds/finance-weekly.json"
ACCOUNTS = (("unthai", "STRIPE_READ_KEY_UNTHAI"), ("friendsstation", "STRIPE_READ_KEY_FRIENDSSTATION"))
# Minor-unit exponent: Stripe amounts are integers in the smallest unit. Default 2.
ZERO = {"bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga", "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf"}
THREE = {"bhd", "jod", "kwd", "omr", "tnd"}
DAY = 86400
MAX_PAGES = 200  # shortcut: stop at 20k rows per list and flag it; raise if an account outgrows it
CHARGE_TYPES = {"charge", "payment"}
REFUND_TYPES = {"refund", "payment_refund"}
FEE_ONLY_TYPES = {"stripe_fee", "network_cost", "application_fee", "billing_fee"}  # amount is the fee itself
PAYOUT_TYPES = {"payout", "payout_cancel", "payout_failure"}  # money leaving the balance, not income
OPEN_DISPUTE = {"needs_response", "under_review", "warning_needs_response", "warning_under_review"}


def exp(cur):
    return 0 if cur in ZERO else 3 if cur in THREE else 2


def major(minor, cur):
    return float(Decimal(minor).scaleb(-exp(cur)))


def new_period():
    return dict(gross=0, refunds=0, fees=0, net=0, charges=0, refund_count=0, payouts_paid=0, payouts_pending=0,
                failed_ids=[], new_subs=0, cancelled_subs=0)


def new_currency():
    return {"this_week": new_period(), "prev_week": new_period(), "open_disputes": {"count": 0, "total": 0, "ids": []}}


def paginate(get, path, params, errors):
    """Yield every item, following has_more/starting_after. A failed call is recorded, not raised."""
    params, last = dict(params, limit=100), None
    for _ in range(MAX_PAGES):
        if last:
            params["starting_after"] = last
        page = get(path, params)
        if "error" in page:
            errors.append(f"{path}: {page['error']}")
            return
        yield from page["data"]
        last = page["data"][-1]["id"] if page["data"] else None
        if not (page.get("has_more") and last):
            return
    errors.append(f"{path}: truncated at {MAX_PAGES} pages")


def digest(get, now):
    """Build one account's digest from a get(path, params) callable. Pure, so --selftest can fake Stripe."""
    errors, cur = [], {}
    bounds = {"this_week": (now - 7 * DAY, now), "prev_week": (now - 14 * DAY, now - 7 * DAY)}

    def slot(ts, c):
        for name, (lo, hi) in bounds.items():
            if lo <= ts <= hi:
                return cur.setdefault(c.upper(), new_currency())[name]

    since = {"created[gte]": now - 14 * DAY}
    for t in paginate(get, "/v1/balance_transactions", since, errors):
        p = slot(t["created"], t["currency"])
        if not p or t["type"] in PAYOUT_TYPES:
            continue
        p["net"] += t["net"]
        if t["type"] in CHARGE_TYPES:
            p["gross"] += t["amount"]; p["fees"] += t["fee"]; p["charges"] += 1
        elif t["type"] in REFUND_TYPES:
            p["refunds"] -= t["amount"]; p["fees"] += t["fee"]; p["refund_count"] += 1
        elif t["type"] in FEE_ONLY_TYPES:
            p["fees"] -= t["amount"]
        else:
            p["fees"] += t["fee"]
    for t in paginate(get, "/v1/payouts", since, errors):
        p = slot(t["created"], t["currency"])
        if p and t["status"] == "paid":
            p["payouts_paid"] += t["amount"]
        elif p and t["status"] in ("pending", "in_transit"):
            p["payouts_pending"] += t["amount"]
    for c in paginate(get, "/v1/charges", since, errors):
        p = slot(c["created"], c["currency"])
        if p and c["status"] == "failed":
            p["failed_ids"].append(c["id"])
    for s in paginate(get, "/v1/subscriptions", dict(since, status="all"), errors):
        p = slot(s["created"], s.get("currency") or "unknown")
        if p:
            p["new_subs"] += 1
    for e in paginate(get, "/v1/events", dict(since, type="customer.subscription.deleted"), errors):
        p = slot(e["created"], e["data"]["object"].get("currency") or "unknown")
        if p:
            p["cancelled_subs"] += 1
    for d in paginate(get, "/v1/disputes", {}, errors):  # not date-limited: a dispute open for a month still needs Mat
        if d["status"] in OPEN_DISPUTE:
            o = cur.setdefault(d["currency"].upper(), new_currency())["open_disputes"]
            o["count"] += 1; o["total"] += d["amount"]; o["ids"].append(d["id"])

    out = {}
    for c, v in cur.items():
        lc = c.lower()
        out[c] = {"minor_unit_exponent": exp(lc)}
        for name in ("this_week", "prev_week"):
            p = v[name]
            out[c][name] = {
                "gross_charges": major(p["gross"], lc), "charge_count": p["charges"],
                "refunds": major(p["refunds"], lc), "refund_count": p["refund_count"],
                "fees": major(p["fees"], lc), "net": major(p["net"], lc),
                "other_net": major(p["net"] - (p["gross"] - p["refunds"] - p["fees"]), lc),  # disputes, adjustments, other rows
                "payouts_paid": major(p["payouts_paid"], lc), "payouts_pending": major(p["payouts_pending"], lc),
                "failed_payments": {"count": len(p["failed_ids"]), "ids": p["failed_ids"][:50]},
                "new_subscriptions": p["new_subs"], "cancelled_subscriptions": p["cancelled_subs"]}
        o = v["open_disputes"]
        out[c]["open_disputes"] = {"count": o["count"], "total": major(o["total"], lc), "ids": o["ids"][:50]}
    return {"currencies": out, "errors": errors}


def scrub(s):
    return re.sub(r"[rs]k_\w+", "[key]", s)[:160]


def stripe_get(key):
    def get(path, params):
        url = "https://api.stripe.com" + path + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, method="GET", headers={"Authorization": "Bearer " + key, "User-Agent": "hermes-feeds/1"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read())["error"].get("message", "")
            except Exception:
                msg = ""
            return {"error": f"HTTP {e.code} " + scrub(msg)}
        except Exception as e:
            return {"error": scrub(str(e))}
    return get


def check_key(key):
    return bool(key) and key.startswith("rk_")


def load_env(path):
    try:
        lines = open(path).read().splitlines()
    except OSError:
        return {}
    return {k.strip(): v.strip().strip("'\"") for k, v in (l.split("=", 1) for l in lines if "=" in l and not l.lstrip().startswith("#"))}


def run():
    env = load_env(ENV)
    if not any(env.get(var) for _, var in ACCOUNTS):
        print(f"finance_weekly: no STRIPE_READ_KEY_* in {ENV}; nothing written")
        return 0
    now = int(time.time())
    feed = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "periods": {"this_week": [now - 7 * DAY, now], "prev_week": [now - 14 * DAY, now - 7 * DAY]},
            "note": "Amounts in major units per currency; currencies are never summed. fees and net follow Stripe balance transactions; other_net = disputes, adjustments and other rows.",
            "accounts": {}, "sources": {}}
    used = 0
    for name, var in ACCOUNTS:
        key = env.get(var)
        if not key:
            feed["sources"]["stripe_" + name] = "source missing"
        elif not check_key(key):
            feed["sources"]["stripe_" + name] = "refused: key is not a restricted rk_ key"
        else:
            feed["accounts"][name] = digest(stripe_get(key), now)
            feed["sources"]["stripe_" + name] = "partial: see errors" if feed["accounts"][name]["errors"] else "ok"
            used += 1
    # PLACEHOLDER sources, not built. When added, write the section into feed["accounts"] / feed["sources"] here.
    feed["sources"]["airbnb_booking_payouts"] = "source missing"  # TODO: rentals dashboard payouts
    feed["sources"]["hostelmate_takings"] = "source missing"      # TODO: Hostelmate takings
    if not used:
        print("finance_weekly: no usable restricted key (" + "; ".join(f"{k}: {v}" for k, v in feed["sources"].items() if k.startswith("stripe_")) + "); nothing written")
        return 1
    tmp = OUT + ".tmp"
    json.dump(feed, open(tmp, "w"), indent=1)
    os.chown(tmp, 10000, 10000); os.chmod(tmp, 0o640); os.replace(tmp, OUT)
    print(f"finance_weekly: wrote {OUT}")
    return 0


def selftest():
    now = 1_000_000_000
    bt = lambda i, ago, typ, cur, amt, fee: dict(id=f"txn_{i}", created=now - ago * DAY // 10, type=typ, currency=cur, amount=amt, fee=fee, net=amt - fee)
    data = {
        "/v1/balance_transactions": [
            bt(1, 10, "charge", "usd", 10000, 320),    # 1 day ago: this week
            bt(2, 20, "payment", "usd", 5000, 175),
            bt(3, 30, "refund", "usd", -2000, 0),
            bt(4, 30, "charge", "jpy", 5000, 180),     # zero-decimal: 5000 yen, not 50.00
            bt(5, 40, "payout", "usd", -7000, 0),      # excluded from net
            bt(6, 100, "charge", "usd", 3000, 117),    # 10 days ago: previous week
            bt(7, 140, "charge", "usd", 999, 30),      # exactly 14 days ago: still previous week
            bt(8, 200, "charge", "usd", 1, 0),         # too old, ignored
            bt(9, 20, "adjustment", "usd", -1500, 0),  # dispute debit goes to other_net
        ],
        "/v1/payouts": [dict(id="po_1", created=now - 2 * DAY, status="paid", currency="usd", amount=7000),
                        dict(id="po_2", created=now - DAY, status="in_transit", currency="usd", amount=300),
                        dict(id="po_3", created=now - DAY, status="failed", currency="usd", amount=999)],
        "/v1/charges": [dict(id="ch_f1", created=now - DAY, status="failed", currency="usd"),
                        dict(id="ch_ok", created=now - DAY, status="succeeded", currency="usd")],
        "/v1/subscriptions": [dict(id="sub_1", created=now - DAY, currency="usd"), dict(id="sub_2", created=now - 9 * DAY, currency="usd")],
        "/v1/events": [dict(id="evt_1", created=now - DAY, data=dict(object=dict(currency="jpy")))],
        "/v1/disputes": [dict(id="dp_1", status="needs_response", currency="usd", amount=1500), dict(id="dp_2", status="won", currency="usd", amount=900)],
    }
    calls = []

    def fake(path, params):  # two items per page, to exercise pagination
        calls.append((path, dict(params)))
        items, start = data[path], 0
        if "starting_after" in params:
            start = [i["id"] for i in items].index(params["starting_after"]) + 1
        return {"data": items[start:start + 2], "has_more": start + 2 < len(items)}

    r = digest(fake, now)
    assert not r["errors"], r["errors"]
    usd, jpy = r["currencies"]["USD"], r["currencies"]["JPY"]
    t, pw = usd["this_week"], usd["prev_week"]
    assert (t["gross_charges"], t["charge_count"], t["refunds"], t["refund_count"], t["fees"]) == (150.0, 2, 20.0, 1, 4.95), t
    assert t["net"] == 110.05 and t["other_net"] == -15.0, t  # payout row excluded
    assert (pw["gross_charges"], pw["charge_count"], pw["fees"]) == (39.99, 2, 1.47), pw  # both of the older charges, none of the 20-day-old one
    assert (t["payouts_paid"], t["payouts_pending"]) == (70.0, 3.0), t  # failed payout ignored
    assert t["failed_payments"] == {"count": 1, "ids": ["ch_f1"]}
    assert (t["new_subscriptions"], pw["new_subscriptions"]) == (1, 1)
    assert usd["open_disputes"] == {"count": 1, "total": 15.0, "ids": ["dp_1"]}  # won dispute not counted
    assert jpy["minor_unit_exponent"] == 0 and jpy["this_week"]["gross_charges"] == 5000.0 and jpy["this_week"]["fees"] == 180.0
    assert jpy["this_week"]["cancelled_subscriptions"] == 1 and usd["this_week"]["cancelled_subscriptions"] == 0
    bt_calls = [c for c in calls if c[0] == "/v1/balance_transactions"]
    assert len(bt_calls) == 5 and "starting_after" not in bt_calls[0][1] and bt_calls[1][1]["starting_after"] == "txn_2"  # has_more followed
    assert all(c[1]["limit"] == 100 for c in calls)
    assert major(12345, "jpy") == 12345.0 and major(12345, "usd") == 123.45 and major(1234, "kwd") == 1.234
    # a failing endpoint is recorded, the rest still builds
    bad = lambda path, params: {"error": "HTTP 403 no permission"} if path == "/v1/disputes" else fake(path, params)
    assert digest(bad, now)["errors"] == ["/v1/disputes: HTTP 403 no permission"]
    assert "rk_live" not in scrub("Invalid API Key provided: rk_live_abc123")
    assert check_key("rk_live_abc") and check_key("rk_test_abc")
    assert not check_key("sk_live_abc") and not check_key("") and not check_key(None) and not check_key("pk_live_x")
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(run())
