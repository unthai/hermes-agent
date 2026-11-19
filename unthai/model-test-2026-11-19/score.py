"""Map blind scores (scores_blind.json) to models via blind_key.json; write score_table.md."""
import json,statistics as st,collections
b=json.load(open('scores_blind.json'));k=json.load(open('blind_key.json'))
R=[json.loads(l) for l in open('results.jsonl')]
M=["deepseek-v4.1-flash:1017","gpt-5.5","gpt-6.1-sol","gpt-6-sol","gpt-6-luna"]
per=collections.defaultdict(dict)
for c,labs in b.items():
    for lab,s in labs.items(): per[k[c][lab]][c]=s
cases=sorted(b)
rows=["| Case | "+" | ".join(M)+" |","|---|"+"---|"*len(M)]
for c in cases: rows.append(f"| {c} | "+" | ".join(str(sum(per[m][c])) for m in M)+" |")
tot={m:sum(sum(v) for v in per[m].values()) for m in M}
rows.append("| **Total /200** | "+" | ".join(f"**{tot[m]}**" for m in M)+" |")
for i,cn in enumerate(["F format","N no invented fact","D right decision","H reads human","L language"]):
    rows.append(f"| {cn} /40 | "+" | ".join(str(sum(v[i] for v in per[m].values())) for m in M)+" |")
rows.append("| cases with N=0 (invented fact) | "+" | ".join(str(sum(1 for v in per[m].values() if v[1]==0)) for m in M)+" |")
rows.append("| cases with D=0 (wrong decision) | "+" | ".join(str(sum(1 for v in per[m].values() if v[2]==0)) for m in M)+" |")
def col(f): return " | ".join(str(f([r for r in R if r['model']==m])) for m in M)
rows.append("| median latency s | "+col(lambda rs: st.median(r['wall_s'] for r in rs))+" |")
rows.append("| max latency s | "+col(lambda rs: max(r['wall_s'] for r in rs))+" |")
rows.append("| median words | "+col(lambda rs: st.median(r['words'] for r in rs))+" |")
rows.append("| output tokens, 20 cases | "+col(lambda rs: sum((r['tokens'] or {}).get('output',0) for r in rs))+" |")
rows.append("| failed calls | "+col(lambda rs: sum(r['status']!='ok' for r in rs))+" |")
G={"outreach drafts: LH-first x4, LH-follow x2, LH-creator":[c for c in cases if c.startswith(("LH-first","LH-follow","LH-creator"))],
   "approval digest x2":[c for c in cases if c.startswith("LH-digest")],
   "inbox triage x2 + reply draft":[c for c in cases if c.startswith("CEO-inbox") or c=="CEO-reply-01"],
   "social daily x2":[c for c in cases if c.startswith("CE-social")],
   "rentals report + guest reply":[c for c in cases if c.startswith("AIR")],
   "voice log + 2 reply drafts":[c for c in cases if c.startswith("VOICE")],
   "morning brief":["CEO-brief-01"]}
rows += ["","| Job group (max) | "+" | ".join(M)+" |","|---|"+"---|"*len(M)]
for g,cs in G.items(): rows.append(f"| {g} ({10*len(cs)}) | "+" | ".join(str(sum(sum(per[m][c]) for c in cs)) for m in M)+" |")
open('score_table.md','w').write("# Score table, 2026-11-19\n\nBlind scores (rubric.md), mapped back through blind_key.json after all 20 cases were scored. Raw criteria per label: scores_blind.json; per model: scores_by_model.json. Mechanical checks: checks.json.\n\n"+"\n".join(rows)+"\n")
json.dump({m:per[m] for m in M},open('scores_by_model.json','w'),indent=1)
print("\n".join(rows))
