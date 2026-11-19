"""Run every case on every model, one call at a time, through `hermes -p ceo chat` on vps2.

Tools: `-t todo` + `--ignore-rules`, so no MCP server (mail, xenia, ...) is loaded and SOUL/memory are not injected;
each case carries its own context. Output: raw/<case>__<model>.txt and results.jsonl (latency, tokens, events).
Rules: sequential only; on Ollama HTTP 429 wait 180 s and retry, at most 3 times; a Codex usage-limit error stops that model.
"""
import json, pathlib, subprocess, sys, time

HERE = pathlib.Path(__file__).parent
MODELS = [("deepseek-v4.1-flash:1017", "ollama-cloud"), ("gpt-5.5", "openai-codex"), ("gpt-6.1-sol", "openai-codex"),
          ("gpt-6-sol", "openai-codex"), ("gpt-6-luna", "openai-codex")]
CMD = ("docker exec -i hermes hermes -p ceo chat --query-file - --format stream-json --ignore-rules -t todo "
       "--max-turns 2 --source tool --model {m} --provider {p}")
USAGE_MARKERS = ("usage limit", "quota", "retry after", "rate limit reached", "plan limit")


def run(prompt, m, p):
    t0 = time.time()
    r = subprocess.run(["ssh", "unthai-dashboard", CMD.format(m=m, p=p)], input=prompt, capture_output=True,
                       text=True, timeout=600)
    wall = round(time.time() - t0, 1)
    events, text, result = [], [], None
    for line in (r.stdout + "\n" + r.stderr).splitlines():
        if not line.startswith("{"):
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "text":
            text.append(e.get("text", ""))
        elif e.get("type") == "result":
            result = e
        else:
            events.append({k: v for k, v in e.items() if k != "timestamp"})
    out = result.get("text") if result and result.get("text") else "".join(text)
    return dict(wall_s=wall, rc=r.returncode, result=result, events=events, text=out or "",
                stderr_tail=(r.stdout + r.stderr)[-600:] if not out else "")


def main():
    only = set(sys.argv[1:])
    done = set()
    res_path = HERE / "results.jsonl"
    if res_path.exists():
        for l in res_path.read_text().splitlines():
            d = json.loads(l)
            if d["status"] == "ok":
                done.add((d["case"], d["model"]))
    stopped = set()
    cases = sorted((HERE / "cases").glob("*.json"))
    for cf in cases:
        c = json.loads(cf.read_text())
        for m, p in MODELS:
            if (c["id"], m) in done or m in stopped or (only and m not in only):
                continue
            for attempt in range(4):
                o = run(c["prompt"], m, p)
                blob = (o["text"] + o["stderr_tail"]).lower()
                if "429" in blob and "concurrent" in blob and attempt < 3:
                    print(f"{c['id']} {m}: 429 concurrent, waiting 180 s", flush=True)
                    time.sleep(180)
                    continue
                break
            status = "ok" if o["text"].strip() else "empty"
            low = o["text"].lower()
            if p == "openai-codex" and any(k in low for k in USAGE_MARKERS) and len(o["text"]) < 600:
                status = "usage_exhausted"
                stopped.add(m)
            if "can't be reached" in low or "provider said" in low or (o["result"] and o["result"].get("exit_code")):
                status = "error" if status == "ok" else status
            init_model = next((e.get("model") for e in o["events"] if e.get("subtype") == "init"), None)
            rec = dict(case=c["id"], model=m, provider=p, status=status, wall_s=o["wall_s"],
                       duration_ms=(o["result"] or {}).get("duration_ms"), tokens=(o["result"] or {}).get("tokens"),
                       chars=len(o["text"]), words=len(o["text"].split()), init_model=init_model,
                       other_events=[e for e in o["events"] if e.get("subtype") != "init"][:5],
                       stderr_tail=o["stderr_tail"][-300:])
            (HERE / "raw" / f"{c['id']}__{m.replace(':', '_')}.txt").write_text(o["text"])
            with res_path.open("a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(c["id"], m, status, o["wall_s"], len(o["text"]), flush=True)


if __name__ == "__main__":
    main()
