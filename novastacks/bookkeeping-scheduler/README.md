# Monthly bookkeeping — scheduled job (Mac mini)

Runs the `monthly-bookkeeping-controller` skill automatically on the **1st of each
month at ~07:00 local**, closing the previous month, and **emails the digest** when
it finishes. Built to run on the always-on Mac mini through Claude Code, where the
local Google Drive invoice folder and local machine actions are available.

## What's here

| File | Purpose |
|------|---------|
| `install.sh` | One-time installer. Generates + loads the launchd LaunchAgent. |
| `run-monthly-bookkeeping.sh` | The runner launchd fires. Calls Claude Code headlessly and logs the run. |
| `bookkeeping-run-prompt.md` | The unattended prompt (invokes the skill, sends the email). No vendor data or email address is stored here — those live only on the mini. |

## Prerequisites on the Mac mini

1. **Claude Code CLI installed** and on PATH (`which claude` returns a path).
2. **The `monthly-bookkeeping-controller` skill present** on the mini (it carries the
   vendor tables, Airtable IDs, and the local Drive path — kept off this public repo).
3. **MCP connectors configured** in Claude Code on the mini: **Gmail**, **Airtable**,
   and **Google Drive** — the same accounts the skill expects.
4. **Google Drive desktop sync running** so the local
   `…/NOVASTACKS AI/Invoices and Receipts/` folder exists for the PDF mirror step.
5. **Auto-login + no sleep at 07:00** (System Settings → Energy). A LaunchAgent runs in
   your logged-in GUI session, which it needs for connector keychain access. If the mini
   is asleep at 07:00, launchd runs the job once on the next wake instead.

## Install

```bash
cd novastacks/bookkeeping-scheduler
BOOKKEEPING_EMAIL=you@yourdomain.com ./install.sh
```

That writes `~/Library/LaunchAgents/com.novastacks.bookkeeping.monthly.plist` (with your
email and the resolved `claude` path baked in locally) and loads it.

## Test it immediately (don't wait for the 1st)

```bash
launchctl start com.novastacks.bookkeeping.monthly
tail -f ~/Library/Logs/novastacks-bookkeeping/run_*.log
```

You should get the digest email within a few minutes, and the full digest in the log.

## How the unattended run behaves

- **Auto-applies only the safe part**: inserting brand-new, deduped invoices into
  Airtable and mirroring their PDFs to the local Drive folder.
- **Never auto-applies judgment calls** (moving a vendor between active/passive/cancelled,
  editing the skill's tables, reclassifying a price change). Those are listed in a
  **"Needs your confirmation"** section of the email for you to action by hand.
- If a connector is down it notes it at the top of the email and continues.

## Security note

The runner uses `claude -p … --dangerously-skip-permissions` so the Gmail/Airtable/Drive
tool calls run without an interactive approval prompt. That's appropriate for a job you
own on a machine you control. If you'd rather tighten it, replace that flag in
`run-monthly-bookkeeping.sh` with an explicit allowlist, e.g.:

```bash
--allowedTools "mcp__Gmail__* mcp__Airtable__* mcp__Google_Drive__* Read Write Edit Bash"
```

(Exact MCP tool-name prefixes depend on how your connectors are registered on the mini —
run `claude mcp list` to confirm.)

## Change the schedule or recipient

Edit the values and re-run `install.sh` (it reloads in place). For example, to move it to
the last-day-of-month or a different hour, adjust `StartCalendarInterval` — or just change
`Hour`/`Minute` and re-run the installer with the same `BOOKKEEPING_EMAIL`.

## Uninstall

```bash
launchctl unload ~/Library/LaunchAgents/com.novastacks.bookkeeping.monthly.plist
rm ~/Library/LaunchAgents/com.novastacks.bookkeeping.monthly.plist
```
