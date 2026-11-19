# Score table, 2026-11-19

Blind scores (rubric.md), mapped back through blind_key.json after all 20 cases were scored. Raw criteria per label: scores_blind.json; per model: scores_by_model.json. Mechanical checks: checks.json.

| Case | deepseek-v4.1-flash:1017 | gpt-5.5 | gpt-6.1-sol | gpt-6-sol | gpt-6-luna |
|---|---|---|---|---|---|
| AIR-guest-01 | 9 | 10 | 8 | 7 | 9 |
| AIR-rentals-01 | 10 | 5 | 5 | 5 | 6 |
| CE-social-01 | 10 | 9 | 6 | 6 | 8 |
| CE-social-02 | 10 | 10 | 10 | 10 | 10 |
| CEO-brief-01 | 8 | 3 | 7 | 6 | 7 |
| CEO-inbox-01 | 10 | 9 | 6 | 7 | 7 |
| CEO-inbox-02 | 10 | 7 | 10 | 9 | 9 |
| CEO-reply-01 | 10 | 9 | 9 | 10 | 10 |
| LH-creator-01 | 10 | 6 | 6 | 4 | 7 |
| LH-digest-01 | 10 | 7 | 10 | 8 | 9 |
| LH-digest-02 | 10 | 10 | 10 | 10 | 10 |
| LH-first-01 | 10 | 9 | 7 | 8 | 7 |
| LH-first-02 | 10 | 4 | 8 | 5 | 7 |
| LH-first-03 | 10 | 9 | 7 | 7 | 10 |
| LH-first-04 | 10 | 8 | 8 | 7 | 9 |
| LH-follow-01 | 8 | 4 | 9 | 8 | 8 |
| LH-follow-02 | 9 | 9 | 10 | 10 | 10 |
| VOICE-log-01 | 9 | 6 | 8 | 6 | 9 |
| VOICE-reply-01 | 10 | 8 | 4 | 8 | 8 |
| VOICE-reply-02 | 10 | 7 | 7 | 7 | 7 |
| **Total /200** | **193** | **149** | **155** | **148** | **167** |
| F format /40 | 37 | 26 | 35 | 29 | 35 |
| N no invented fact /40 | 38 | 31 | 30 | 28 | 35 |
| D right decision /40 | 38 | 30 | 27 | 29 | 31 |
| H reads human /40 | 40 | 24 | 25 | 26 | 28 |
| L language /40 | 40 | 38 | 38 | 36 | 38 |
| cases with N=0 (invented fact) | 0 | 3 | 4 | 3 | 0 |
| cases with D=0 (wrong decision) | 0 | 3 | 3 | 2 | 3 |
| median latency s | 13.3 | 13.350000000000001 | 15.149999999999999 | 12.45 | 15.95 |
| max latency s | 19.2 | 85.7 | 63.8 | 67.3 | 65.7 |
| median words | 139.5 | 101.5 | 79.5 | 84.0 | 82.5 |
| output tokens, 20 cases | 18788 | 17756 | 19470 | 16389 | 23175 |
| failed calls | 0 | 0 | 0 | 0 | 0 |

| Job group (max) | deepseek-v4.1-flash:1017 | gpt-5.5 | gpt-6.1-sol | gpt-6-sol | gpt-6-luna |
|---|---|---|---|---|---|
| outreach drafts: LH-first x4, LH-follow x2, LH-creator (70) | 67 | 49 | 55 | 49 | 58 |
| approval digest x2 (20) | 20 | 17 | 20 | 18 | 19 |
| inbox triage x2 + reply draft (30) | 30 | 25 | 25 | 26 | 26 |
| social daily x2 (20) | 20 | 19 | 16 | 16 | 18 |
| rentals report + guest reply (20) | 19 | 15 | 13 | 12 | 15 |
| voice log + 2 reply drafts (30) | 29 | 21 | 19 | 21 | 24 |
| morning brief (10) | 8 | 3 | 7 | 6 | 7 |

## Notes on the run

- Each case was run once per model, 100 calls, one at a time, between 12:50 and 13:30 UTC on 2026-11-19, through `hermes -p ceo chat --query-file - --format stream-json --ignore-rules -t todo --max-turns 2`. `-t todo` keeps every MCP server (mail, xenia) off, so nothing could be sent. No 429, no Codex usage error, no failed call.
- The `ceo` config still injects its `environment_hint` ("SMART ROUTING RULES", delegate to freellm) and `reasoning_effort: medium` into every run, for every model. That is what cron jobs get too.
- LH-digest-02: every model returned the silence marker; the interactive CLI replaced it with a warning line, so the exact `[SILENT]` string could not be checked. Scored as correct for all.
- One sample per case: a difference of 1-2 points in one case is noise. The totals and the repeated failure types are the signal.

## Recommendation per job (no job changed)

DeepSeek flash won 193/200 and had no invented fact and no wrong decision. Every GPT model failed at least one trap: missed the double booking (all four), answered a Thai caller in English (all four), named a weakness in a cold email (3 of 4), invented an email address or a dentist's name. Among the GPT models `gpt-6-luna` scored best (167), `gpt-5.5` lowest with `gpt-6-sol` (149, 148).

Keep every text job on the profile default (DeepSeek, unpinned, with the fallback chain). Pinning a job to Codex would also remove its fallback chain (cron/scheduler.py 96-111, 1775-1780, 2463-2466 on the host).
Replace the `gpt-5.5` fallback with `gpt-6-luna` in the profile chains (set-model-chain.py), per Mat's GPT-6 preference; that is a config change, not a cron edit.
