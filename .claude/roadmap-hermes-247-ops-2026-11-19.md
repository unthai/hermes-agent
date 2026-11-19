# HERMES 24/7 operations roadmap

Written 2026-11-19 from a live read of vps2 (`hermes`, `hermes-unthai`, v0.23.1). Nothing on the server was changed. Times are Bangkok time (the vps2 cron clock).

Goal: Hermes runs the daily operation of the company and every project, and Mat is pulled in only for approvals and exceptions.

## 1. Where we start

- 21 profiles, 18 cron jobs. 9 profiles have no job.
- Hermes finds and reports. It sends nothing: all outreach stops at a draft.
- 12 of 18 jobs deliver `local`, so the result sits in a file nobody reads.
- Broken now: `unthai/herald-tick` (HTTP 401 every hour), `leadhunter/lead-review-weekly` (invalid tool call, 11-13), `friendsstation/hostelmate-login-check` (result not delivered).
- Paused: `ce/content-brief` since 11-07.
- The targets page (KH `Projects/hermes/targets`, edited on admin.unth.ai/hermes) already switches jobs on and off per project. Every new job plugs into it.

## 2. Decisions taken (defaults accepted 2026-11-19)

1. Outbound email and outreach need Mat's approval on Telegram for the first 2 weeks of each job. After that, low-risk templates send on their own.
2. Facebook group comments and DM replies stay draft-only. Hermes never posts in a group from a personal account by itself.
3. Finance reads Stripe, Airbnb and Booking payouts, and Hostelmate. No bank access.
4. `spankys` and `spankys-marketing` are archived. The three nitehub profiles are merged into one. Archive, never delete.

## 3. Structure

One profile per function. Projects are rows in the targets page, not profiles.

| Profile | Owns | Functions from Mat's list |
|---|---|---|
| `ceo` | Morning brief built from every other agent's result, approval queue, weekly review, escalation to Mat | all (reporting) |
| `inbox` (new) | Email triage, replies, spam and cold-email filtering | 1 |
| `leadhunter` | Lead hunt, XENIA records, outreach, follow-up sequences, Tour In partner and advertiser outreach | 2, 9 |
| `marketing` | Posting coverage on every account, comments and DMs, Facebook group watch, channel checks | 3, 4, 7 |
| `airbnb` (scope: rentals) | Airbnb and Booking reservations, guest messages, calendar gaps | 5 |
| `finance` (new) | Weekly money report, unpaid invoices, payout checks | 6 |
| `support` | Voice-call follow-up: transcript, email, proposal, escalation | 8 |
| `search` | Research on request for the others (affiliates, influencers, partner lists) | feeds 2, 9 |
| `friendsstation`, `xheart`, `ecommerce`, `xclusive`, `joe`, `revr`, `doggystyle`, `nitehub` | Project chat agents and their existing jobs. No new duties | - |

Rules that apply to every job:

- **Autonomy level per job**, stored as a column in the Agent tasks table: `L0` report only, `L1` draft and wait for approval, `L2` send inside limits, `L3` free. Every new job starts at `L0`.
- **One approval path**: a draft is posted to Mat's Telegram with Approve / Edit / Reject. Nothing else counts as approval.
- **One record**: every lead, reply, call and partner contact is written to XENIA. Every agent result is one line in the `ceo` morning brief.
- **Hard limits per run** (already used by leadhunter): caps on leads, drafts, sends. A job that hits its cap stops and says so.
- **Failure is loud**: a failed or undelivered job shows in the morning brief the next day.

## 4. Roadmap

Model column = which Claude model builds the item. Opus for design, cross-system wiring and anything that sends to real people. Sonnet for a bounded job, a prompt or a script with a clear spec.

### Phase 0 - Repair and make results visible (2 to 3 days)

| # | Work | Model | Done when |
|---|---|---|---|
| 0.1 | Fix `herald-tick` 401 (find which key the script sends and what HERALD expects) | Sonnet | 3 hourly runs in a row end `ok` |
| 0.2 | Fix `lead-review-weekly` invalid KH tool call | Sonnet | Manual run ends `ok` and writes its review |
| 0.3 | Give `hostelmate-login-check` a delivery target | Sonnet | Next run is delivered to Telegram |
| 0.4 | Decide `ce/content-brief`: resume or remove | Mat | Job is active or deleted |
| 0.5 | `ceo/morning-brief` reads the last result and status of every job in both gateways, plus failures | Opus | Brief lists all 18 jobs, with failures first |
| 0.6 | Add the autonomy-level column to the Agent tasks table and make jobs read it | Opus | A job set to `L0` cannot send |
| 0.7 | Archive `spankys`, `spankys-marketing`; merge `nitehub-public` and `nitehub-recruiter` into `nitehub` | Sonnet | Profiles moved to an archive folder, their bots stopped, gateway restarts clean |
| 0.8 | Audit what each profile can reach: MCP servers, API keys, logged-in browser sites | Sonnet | Table in KH: profile, tool, works yes/no |

0.8 matters: the first audit could not confirm MCP wiring per profile, and every later phase depends on it.

### Phase 1 - Eyes everywhere, report only (week 1 to 2)

Every job below runs at `L0` and reports to the morning brief. No sending.

| # | Job | Profile | Schedule | What it reports | Model |
|---|---|---|---|---|---|
| 1.1 | `inbox-triage` | inbox | every 2 h, 08:00-22:00 | New mail per mailbox, sorted: reply needed, FYI, cold pitch, spam. Covers mail.unth.ai domains and Gmail (two separate systems) | Opus |
| 1.2 | `social-coverage` | marketing | daily 09:00 | Per account: last post date, next scheduled post, accounts with nothing in 48 h. Reads HERALD, Blotato and the dashboard `social_accounts` | Sonnet |
| 1.3 | `social-inbox` | marketing | every 3 h | New comments and DMs per account, with the ones that need an answer | Sonnet |
| 1.4 | `fb-group-watch` | marketing | twice daily | Posts in a named list of groups that match a project's ICP, with link and reason. Uses the logged-in Hermes browser, read only | Opus |
| 1.5 | `rentals-daily` | airbnb | daily 08:00 and 18:00 | New, changed and cancelled reservations, check-ins in the next 48 h, unanswered guest messages, empty nights in the next 14 days | Sonnet |
| 1.6 | `finance-weekly` | finance | Mon 08:00 | Revenue per project from Stripe, payouts from Airbnb and Booking, Hostelmate takings, failed payments, open invoices | Opus |
| 1.7 | `channel-check` | marketing | daily 10:00 | Per YouTube channel (faceless channels and XHEART): uploads against plan, views, retention, strikes or policy flags | Sonnet |
| 1.8 | `voice-call-log` | support | every 30 min | Every call to a voice agent: caller, transcript, what they asked for. Written to XENIA | Opus |
| 1.9 | `partner-hunt` | leadhunter + search | daily | Tour In partners and advertisers (hotels, tour operators, tourism boards, travel brands) per country site, written to XENIA | Sonnet |

Needed from Mat before phase 1: the Facebook group list per project; the list of faceless channels; a TOURIN section in the targets page (ICP, countries, what we sell: listing, sponsored article, banner, affiliate).

Exit test: for 5 days running the morning brief covers all nine functions and Mat finds nothing he had to look up by hand.

### Phase 1 status (2026-11-19)

Both live jobs deliver `local` (collected by the 06:30 brief), alert Telegram on failure, and are pinned to `Asia/Bangkok`. New jobs default to UTC: always pass `--timezone Asia/Bangkok`.

| # | Status | Detail |
|---|---|---|
| 1.1 | Live | `ceo/inbox-triage` (id `198368b99bd6`), daily 05:40. Runs on `ceo`, which already has the mail MCP, instead of a new `inbox` profile. First run read 43 of 43 mailboxes on the own domains. Gmail is not covered. Daily, not every 2 h: at L0 the only reader is the morning brief. |
| 1.5 | Live | `airbnb/rentals-daily` (id `f387daee4f40`), daily 05:30. Read-only dashboard tools only. Guest messages are not covered: they need the logged-in browser on Airbnb and Booking. |
| 1.2, 1.3 | Live for Blotato accounts | `ce/social-daily` (id `15a0730086f3`), daily 05:45: coverage, failed posts, comments to answer, DMs, in one job. Reads `/opt/data/feeds/social-blotato.json`. Covers the 13 accounts in Blotato only. Not covered: Facebook Pages in the dashboard `social_accounts` (Tour In and others), HERALD groups, LinkedIn. The feed holds the latest 100 posts and no DM text. |
| Feeds | Live | Host-side, so no publishing or dialing key enters Hermes (decision 2026-11-19). `/root/hermes-feeds/voice_calls.sh` (reads `voice-postgres`, no key) and `/root/hermes-feeds/social_blotato.py` (GET only; key in `/root/hermes-feeds/.env`, root 600). Cron `/etc/cron.d/hermes-feeds` at :25 and :20 every hour, log `/var/log/hermes-feeds.log`. Output in `/root/.hermes/feeds/` = `/opt/data/feeds/` in the container, readable by every agent. |
| 1.6 | Blocked: access | No Stripe key on vps2. Needs restricted read-only Stripe keys (UNTHAI, Friends Station) in a `finance` profile. Rentals income is already readable through the dashboard MCP. |
| 1.8 | Live | `ceo/voice-call-log` (id `b46488d5cc57`), daily 05:35. Reads `/opt/data/feeds/voice-calls.json` (last 26 h). On `ceo`, not `support`: the `support` bot cannot message Mat until he sends it `/start`. Nothing is written to XENIA yet (phase 2). |
| 1.4 | Blocked: input | Facebook group list per project. |
| 1.7 | Blocked: input + access | List of faceless channels; YouTube Analytics access exists only on the Mac (yt-analytics MCP), not on vps2. |
| 1.9 | Blocked: input | Tour In offer and target countries. |

Checked on the way: n8n `UNTH.AI Lead Capture` is active (25 active workflows).

#### Faceless channels (found 2026-11-19, source `~/Code/faceless-channels/CHANNELS.md` + KH `faceless-channel`)

| Channel | Status | For `channel-check` |
|---|---|---|
| Birds Conspiracy | Active. 14 videos in IRIS staging, site live | Yes, once videos publish |
| Good Boy Network | On hold (Higgsfield credits). Handles reserved, no IRIS or Blotato route | No |
| Robot Roasts | Planned. No real clip, no accounts | No |
| 9 paper-only (Philosophical Cats, Toddler Philosophers, Savage Grandparents, Baby Shenanigans, HIA, AI Fortune Teller, Avatar Motivation Singer, Fitness Sloth, Meditation Memes) | Concept only | No |
| XHEART TV, XHEART sister channel (ambient + AI music), XHEART Tech trending series | Live, not faceless-channel project | Yes |

So 1.7 covers XHEART's channels and Birds Conspiracy. It still needs YouTube Analytics access on vps2. The larger gap is production, not monitoring: only one faceless channel can make videos.

#### Facebook groups (1.4), reworked

No group list exists per project, except Spanky's (218 synced, 183 reviewed) in HERALD. HERALD is already the system for groups: group registry per business, tags and categories, membership checks through real consenting people, propose and approve posts. So groups go into HERALD, not a new list.

1. `search/fb-group-discovery` (new, weekly, report only): per active project in the targets page, find candidate groups (name, URL, members, language, posting rules, why it fits) and write them to a KH page per project. Public search only, no logged-in browsing.
   Live since 2026-11-19: id `0edd28c65115`, Wednesdays 03:00 Bangkok. First run: 34 groups on 4 pages `Projects/hermes/fb-groups/{xheart,unthai,htmmw,tourin}`. Member counts come from search snippets (the profile's `web_extract` backend is search-only and Facebook shows a login wall), so treat them as unverified.
2. Mat picks groups. Joining is done by a person from their own account: HERALD forbids clients from browsing as a logged-in person. Creating our own groups is also manual.
3. Joined groups are added to HERALD under the project's business with tags.
4. `fb-group-watch` reads them through HERALD. Blocker: `HERALD_READS` is off and its selectors have never run on a live Facebook page. That is HERALD work, in the HERALD repo.

Each project needs a business in HERALD first: today only `spankys` and `nitehub` exist.

Tour In offer and target countries (1.9): being built in its own session, result goes to KH under `Projects/tour-in/`.

### Phase 2 - Drafts with one-tap approval (week 3 to 4)

Jobs move to `L1`. Each draft goes to Telegram for Approve / Edit / Reject.

| # | Work | Model |
|---|---|---|
| 2.1 | Approval queue: Telegram buttons, a record of every decision, send on approve | Opus |
| 2.2 | Email replies: draft for "reply needed" mail; cold pitches and spam archived without a draft | Opus |
| 2.3 | Lead outreach: first message at once when a lead is added, then follow-ups on day 3, 7 and 14, stopped on any reply | Opus |
| 2.4 | Comment and DM reply drafts per brand voice | Sonnet |
| 2.5 | Facebook group drafts: a suggested comment or private message for each matched post. Mat posts it himself | Sonnet |
| 2.6 | Voice follow-up: after each call, a summary email to the caller and a proposal built from what they asked for. Escalate to Mat when the deal is large or the request is unclear | Opus |
| 2.7 | Tour In pitch: media kit per country site with real traffic numbers, and an outreach sequence | Opus |
| 2.8 | Guest message drafts for Airbnb and Booking | Sonnet |
| 2.9 | Posting gaps: when an account has nothing planned, ask IRIS for content and queue it in HERALD for approval | Sonnet |

#### Phase 2 status (2026-11-19)

Design decided: approve by Telegram text reply, send by a host-side script. XENIA already holds the queue as tags: `draft-ready` → `approved-to-send` / `rejected` → `contacted` → `followup-ready` → `cold`.

| # | Status | Detail |
|---|---|---|
| 2.1 approve | Built | `leadhunter/approval-queue` (id `084bd5b72a90`), daily 07:00, delivers to Mat's Telegram: up to 8 oldest drafts with full text. Mat replies `send 1,3` · `drop 2 - reason` · `edit 4: new text`; rules appended to `leadhunter/SOUL.md` (backup `.bak-20261119`). |
| 2.1 send | Blocked: XENIA | XENIA's agent API has no action that sends one custom email to a lead: `outreach:send` gates only `sequences.enroll`. Needs a new action `outreach.sendDraft` in the CRM repo (proposed as its own task). Until then Mat sends approved drafts from XENIA by hand, as before. |
| 2.1 send, XENIA deploy | Live 2026-11-19 04:15 UTC | `main` = `e72a6f6` (fast-forward, not pushed). Migration applied to **`crm-postgres`** (the backend's database; the session's note said `root-postgres-1`, which is wrong since the 2026-11-18 move) and recorded with `prisma migrate resolve`. `/api/version` `gitSha` `e72a6f6`, health 200, `outreach.sendDraft` in the manifest, Prisma reads `tags`. Rollback images `crm-crm-backend:rollback-f5ebbc2`, `crm-crm-standalone:rollback-f5ebbc2`; the column can stay. Not done: canary send, a key with `outreach:send`. |
| 2.1 tags switch | Done 2026-11-19 05:20 UTC | 198 leads tagged `draft-ready` through the API. `leadhunter/SOUL.md` and jobs `lead-hunt-daily`, `outreach-queue`, `approval-queue` use `addTags` / `removeTags` / `leads_list tag` (backups `.bak-20261119-tags`). Verified: `approval-queue` showed `8 of 198` using only `xenia` and KH tools. Gotcha: the gateway caches each MCP server's tool list at start and does not respawn a killed stdio server, so **after any XENIA API change restart the main gateway** (`docker restart hermes`). `leads_list` returns at most 200 leads, no total, no offset. Not tested: Mat's `send` / `drop` / `edit` replies. |
| CRM stability | Fix live, not yet proven | Cause: the OCR timeout terminated the `tesseract.js` worker while tesseract was still downloading the image; the late `postMessage` was an unhandled rejection and Node exited. Fix `b8a2dcf` (branch `fix/ocr-worker-crash-loop`, merged to local `main`, not pushed) live since 2026-11-19 06:27 UTC: `/api/version` `gitSha` `b8a2dcf`, health 200, `RestartCount` 0 after 6 minutes. No OCR job had run yet at that check, so the fix was not exercised. Re-check `docker inspect root-crm-backend-1 --format '{{.RestartCount}}'` and the log for `OCR failed` (handled) and `unhandled promise rejection` after a few hours. |
| 2.1 sender script | Built, switched off | `/root/hermes-feeds/outreach_sender.py` on the vps2 host (source `unthai/hermes-feeds/outreach_sender.py` in this repo). Dry run by default; `--send` sends leads tagged `approved-to-send` with `outreach.sendDraft`, at most `SENDER_MAX_PER_RUN` (default 5) per run, idempotency key = hash of lead id + subject + body, stops the run on a cap, `SENDING_DISABLED`, a 502 or a timeout. It parses the LAST draft block in the notes (`FIRST-EMAIL DRAFT` or `FOLLOW-UP DRAFT` header, `Subject:` line, body up to `END-DRAFT`, a known notes header, or the end) and refuses template leftovers. Results go to `/root/.hermes/feeds/outreach-sent.json`. Dry run 2026-11-19 over the 198 drafts with the read key: 166 would send (every body ends at the signature), 20 skipped for no draft header (XHEART sponsor leads such as Hugging Face, DJI), 12 for no email. Format rules appended to `leadhunter/SOUL.md` (backup `.bak-20261119-format`). **No key and no cron yet.** To switch on: 1) Mat mints a XENIA key with `outreach:send` + `leads:read` and puts it in `/root/hermes-feeds/.env` as `XENIA_SEND_KEY`; 2) canary: tag the internal `mat@unth.ai` lead `approved-to-send`, run `python3 /root/hermes-feeds/outreach_sender.py --send`, check the mail and that a reply lands on the lead; 3) add a cron line to `/etc/cron.d/hermes-feeds`. |
| 2.1 send, XENIA side | Built | `outreach.sendDraft` on branch `feat/outreach-send-draft` (`e72a6f6`) in `~/Code/crm`, 1627 backend tests pass. Not pushed, not merged, no canary send. It also adds real tag storage (`Lead.tags`, migration `20261119000002_lead_tags`, `leads.update` `addTags` / `removeTags`, `leads.list` `tag`): XENIA had none, so the leadhunter "tags" today are text in notes or another field. After deploy: switch `leadhunter/SOUL.md` and the jobs `lead-hunt-daily`, `outreach-queue`, `approval-queue` to the tag params, re-tag the existing drafts once, then write the host sender script. Daily cap: env `OUTREACH_SEND_DRAFT_DAILY_CAP` (default 10) in `/root/crm/.env`. Contract and deploy steps: session notes `xenia-outreach-senddraft.md`. |
| Models | Tested | `gpt-6.1-sol`, `gpt-6-sol`, `gpt-6-luna` all answer through the Codex login (`--provider openai-codex`). Not yet pinned on any job. |

Found while building: the Ollama account refuses concurrent runs (`HTTP 429: too many concurrent requests`) and the job fails instead of falling back. Morning jobs are now spread: rentals 05:00, voice 05:10, inbox 05:20, social 05:50. Keep new jobs at least 10 minutes from any other, or pin them to another provider.

Writing quality: Hermes runs on DeepSeek through Ollama. Before any `L1` job goes live, test its drafts on 20 real cases. If the drafts are not good enough to send with light edits, give that job a stronger model for the writing step only.

Exit test: Mat approves 80% of drafts without editing, for one week, per job.

### Phase 3 - Send inside limits (week 5 to 8)

A job moves to `L2` only after it passes its phase 2 exit test. One job at a time.

- Order: email acknowledgements and simple replies, then lead follow-ups (not first contact), then comment replies on our own pages, then guest messages, then first-contact outreach.
- Limits per job: sends per day, allowed recipients, allowed templates, no prices or commitments outside the approved offer sheet.
- Never automatic: Facebook group comments, refunds or any money movement, contracts, anything a recipient could read as a legal commitment, replies to complaints.
- A weekly sample of 10 sent messages per job goes to Mat. Two bad ones puts the job back to `L1`.

### Phase 4 - Steady state (from week 9)

- `ceo/weekly-review` scores each function: volume, replies, revenue touched, failures.
- Targets page reviewed monthly: which projects are on, with what numbers.
- Any new project gets a row in the targets page and an ICP section. No new profile.

### Phase 0 status (2026-11-19)

| # | Status | Detail |
|---|---|---|
| 0.1 | Done | HERALD key `hermes-tick` (id 2, scope `propose`, business `spankys`) was revoked 2026-11-17 15:07 UTC with the other spankys keys. Mat issued key id 26 `hermes-tick-20261119` (scope `propose`, business `nitehub`: HERALD refuses a propose key with no business) into `/opt/data/profiles/unthai/herald-tick.key`. Manual tick 2026-11-18 18:32 UTC ended `ok`. Old file kept as `herald-tick.key.bak-20261119`. |
| 0.2 | Done | Cause: KH MCP returned 500 and was parked minutes before the 11-13 run, so its tools were missing. Manual run 2026-11-18 17:31 UTC ended `ok`. No change needed. |
| 0.3 | Done | `--deliver telegram:5165748436`; manual run delivered. Backup `jobs.json.bak-20261119`. |
| 0.4 | Waiting for Mat | `ce/content-brief` still paused. |
| 0.5 | Mostly there already | `ceo/scripts/collect_runs.py` feeds every job's output and a failing-jobs list into the brief, but only for the main gateway: `hermes-unthai` is not mounted there. Instead of a new mount, every job now has `--failure-deliver telegram:5165748436` (9 jobs set, backups `jobs.json.bak-20261119-fd`). The two `marketing` jobs are skipped: no bot, the script alerts by itself. |
| 0.6 | Moved to phase 2 | All outreach jobs are draft-only by prompt today, so a level column would gate nothing yet. Build it with the approval queue (2.1). |
| 0.7 | spankys done, nitehub open | `spankys` + `spankys-marketing` moved to `/root/.hermes/profiles-archive-20261119/` and the main gateway restarted 2026-11-18 18:40 UTC (script `/root/archive-spankys-20261119.sh`). 15 bots reconnected, the two are no longer registered, Friends Station job ran `ok` at 18:49. The gateway left two empty `spankys*` log folders in `profiles/`. Restore = move the folders back and restart. Found on restart: the bots of `joe`, `nitehub-recruiter`, `support`, `xclusive` answer `Chat not found` for chat 5165748436, so they cannot message Mat until he sends each one `/start`. Nitehub merge: `nitehub-public` has no bot and may serve the NiteHub site through the API: check before merging. No API calls to any of the four profiles in the last 72 h. |
| 0.8 | Done | KH wiki `Projects/hermes/profile-access-audit-2026-11-19`. |

### Model per job

Every profile runs `ollama-cloud:deepseek-v4.1-flash:1017` with fallbacks `gpt-5.5` (Codex OAuth), freellm `auto:reliable`, `auto:fast`, `deepseek-chat`, `gpt-oss:120b`. A cron job can pin its own model with `hermes cron edit <id> --model <m> --provider <p>`, so the choice is per job, not per profile.

| Kind of job | Model | Why |
|---|---|---|
| Collect, count, check, sort (coverage, rentals, channel check, call log, spam sort) | DeepSeek flash (current) | Cheap, high volume, structured output |
| Text a real person reads (email replies, outreach, proposals, guest messages, group comments) | A stronger writing model, pinned on the job | One weak message costs more than the tokens saved |
| Reasoning over many inputs (morning brief, finance weekly, weekly review) | Stronger model, runs once a day or week | Low volume, so cost is small |
| Script-only (`marketing`, `herald-tick`, login check) | No model | Already the cheapest |

Candidates for the stronger tier are tested in phase 2 on the same 20 real cases per job. Pick per job on approval rate, then cost.

- GPT-6 family through the Codex login already in the configs (`provider: openai-codex`, subscription usage, no per-token bill, but it can run out). Hermes v0.23.1 knows `gpt-6-luna`, `gpt-6-sol`, `gpt-6-astra` (each with `-pro`; astra also `-fast` / `-flex`) and `gpt-6.1-sol`. It has no `gpt-6.2` id: that needs a Hermes upgrade or a manual model entry. Owner note 2026-11-19: prefer GPT-6.x over `gpt-5.5`.
- Claude Sonnet through the Anthropic key, MiniMax M3.1 through Ollama: per-token cost, used where GPT-6 loses the test or the Codex usage runs out.

First step in phase 2: list which GPT-6 ids the Codex account really serves and what each costs in usage, then replace the `gpt-5.5` fallback in all configs with the chosen one (`/root/hermes-desktop/set-model-chain.py`).

## 5. Risks

- **Account bans.** Automated activity in Facebook groups and on Airbnb/Booking from a logged-in browser can lose the account. Read-only and low frequency in phase 1; group posting stays manual.
- **Email reputation.** Cold outreach from the main domains can hurt delivery of normal mail. Send outreach from a separate sending domain, with volume raised slowly.
- **Wrong promises.** An agent that quotes a price or a date binds the company. Offer sheet per project, and nothing outside it.
- **Server.** vps2 has one failed NVMe and one worn one (OVH ticket open). More jobs raise the cost of an outage. Keep job state in XENIA and KH, not only on the host.
- **Model limits.** All jobs share one Ollama account. Stagger schedules and watch for the weekly limit.

## 6. Not verified in this audit

- MCP servers and working API access per profile (item 0.8).
- n8n workflows (16 unpublished after the 11-14 upgrade) and whether any still does part of this work.
- State of the voice gateway (PHEME) and where call transcripts land today.
- Which social accounts HERALD and Blotato each carry.
- Whether XENIA can hold a follow-up sequence or needs a new field.
