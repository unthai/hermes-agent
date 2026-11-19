#!/usr/bin/env python3
"""Send approved outreach drafts through XENIA. Runs on the vps2 host, never inside Hermes.

Mat approves a draft in Telegram; the leadhunter agent tags the lead `approved-to-send`.
This script sends exactly the draft stored in the lead notes with the XENIA action
`outreach.sendDraft`, which itself refuses unapproved, suppressed or duplicate sends and
enforces a daily cap. No LLM is involved, so an approved text cannot be rewritten.

Dry run by default: prints what it would send. Pass --send to send.
Config: /root/hermes-feeds/.env  XENIA_SEND_KEY (scopes outreach:send + leads:read),
        optional XENIA_API_URL, SENDER_MAX_PER_RUN (default 5).
"""
import argparse, hashlib, json, os, re, sys, time, urllib.error, urllib.request

REPORT = "/root/.hermes/feeds/outreach-sent.json"
HEADER = re.compile(r"^(FIRST-EMAIL|FOLLOW-UP) DRAFT\b.*$", re.M)
# A line that starts one of these ends the draft body. Anything else after the header is body.
TERMINATOR = re.compile(r"^(END-DRAFT|RESEARCH\b|RECORD NOTE\b|REJECTED\b|TAGS?:|tags?:|(FIRST-EMAIL|FOLLOW-UP) DRAFT\b)", re.M)
# Leftover template or agent text: never send a body that contains one of these.
SUSPECT = re.compile(r"\{\{|\}\}|\[[A-Z][A-Za-z _-]{2,}\]|NOT sent|status:|lead id|draft-ready|approved-to-send", re.I)
STOP_CODES = {"DAILY_CAP_REACHED", "WORKSPACE_SEND_LIMIT", "SENDING_DISABLED"}


def parse_draft(notes):
    """Return (subject, body) from the LAST draft block in the notes, or (None, reason)."""
    heads = list(HEADER.finditer(notes or ""))
    if not heads:
        return None, "no draft header"
    rest = notes[heads[-1].end():].lstrip("\n")
    first, _, tail = rest.partition("\n")
    if not first.startswith("Subject:"):
        return None, "no Subject line under the header"
    subject = first[len("Subject:"):].strip()
    end = TERMINATOR.search(tail)
    body = (tail[:end.start()] if end else tail).strip()
    if not subject or len(subject) > 150:
        return None, "subject empty or over 150 chars"
    if not 80 <= len(body) <= 5000:
        return None, f"body length {len(body)} outside 80-5000"
    hit = SUSPECT.search(subject + "\n" + body)
    if hit:
        return None, f"suspect text in draft: {hit.group(0)!r}"
    return subject, body


def selftest():
    ok = "x\nFIRST-EMAIL DRAFT (status: draft-ready, NOT sent)\nSubject: AI for Acme?\n\nHi Acme team,\n\n" + "word " * 30 + "\n\nMat\n"
    assert parse_draft(ok)[0] == "AI for Acme?" and parse_draft(ok)[1].endswith("Mat")
    assert parse_draft(ok + "END-DRAFT\njunk after")[1].endswith("Mat")
    assert parse_draft(ok + "RESEARCH 2026-11-19\n- note")[1].endswith("Mat")
    assert parse_draft("no draft here")[0] is None
    assert parse_draft("FIRST-EMAIL DRAFT\nHi there")[0] is None  # no Subject line
    assert parse_draft(ok.replace("Hi Acme team", "Hi {{name}}"))[0] is None  # template leftover
    assert parse_draft(ok.replace("Hi Acme team", "Hi [Company Name]"))[0] is None
    # an edited draft appended later wins over the first one
    two = ok + "FOLLOW-UP DRAFT\nSubject: Second\n\n" + "later " * 30
    assert parse_draft(two)[0] == "Second"
    print("selftest ok")


def load_env(path):
    return {k: v.strip().strip("'\"") for k, v in (l.strip().split("=", 1) for l in open(path) if "=" in l and not l.startswith("#"))}


def call(base, key, action, params):
    req = urllib.request.Request(
        base + "/api/hermes/execute", data=json.dumps({"action": action, "params": params}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "User-Agent": "hermes-outreach-sender/1"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        raw = e.read()[:2000].decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"error": raw[:200]}
    except Exception as e:  # network error, timeout
        return 0, {"error": str(e)[:200]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--send", action="store_true", help="really send (default: dry run)")
    ap.add_argument("--tag", default="approved-to-send", help="tag to read; only approved-to-send can be sent")
    ap.add_argument("--env-file", default="/root/hermes-feeds/.env")
    ap.add_argument("--key-name", default="XENIA_SEND_KEY")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.send and a.tag != "approved-to-send":
        sys.exit("refusing: --send works only on the tag approved-to-send")
    env = load_env(a.env_file)
    key = env.get(a.key_name)
    if not key:
        sys.exit(f"no {a.key_name} in {a.env_file}: nothing to do")
    base = env.get("XENIA_API_URL", env.get("CRM_API_URL", "https://crm.unth.ai")).rstrip("/")
    cap = int(env.get("SENDER_MAX_PER_RUN", "5"))

    status, res = call(base, key, "leads.list", {"tag": a.tag, "limit": 200})
    if status != 200:
        sys.exit(f"leads.list failed: HTTP {status} {res.get('error')}")
    leads = res.get("data", {}).get("leads", [])
    results, sent = [], 0
    for lead in leads:
        row = {"leadId": lead["id"], "company": lead.get("companyName"), "to": lead.get("email"), "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        subject, body = parse_draft(lead.get("notes"))
        if not lead.get("email"):
            row["result"] = "skipped: no email"
        elif subject is None:
            row["result"] = "skipped: " + body
        elif not a.send:
            row.update(result="dry run: would send", subject=subject, chars=len(body), first=body.splitlines()[0][:80], last=body.splitlines()[-1][:80])
        elif sent >= cap:
            row["result"] = f"left for next run: per-run cap {cap}"
        else:
            idem = hashlib.sha256(f"{lead['id']}|{subject}|{body}".encode()).hexdigest()[:40]
            status, res = call(base, key, "outreach.sendDraft", {"leadId": lead["id"], "subject": subject, "body": body, "idempotencyKey": idem})
            code = res.get("code") or ("OK" if status == 200 else f"HTTP {status}")
            row.update(result=code, subject=subject, detail=(res.get("data") or {}).get("status") or res.get("error"))
            if status == 200:
                sent += 1
            elif code in STOP_CODES or status in (0, 502, 503, 504):
                results.append(row)
                print(f"stopping run: {code} {res.get('error')}")
                break
        results.append(row)

    for r in results:
        print(json.dumps(r, ensure_ascii=False))
    kinds = {}
    for r in results:
        k = r["result"].split(":")[0]
        kinds[k] = kinds.get(k, 0) + 1
    print(f"{'SEND' if a.send else 'DRY RUN'} tag={a.tag} leads={len(leads)} {kinds}")
    if a.send and results:  # keep the last 200 results for the morning brief
        old = json.load(open(REPORT)) if os.path.exists(REPORT) else []
        tmp = REPORT + ".tmp"
        json.dump((old + results)[-200:], open(tmp, "w"), ensure_ascii=False)
        os.chown(tmp, 10000, 10000); os.chmod(tmp, 0o640); os.replace(tmp, REPORT)


if __name__ == "__main__":
    main()
