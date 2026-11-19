# Handoff: Herald deploy and posting work (session of 2026-09-30 → 2026-10-01)

Start here in a fresh session. Everything below was true at 2026-09-30 18:35Z.

## Where things are

- **Repo:** `~/Code/herald` (github `unthai/herald`, private). The shared checkout is used by other
  sessions: do not work in it. This session's worktree: `~/Code/herald-wt-deploy` (detached at
  `origin/main`); its untracked `.claude/` holds three reports:
  - `double-post-report.md`: can two approvals post a group twice (answered, fixed).
  - `vps2-rebuild-audit.md`: 58 images on vps2 recreate their container on every rebuild.
  - `recreate-report.md`: why (provenance attestation + containerd image store).
- **Live:** Herald on vps2 (`unthai-dashboard`), `origin/main` `e43f4a7` (code `1cb7e84`), healthy.
  Record of every deploy: `docs/superpowers/rollout-log.md` in the repo.
- **Deploy:** only `scripts/deploy.sh <label>` from a checkout of `origin/main` (it ships
  `git archive origin/main`). It runs the 3.12 suite in the extracted tree, takes a lock on vps2
  (`/run/lock/herald-deploy.lock`, holder in `.info`), copies the DB, rsyncs with checksums, builds,
  runs `restart-check && up -d` in one command, waits for health. One ssh connection per run.
  A deploy with no image change does not recreate the container. `--dry-run` shows drift only.
- **Second agent:** Claude Code on `deepseek-v4.1-flash:cloud` in cmux `workspace:3` / `surface:5`,
  cwd `~/Code/herald-wt-deploy`. Idle at ~56% context: send `/clear` before a new task.
  Drive it with `C=/Applications/cmux.app/Contents/Resources/bin/cmux`:
  `$C read-screen --surface surface:5 --lines 40`, `$C send --surface surface:5 "..."`,
  `$C send-key --surface surface:5 Enter`. Long briefs go in a file in its worktree's `.claude/`.
  Its stub tests have passed on broken code three times: read its diffs and run the mechanism live.

## Done this session (all merged and deployed)

| PR | What |
|---|---|
| #13 | Run report readable (later trimmed to English-only by the other session's #29) |
| #16, #19 | `scripts/deploy.sh` |
| #20, #22 | Deploy lock on vps2; lock files kept out of the shipped tree |
| #25 | `provenance: "disabled=true"`: a build without changes keeps the image id |
| #26 | One ssh connection per deploy (lock connection is the ControlMaster); healthcheck `start_period 20s`, `start_interval 2s` (boot is ~2 s) |
| #27 | Plain words for all 22 failure reasons (`reason_text()`) |
| #30 (= #28) | Claim the group at submit in one `BEGIN IMMEDIATE`: two people can no longer post one group twice |

## Open, needs Mat

1. **Proposals in Telegram:** approve **9**, reject **8** (same text; 8 also plans group 174, whose
   Spanky's tag is paused). 6 plans the same five groups as 9: approved second, it fails
   `posted_recently`. Post 6 in two days, or re-propose then.
2. **Hermes containers recreate on every rebuild** (bots drop ~2.5 min). `hermes-agent:latest` is an
   OCI index with an attestation. Fix is the Herald pattern, but it touches the prod gateway: do it
   with Mat present. Hermes builds with the `htthrottle` buildx builder (`--load`), so the flag goes
   on that build command (`--provenance=false`), not only the compose file. Check with
   `docker image inspect hermes-agent:latest --format '{{.Descriptor.MediaType}}'` after.
3. **Other vps2 projects:** see `vps2-rebuild-audit.md` (mugen worker, payload-cms, voice, camofox
   matter most; many use `--force-recreate` anyway).

## Open, known limits (no action unless they bite)

- `deploy.sh`: no automatic rollback; `kill -9` of the script frees the lock while a step may still
  run (documented in `take_lock`); test suite is opt-out, kept on purpose (no CI), against the
  estate rule 1 in Knowledge Hub `conventions/deploy-speed`.
- 2026-09-30 15:54-15:56Z: new ssh connections from the Mac to vps2 hung, sshd logged none. Cause
  unknown.
- Branch `fix/report-reason-words` on origin holds a merge of #28 (it was #28's base); harmless,
  can be deleted.

## Lessons (also in memory)

- One session deploys Herald at a time; the lock now enforces it.
- Search Knowledge Hub for conventions before briefing deploy-path work.
- `provenance: false` does not work on Compose v5.1.4; `"disabled=true"` does.
