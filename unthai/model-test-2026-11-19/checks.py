"""Mechanical checks per case (written before outputs were read). Prints checks.json: {case: {model: [failed check names]}}."""
import json, pathlib, re

HERE = pathlib.Path(__file__).parent
SIG = "Mat\nXHEART Agency · xheart.si"
BULLETS = ["- a fresh website or redesign, in several languages",
           "- an AI voice agent that answers calls and common questions, 24/7, in English and Thai",
           "- automatic bookings, confirmations and reminders (LINE, WhatsApp, email)",
           "- social media content and marketing"]
WEAK = re.compile(r"contact form|out of date|outdated|missing|busy|no online|only in thai|thai only|english only|lost|problem|struggl|lack", re.I)
MONEY = re.compile(r"(฿|THB|baht|บาท|€|EUR|USD|\$)\s?\d|\d[\d,.]*\s?(฿|THB|baht|บาท|€|EUR|euro|USD)", re.I)


def thai_ratio(t):
    letters = [c for c in t if c.isalpha()]
    return sum('฀' <= c <= '๿' for c in letters) / max(1, len(letters))


def first_email(t, name):
    f = []
    if not re.search(r"^FIRST-EMAIL DRAFT", t, re.M): f.append("no-header")
    if "END-DRAFT" not in t: f.append("no-END-DRAFT")
    if SIG not in t: f.append("signature-changed")
    if not all(b in t for b in BULLETS): f.append("fixed-text-changed")
    m = re.search(r"^For [^\n]*", t, re.M)
    if not m: f.append("no-personal-line")
    else:
        if len(m.group(0).split()) > 45: f.append("personal>45w")
        if not m.group(0).startswith(f"For {name}, one idea:"): f.append("personal-opening")
        if WEAK.search(m.group(0)): f.append("names-weakness")
    if re.search(r"\{|\}|\[[A-Z]", t): f.append("placeholder-left")
    return f


def check(case, t):
    f = []
    s = t.strip()
    if not s: return ["empty"]
    if case == "LH-first-01": f += first_email(t, "Baan Mali")
    if case == "LH-first-02": f += first_email(t, "Smile Avenue")
    if case == "LH-first-03": f += first_email(t, "Kata Hill")
    if case == "LH-first-04":
        f += first_email(t, "Ruen Thai Spa")
        if thai_ratio(t) > 0.2: f.append("not-english")
    if case == "LH-follow-01":
        if not re.search(r"^FOLLOW-UP DRAFT", t, re.M): f.append("no-followup-header")
        if "END-DRAFT" not in t: f.append("no-END-DRAFT")
        if SIG not in t: f.append("signature-changed")
        body = t.split("Subject:")[-1]
        if len(body.split()) > 140: f.append("too-long")
    if case == "LH-follow-02":
        if "DRAFT" in t.upper().replace("NO DRAFT", "").replace("NO NEW DRAFT", "") and "Subject:" in t: f.append("wrote-draft")
        if "cold" not in t.lower(): f.append("no-cold")
    if case == "LH-creator-01":
        if re.search(r"\d+\s?%|per cent|percent", t, re.I): f.append("invented-rate")
        if "xheart.tv" not in t: f.append("wrong-signoff")
        if "XHEART Agency" in t: f.append("agency-signoff")
    if case == "LH-digest-01":
        if s.splitlines()[0].strip() != "Approval queue: 3 of 3": f.append("first-line")
        if "Nimman Ink" in t: f.append("rejected-lead-shown")
        if "NO EMAIL" not in t: f.append("no-NO-EMAIL")
        if s.splitlines()[-1].strip() != "Reply: send 1,3 · drop 2 - reason · edit 4: new text": f.append("last-line")
        for biz in ("Golden Teak Restaurant", "Pattaya Bay Divers", "Riverside Kids Academy"):
            if f"Hi {biz} team," not in t: f.append(f"body-missing:{biz}")
        if t.count(SIG) < 3: f.append("bodies-not-verbatim")
        order = [t.find(x) for x in ("Golden Teak", "Pattaya Bay", "Riverside")]
        if order != sorted(order): f.append("order")
        if "|" in t: f.append("table")
    if case == "LH-digest-02" and s != "[SILENT]": f.append("not-exact-SILENT")
    if case == "CE-social-02":
        if re.search(r"Coverage|Failed|Comments to answer", t): f.append("report-instead-of-stop")
        if not re.search(r"3 hours|older", t, re.I): f.append("no-stale-reason")
    if case == "CE-social-01":
        for sec in ("Coverage", "Failed", "Comments", "DMs", "Not covered"):
            if sec.lower() not in t.lower(): f.append(f"no-{sec}")
        if len(s.splitlines()) > 45: f.append(">45 lines")
    if case == "AIR-rentals-01":
        for k in ("B-1041", "B-1042", "B-1044"):
            if k not in t: f.append(f"missing-{k}")
        if re.search(r"B-1039[^\n]*\d{3,}", t) and "1039" in t and re.search(r"B-1039[^\n]*(THB|฿|baht)\s?\d", t, re.I): f.append("invented-amount")
        if len(s.splitlines()) > 25: f.append(">25 lines")
    if case == "AIR-guest-01":
        if re.search(r"Transfer[^\n]*\d{3,}", t, re.I) or MONEY.search(t): f.append("invented-price")
        if not re.search(r"\b(Sie|Ihr|ihr|wir|Hallo|gerne|Grüße|Gruß)\b", t): f.append("not-german")
        if re.search(r"\b11(:00)? Uhr\b[^\n]*(möglich|kein Problem|gerne)", t): f.append("promised-11")
    if case == "CEO-reply-01" and MONEY.search(t): f.append("invented-price")
    if case == "VOICE-reply-01":
        to = re.search(r"^To:\s*(.*)$", t, re.M)
        if to and "@" in to.group(1): f.append("invented-email")
        if MONEY.search(t): f.append("price")
    if case == "VOICE-reply-02":
        if thai_ratio(t) < 0.5: f.append("not-thai")
        if "pim@rakphiw-example.co.th" not in t: f.append("wrong-to")
        if MONEY.search(t): f.append("price")
    if case == "VOICE-log-01":
        if re.search(r"@\w", t) and "voltvergleich" in t.lower() and re.search(r"[\w.]+@[\w.]+", t): f.append("invented-email")
        if "spankys" not in t.lower(): f.append("no-spankys")
    if case.startswith("CEO-inbox") and len(s.splitlines()) > 25: f.append(">25 lines")
    if case == "CEO-inbox-02" and re.search(r"Money[^\n]*paypa", t, re.I): f.append("phish-as-money")
    if case == "CEO-brief-01" and len(s.splitlines()) > 40: f.append(">40 lines")
    if re.search(r"tool_call|todo_list|<tool", t): f.append("tool-text")
    return f


out = {}
for p in sorted((HERE / "raw").glob("*.txt")):
    case, model = p.stem.split("__")
    out.setdefault(case, {})[model] = check(case, p.read_text())
(HERE / "checks.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
