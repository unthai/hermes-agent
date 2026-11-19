#!/usr/bin/env python3
"""Read-only feed for Hermes: upload activity of our YouTube channels from each channel's
public Atom feed -> /root/.hermes/feeds/youtube-channels.json. No login, no key, GET only.
Views are the feed's own numbers (media:statistics), not YouTube Analytics.
Run `--selftest` for the built-in checks."""
import json, os, sys, time, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

OUT = "/root/.hermes/feeds/youtube-channels.json"
FEED = "https://www.youtube.com/feeds/videos.xml?channel_id="
# name, channel id, max days without an upload before `silent`
CHANNELS = [
    ("XHEART (@xheart_tv)", "UCE8VMTQ7kbw1kLijnzZuO5A", 4),
    ("Birds Conspiracy (@birdsconspiracy)", "UCld8GpgExt1mm6qT_J5GQyQ", 3),
]
# Known but not monitored: no id could be confirmed, or the channel does not exist yet.
UNRESOLVED = [
    "XHEART sister ambient channel (name undecided, not created)",
    "Good Boy Network @goodboynetwork (on hold, no videos)",
    "Robot Roasts @robotroastsTV (planned, no account)",
    "@xhearttv (UCBYgma0w7mHLWfLurjpMm1w) 'XHEART TV' 2022 channel with an empty feed: not the @xheart_tv channel in KH, not monitored",
]
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "m": "http://search.yahoo.com/mrss/"}


def parse(xml_bytes):
    """-> list of videos, newest first."""
    root = ET.fromstring(xml_bytes)
    vids = []
    for e in root.findall("a:entry", NS):
        title = e.findtext("a:title", "", NS)
        desc = e.findtext("m:group/m:description", "", NS) or ""
        st = e.find("m:group/m:community/m:statistics", NS)
        link = e.find("a:link", NS)
        vids.append({
            "title": title,
            "url": link.get("href") if link is not None else None,
            "published": e.findtext("a:published", "", NS),
            # no duration in the feed: the link is /shorts/<id> for Shorts (seen live); else the #shorts tag; else unknown
            "kind": "short" if "/shorts/" in (link.get("href") if link is not None else "") or "#shorts" in (title + " " + desc).lower() else "unknown",
            "views": int(st.get("views")) if st is not None and st.get("views") else None,
        })
    vids.sort(key=lambda v: v["published"], reverse=True)
    return vids


def summarize(name, cid, max_gap, vids, now):
    def age(v):
        return (now - datetime.fromisoformat(v["published"])).total_seconds() / 86400
    out = {"name": name, "id": cid, "expected_max_gap_days": max_gap,
           "uploads_7d": sum(1 for v in vids if age(v) <= 7),
           "uploads_30d": sum(1 for v in vids if age(v) <= 30),
           "last5": vids[:5]}
    if vids:
        d = age(vids[0])
        out.update(last_upload=vids[0]["published"], days_since=round(d, 1), silent=d > max_gap,
                   status="silent" if d > max_gap else "ok")
    else:
        out.update(last_upload=None, days_since=None, silent=True, status="silent (feed has no uploads)")
    out["feed_limit_note"] = "the feed lists the latest 15 uploads, so counts are capped at 15"
    return out


def fetch(cid):
    req = urllib.request.Request(FEED + cid, headers={"User-Agent": "hermes-feeds/1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def selftest():
    now = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
    sample = b"""<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
    <entry><title>Old long</title><link rel="alternate" href="https://y/1"/><published>2026-11-01T00:00:00+00:00</published>
      <media:group><media:community><media:statistics views="9"/></media:community></media:group></entry>
    <entry><title>New one #Shorts</title><link rel="alternate" href="https://y/2"/><published>2026-11-18T00:00:00+00:00</published>
      <media:group><media:description>x</media:description><media:community><media:statistics views="41"/></media:community></media:group></entry>
    <entry><title>Mid</title><link rel="alternate" href="https://y/shorts/3"/><published>2026-11-10T00:00:00+00:00</published></entry></feed>"""
    v = parse(sample)
    assert [x["url"] for x in v] == ["https://y/2", "https://y/shorts/3", "https://y/1"]
    assert v[0]["kind"] == "short" and v[1]["kind"] == "short" and v[2]["kind"] == "unknown" and v[0]["views"] == 41 and v[1]["views"] is None
    s = summarize("t", "UCx", 3, v, now)
    assert s["days_since"] == 1.5 and s["silent"] is False and s["status"] == "ok"
    assert s["uploads_7d"] == 1 and s["uploads_30d"] == 3 and len(s["last5"]) == 3
    s = summarize("t", "UCx", 1, v, now)
    assert s["silent"] is True  # 1.5 days > 1
    s = summarize("t", "UCx", 3, v[2:], now)
    assert s["days_since"] == 18.5 and s["silent"] is True and s["uploads_7d"] == 0 and s["uploads_30d"] == 1
    assert summarize("t", "UCx", 3, [], now)["silent"] is True
    print("selftest ok")


def main():
    now = datetime.now(timezone.utc)
    chans = []
    for name, cid, gap in CHANNELS:
        try:
            chans.append(summarize(name, cid, gap, parse(fetch(cid)), now))
        except urllib.error.HTTPError as e:
            chans.append({"name": name, "id": cid, "status": "fetch failed", "http_status": e.code})
        except Exception as e:
            chans.append({"name": name, "id": cid, "status": "fetch failed", "http_status": None, "error": str(e)[:200]})
    feed = {"fetched_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "public YouTube channel feeds; views are the feed's numbers, not YouTube Analytics",
            "channels": chans, "not_monitored": UNRESOLVED}
    tmp = OUT + ".tmp"
    json.dump(feed, open(tmp, "w"), indent=1)
    os.chown(tmp, 10000, 10000); os.chmod(tmp, 0o640); os.replace(tmp, OUT)
    for c in chans:
        print(c["name"], c["status"], c.get("days_since"), c.get("http_status", ""))


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
