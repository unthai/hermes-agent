# Session prompt: fold the REVR content engine into IRIS, then delete the duplicate

Paste everything below the line into a new Claude Code session. Suggested working directory:
`~/Code/content-platform` (the IRIS repo). Facts below were verified on 2026-10-14/15 unless marked
**VERIFY**.

---

## Goal

UNTHAI product naming: **IRIS = the content engine**. Today there are two content engines on vps2:

1. **IRIS (global)**: container `root-content-engine-1`, source `content-platform/apps/content-engine`.
2. **REVR content engine (duplicate)**: container `root-revr-content-engine-1`, source
   `revr-dashboard/content-engine` (package `@revr/content-engine` v0.1.0).

Mat's decision: REVR must NOT be a separate system. It must run **inside IRIS** as a brand/tenant, and
the duplicate must then be **deleted**. Do this safely: nothing REVR-specific (briefs, sources,
schedule, published history, analytics, backups) may be lost, and the duplicate is removed only after
the IRIS-hosted REVR pipeline has been proven in production and Mat has said yes to the deletion.

## Why now (the symptom that started this)

The REVR engine cannot reach Hermes: its compose service is attached only to the `revr_internal`
network (compose alias `revr_db`), so `http://hermes:8642` does not resolve. Logs show repeated
`hermes task failed: fetch failed`, and cover generation then falls back to Gemini, which has no
`GEMINI_API_KEY`, so blog posts publish **without a cover image**
("cover generation failed — publishing without cover", briefs 58 and 59, 2026-10-13/14). This
predates the Hermes v0.22.0 upgrade and is a network problem, not an upgrade regression. Moving
REVR into IRIS removes the problem at the root (IRIS is on `root_default` and already has the
Higgsfield mounts); do NOT just bolt `root_default` onto the REVR container as the fix.

## What I know about the two systems

### IRIS (global), the target
- Container `root-content-engine-1`, image `root-content-engine:latest` (created 2026-10-14 13:21 UTC),
  cmd `node dist/index.js`, workdir `/app`, network `root_default` only.
- Compose: `/root/content-platform/deploy/docker-compose.yml`, service `content-engine`.
  The compose project is `root`, launched from `/root/docker-compose.yml`; the CE compose re-declares
  `content-engine-redis` with an explicit `container_name` that project `root` owns, so ALWAYS recreate
  with `--no-deps` (KH convention "vps2 compose recreate collides on shared container_name").
- Mounts: volume `root_htmmw_media` -> `/app/media`, `/root/higgsfield-data` -> `/higgsfield`,
  `/root/backups/content-engine` -> `/backups`.
- Live source is the monorepo `/root/content-platform/apps/content-engine` (316 src files, dirs
  `analytics config curate db generate index.ts ingest inventory lib ops publish queues seo social
  workers`). The VPS tree is not a git checkout; local repo is `~/Code/content-platform`.
  Last known commit in KH: `0147ca8` (sendAlert, 26 call sites).
- Alerts: `sendAlert` -> Telegram @UNTHAI_content_writer_bot + ntfy `htmmw-content-engine` +
  `content_pipeline.alerts` row. Hermes profile `ce` ("UNTHAI CE") is its operator bot; its `.env`
  `CE_ADMIN_KEY` = IRIS `PAYLOAD_API_KEY` for `x-admin-key` calls to
  `http://root-content-engine-1:3010/admin/*` and `/api/admin/*`.
- **Known IRIS gotchas (read before any deploy):**
  - `scripts/deploy.sh` builds with plain `docker build --no-cache`, not `htthrottle`
    (primer issue 17). Use the capped builder: `docker buildx use htthrottle` / `--builder htthrottle`.
  - KH says VPS `/root/ce-patches` mounts can shadow image files and contain an HTMMW strict-cover
    hotfix that the repo lacks, while the repo has an inline-images feature the VPS lacks.
    A clean rebuild from the repo can silently drop that hotfix. **Reconcile ce-patches vs repo
    (diff them) and audit the compose for stale file mounts BEFORE building.**
  - Search KH first: `searchContext("content engine deploy", "<IRIS project slug>")`. Find the slug
    with `listProjects` (try content-platform / htmmw / content-engine).

### REVR content engine, the duplicate (source of what must be migrated)
- Container `root-revr-content-engine-1`, image `revr-content-engine:latest` (created 2026-10-10
  18:21 UTC; rollback tags `revr-content-engine:previous` and `:f324510`), started 2026-10-10,
  no restarts, healthcheck `http://127.0.0.1:3010/healthz`.
- Compose `/root/revr-dashboard/docker-compose.yml`, service `revr-content-engine`
  (build context `./content-engine`), env file `/root/revr-dashboard/content-engine/.env`,
  mount `/var/backups/revr-content-engine` -> `/backups`, network `revr_internal` only.
- Source `/root/revr-dashboard/content-engine` (not a git repo on the VPS; the repo is
  `revr-dashboard`, KH slug `revr-dashboard`, merged into KH slug `revr`; local checkout not at
  `~/Code/revr-dashboard`, **VERIFY** under `~/Code/revr/`). 144 src files. Top-level modules
  `analytics calendar config.ts curate data db generate index.ts ingest lib ops publish queues
  refresh workers`. Modules only REVR has: **`calendar`, `data`, `refresh`**. Modules only IRIS has:
  `config`, `inventory`, `seo`, `social`. Both share `lib/hermes.ts` and `lib/higgsfield.ts`.
  Docs in its root: `REPRODUCTION.md` (2026-06-07, "reproduce, adapt or port to any UNTH.AI project"),
  `IMPLEMENTATION-PLAN.md`, `AUDIT-REPORT.md` (sources rated 0.3-0.9 for "real-estate investing,
  PropTech"), `_smoke.mjs`, `tests/`, `scripts/`.
- Pipeline: ingest (RSS, Reddit, YouTube, email newsletters) -> curate (audience_fit x
  monetization_signal, dedupe, top 8) -> generate (1200+ word blog, editor pass, fact-check, SEO, cover)
  -> quality gate -> publish (Payload CMS blog, Listmonk newsletter, n8n social, Postiz reels)
  -> analytics (engagement poll every 15 min feeds topic boost). DB migrations include
  `018_cron_schedule.sql`, `029_cost_caps.sql`, `031_fix_cron_schedule.sql`.
- Env variable NAMES (never print values): DATABASE_URL REDIS_URL PUBLISH_TARGET PAYLOAD_URL
  PAYLOAD_API_KEY PUBLIC_SITE_URL FREELLM_URL FREELLM_API_KEY LLM_PROVIDER ANTHROPIC_API_KEY
  NVIDIA_API_KEY SEARCH_PROVIDER EXA_API_KEY MEDIA_PUBLIC_URL HTTP_PORT CONTENT_ENGINE_ADMIN_KEY
  NTFY_TOPIC CRON_EXPR CONTENT_LANGUAGES CONTENT_PRIMARY_LANG LISTMONK_URL POSTIZ_URL HERMES_URL
  HERMES_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID. Note `GEMINI_API_KEY` is NOT set (the
  cover fallback is dead).
- Alerts: Telegram @UNTHAI_content_writer_bot tagged `[REVR CE]` + ntfy `revr-content-engine`.
  Built via `htthrottle` (revr-dashboard `f324510`).
- Its Postgres and Redis live on `revr_internal` (`root-revr-postgres-1` has a `revr_dashboard`
  DB; **VERIFY** which DB and schema the engine uses, and where its Redis is). Its CMS target is
  REVR's Payload (`root-revr-cms-1`, **VERIFY** `PAYLOAD_URL`).
- Related REVR facts (KH slug `revr`): REVR is one global product, launch Thailand + Japan,
  brand line "the first Super Real Estate Agent"; do not describe it as Thailand-only or a
  "real estate marketplace".

## Hermes facts you need (this session upgraded Hermes to v0.22.0)

- From a container on `root_default`, `http://hermes:8642` is the default profile; profile APIs are at
  `/p/<profile>/v1` (the `ce` profile exists). Auth is a shared `API_SERVER_KEY` (IRIS calls it
  `HERMES_API_KEY`); read it from env files, never print it.
- `hermes-agent` image `7e64f1e1d2d6` = v0.22.0. Health: `GET http://hermes:8642/health` returns
  `{"status":"ok","version":"0.22.0"}`.
- Image generation goes Hermes -> `higgsfield-gateway` (`http://higgsfield-gateway:3050/mcp`),
  which owns the only OAuth grants; do not re-authorize from a profile.
- Hermes KH primer (`getPrimer("hermes")`) has the full operational detail and gotchas.

## Environment rules (these have each cost an incident before)

- vps2 (`ssh unthai-dashboard`, root@15.235.13.34) is shared by 35+ services. NEVER
  `docker compose down`, never `docker image/system/volume prune -a`, never stop
  `hermes-workspace`. Recreate single services with `up -d --no-deps --force-recreate <svc>`.
- Builds: use the capped builder (`docker buildx use htthrottle`), `nice -n19 ionice -c3`,
  detached with `nohup ... &` (SSH to vps2 drops intermittently; 2 of 3 connects timed out on
  2026-10-14/15). An uncapped build once hard-reset the host. Disk was 89% (50 GB free); the disk
  guard prunes at 90%, so check `df -h /` first and keep build cache small.
- Tag the current image before replacing it (`docker tag <img>:latest <img>:rollback-YYYYMMDD`).
- Secrets: never print env values (no `printenv`, `docker exec ... env`, `cat .env`). Check names only.
  Read values inside the command that needs them.
- Query Knowledge Hub BEFORE asking me (`searchContext`, slug in `.kh-project`); write what you learn
  back (contribute with `session_id` + `source_ref`). Default owner email: mat@unth.ai.
- Use the Superpowers `brainstorming` skill for the design step and `verification-before-completion`
  before claiming anything is done.

## Plan (do the phases in order; stop and report at each gate marked GATE)

### Phase 0: orient (read-only)
1. Read KH for IRIS and REVR (`getPrimer`, `getGotchas`, wiki pages on content engine and REVR content).
2. Diff the two trees module by module (`generate`, `publish`, `curate`, `ingest`, `lib`, `db`,
   `workers`, `queues`). Produce a table: REVR-only code, IRIS-only code, same-name-different-behaviour,
   identical. Determine which came first and what REVR customized (sources, scoring, prompts,
   languages, publish targets, cron, cost caps).
3. Answer: does IRIS already support multiple brands/tenants (look for a brand/site/tenant key in
   `db` schema, `config`, `publish`, `inventory`)? HTMMW is IRIS's current brand (Payload =
   howtomakemoneywith.ai). If there is no tenant concept, that is the main design work.
4. Inventory REVR state to preserve: DB tables and row counts (briefs, content items, sources,
   analytics, cost ledger, cron schedule), published content and its Payload ids, media, Listmonk and
   Postiz objects, ntfy topic, backups under `/var/backups/revr-content-engine`.
5. **GATE:** write the findings and a proposed design to `docs/` and show me before changing anything.

### Phase 1: design (brainstorming skill)
Decide, with me, how REVR becomes an IRIS brand: per-brand config (sources and scores, languages,
persona/prompts, publish targets for Payload/Listmonk/Postiz, cron schedule, cost caps, alert topic
and tag), data separation (brand column vs schema), and whether REVR-only modules
(`calendar`, `data`, `refresh`) are folded into IRIS generally or kept brand-gated. Keep the
IRIS HTMMW behaviour byte-for-byte unchanged by default (feature-flag or brand-scoped).

### Phase 2: implement in `content-platform` (TDD, small commits)
- Brand/tenant plumbing + REVR brand config, migrated REVR-only modules, tests, and an HTMMW
  regression test. Resolve the `ce-patches` divergence first (see gotchas) so the deploy does not
  drop the HTMMW strict-cover hotfix.
- Cover generation must use the working path (Hermes on `root_default` -> Higgsfield). Do not rely on
  Gemini (no key). Make "publish without cover" a loud alert instead of a silent warning.

### Phase 3: data migration (REVR DB -> IRIS)
- Take a fresh `pg_dump` of the REVR content-engine DB and verify it restores. Copy, never move.
- Import into IRIS under the REVR brand; verify row counts and a sample of Payload ids match.
- Keep the REVR engine RUNNING and publishing during this phase; do not run two engines publishing
  the same brand. Use `PUBLISH_TARGET`/dry-run on the IRIS side until cutover.
- **GATE:** show me counts and a dry-run publish before cutover.

### Phase 4: cutover
- Build the IRIS image with the capped builder, tag the rollback, recreate `content-engine`
  with `--no-deps`. Pause the REVR engine's cron (stop publishing, do not delete), enable the REVR
  brand schedule in IRIS, run one real cycle, and verify: blog on the REVR Payload site with a
  cover image, newsletter draft, social/reel jobs queued, analytics poll, alerts tagged for REVR,
  cost caps enforced.
- Keep the REVR container stopped (not removed) for a soak period (propose 7 days).
- Update consumers: Hermes `ce` profile / any admin calls that targeted `root-revr-content-engine-1`,
  `scripts/backup-watchdog.sh` and the REVR compose/ntfy topic, `revr_dashboard` references.

### Phase 5: delete the duplicate (ONLY after soak and my explicit "yes")
List exactly what will be removed and wait for my confirmation, then:
- `root-revr-content-engine-1` container and the `revr-content-engine` service block in
  `/root/revr-dashboard/docker-compose.yml` (back up the file first).
- Images `revr-content-engine:latest|previous|f324510` (keep one tarball export or a git tag of
  the source for rollback if I ask).
- `/root/revr-dashboard/content-engine` source (archive to `/root/archive/` first) and
  `content-engine` from the `revr-dashboard` repo; dump then drop its now-unused DB objects.
- `/var/backups/revr-content-engine` only after its dumps are copied into IRIS backups.
- Any cron/ntfy/watchdog entries pointing at it.
Never use `docker image prune -a` or similar to do this; remove by exact name.

### Phase 6: close out
- Update KH: IRIS primer (REVR brand, config, deploy steps), REVR primer/dashboard primer
  (engine now in IRIS), the Hermes primer (remove the revr-content-engine consumer and the
  network note), alert routing map, and record the decision "REVR is an IRIS brand".
- Verify end to end and report with evidence (logs, row counts, a published URL).

## Acceptance criteria
1. REVR blog/newsletter/social/reels are produced by IRIS under a REVR brand, with a cover image.
2. HTMMW output is unchanged (regression test + one observed cycle).
3. No REVR data lost: counts match the pre-migration dump.
4. `root-revr-content-engine-1`, its images, compose block and source are gone, with a documented
   rollback (dump + archived source) and my explicit approval for the deletion.
5. KH and alert routing reflect the new single system.

## Report back
At each GATE: what you found, what you propose, and what you will NOT touch. If something here
turns out to be wrong, say so and correct the plan rather than working around it.
