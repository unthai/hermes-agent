# Hermes `marketing` profile — portfolio social media monitor

Status: draft for Mat's approval, 2026-11-09.

## Intent

Mat runs about 19 brands that publish content and social posts through IRIS, Blotato and Herald. Nobody watches whether what was scheduled actually went out, or went out twice, or went out wrong. The 2026-10-20 incident (IRIS auto-published duplicate and ungated videos to XHEART YouTube) was found by hand, hours later.

The `marketing` profile is a single Hermes agent that watches the whole portfolio and tells Mat on Telegram when something is wrong, plus a weekly digest. It is the first step toward a portfolio digital-marketing director; v1 only observes and reports.

## Goals

- Every brand in IRIS is checked daily for publishing problems.
- Mat hears about a real problem the same day, in one Telegram line with a link.
- Mat gets one Monday digest covering every brand.

## Non-goals (v1)

- Fixing anything: no retry, pause, approve, edit, publish or reconnect. Decided by Mat 2026-11-09: alert only.
- Drafting content, strategy, calendars, ads, comment or DM replies.
- Any IRIS code change.

## Anti-goals (failure even if it works)

- The agent holds any credential that can write to IRIS, Blotato or Herald, or publish anywhere.
- Alert noise: the same problem alerted every day, or alerts on healthy days. Mat stops reading it.
- False "all good": a check that silently fails (401, timeout, empty response) reported as no problems.

## Scope: brands

All IRIS projects, currently 19 on the IRIS read tokens: doggystyle, htmmw, kado, nitehub-en, nitehub-th, revr, tour-in-france, tour-in-india, tour-in-japan, tour-in-thailand, tour-in-vietnam, tss, unth-ai, xheart, xclusive, norie, unthai-me, birds-conspiracy, good-boy-network, robot-roasts (the builder confirms the exact list from the tokens on `ce`). Shadow-mode brands are included: their checks are "nothing should have published"; anything that did is an alert.

Herald (Facebook groups) is out of v1: Herald has no read-only key, its only key can propose, and it has sent one post ever. Add it when Herald has a read-only key.

## Access (all read-only)

| Source | Credential | Where it is now |
|---|---|---|
| IRIS block API `https://iris.unth.ai/app/api/content/*`, header `x-agent-token` | `IRIS_READ_TOKEN_<BRAND>` (GET only, writes answer 403, migration 268) | `/root/.hermes/profiles/ce/.env` — copy to `marketing`. Do not mint new ones, do not rotate any token. |
| Knowledge Hub | profile's KH key, as other profiles | brand personas and rules |

Blotato publish status and metrics are read through IRIS (IRIS stores each workspace's Blotato key and harvests metrics); the agent gets no Blotato key in v1.

`IRIS_TOKEN` (XHEART write token) on `ce` is NOT copied.

## Checks (daily)

Per brand, over the last 24 h plus anything due and not yet resolved:

1. **Due, not posted:** scheduled slot passed and no publish recorded.
2. **Failed publish:** publish failed, or channel is `needs_reauth` / disconnected.
3. **Duplicate:** same story or same video published twice on one channel, or two posts with the same source story.
4. **Ungated / rule break:** a published item that skipped approval or quality gates, or contains a brand `never` rule word. Primary signal: a publish-log entry with no matching approval record. The builder must confirm this signal would have caught the 2026-10-20 XHEART publishes by checking those records; if they left no trace in the read API, report that to Mat instead of shipping a check that cannot fire.
5. **Shadow leak:** a shadow brand published anything. The builder finds where shadow status lives (project status / automation / kill-switches) in the IRIS code.
6. **Quiet brand:** a live brand overdue against its own cadence (`cadences` endpoint) by more than one slot; brands with no cadence use 7 days. A quarantined feed.
7. **Check health:** any brand whose API read failed (401, 5xx, timeout) is itself an alert ("could not check X"), never a silent pass.

Exact endpoints and fields: left to the builder, from `apps/content-engine/src/ops/agent*.ts` in `~/Code/iris/content-platform`.

## Output

- **Alerts:** one Telegram message per daily run, only if there are problems. One line per problem: brand, what, link. Dedup key: (brand, check, item id). A problem already alerted is not repeated unless it got worse (more items for the same brand and check) or has stayed open 7 days; open problems are always listed in the digest.
- **Monday digest (Bangkok morning):** per brand: posted / failed / pending approval this week, top posts by IRIS metrics, still-open problems, quiet brands.
- **Healthy day:** no message.

## Build

- New profile `/root/.hermes/profiles/marketing` on vps2, modelled on `leadhunter`: `SOUL.md`, `config.yaml`, `.env`, `cron/jobs.json`. Ownership `10000:10000`.
- Model: the standard model chain the other profiles use (primary `deepseek-v4.1-flash:1017` on ollama-cloud).
- Toolsets: minimal. No browser, no write MCPs. Read-only HTTP to IRIS, Herald, KH.
- Cron (UTC): daily run `0 2 * * *` (09:00 Bangkok); digest `30 1 * * 1` (08:30 Bangkok Monday).
- Telegram: own bot only if Mat creates one. Default (builder's call): deliver through the existing alert route (`TELEGRAM_ALERT_BOT_TOKEN` / `TELEGRAM_ALERT_CHAT_ID`) so no new bot is needed.
- Dedup state for "already alerted": a small file in the profile (builder's call).
- Back up any file before editing; restart the gateway the documented way; never stop `hermes-dashboard` / hermes.unth.ai.
- After build: one manual run, results checked against IRIS by hand; KH contribute (profile, cron ids, token location).

## Calls I made (Mat can override)

- All 19 brands from day one, shadow brands included.
- 09:00 Bangkok daily, Monday 08:30 digest; quiet = one cadence slot overdue (7 days without a cadence).
- Herald left out of v1 (no read-only key).
- Re-alert only when worse or after 7 days open.
- No message on healthy days.
- Existing alert bot instead of a new bot.
- No Blotato key; Blotato data read through IRIS.

## Left to the builder

Endpoint mapping, check implementation (prompt-only vs a small script the agent runs), dedup storage format, digest layout.
