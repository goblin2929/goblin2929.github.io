# Bianca — Mac mini setup playbook

Run these on the **Mac mini**, where Claude Code (Bianca) lives. Everything the
phone sends arrives over Telegram; Bianca does the thinking and sends via
Gmail / WhatsApp Web.

> Hand this to Claude Code on the mini: open the repo and say
> *"Follow bianca/SETUP.md to set up the card follow-up flow."*
> The `bianca-card-flow` Skill loads automatically and tells you the flow logic.

---

## 0. Prereqs (already true)
- Claude Code installed and signed in on the mini.
- Airtable + Gmail connected in Claude Code.
- Chrome installed on the mini.

## 1. Get the code
```bash
git clone <this-repo-url>          # or: git pull, if already cloned
cd <repo>
```
The Skill at `.claude/skills/bianca-card-flow/SKILL.md` loads automatically when
Claude Code runs in this repo.

## 2. Prep the BD Mastersheet
In Airtable, on the BD Mastersheet Bianca built, make sure these fields exist
(add any missing — see `BIANCA_CARD_FLOW.md` §3):
`Source, Card Image, My Note, Channel, Draft Message, Status, Sent Message,
Sent At`. `Status` options: `Drafted, Sent, Cancelled, Send failed`.

## 3. Create the Telegram bot (~2 min)
1. In Telegram, message **@BotFather** → `/newbot` → follow prompts.
2. Copy the **bot token** it gives you.
3. Message your new bot once, then note **your own chat ID** (send `/start`; the
   bot code below prints the chat ID of whoever messages it — lock it to yours
   so only you can drive Bianca).

## 4. Set secrets (local, never commit)
Create `bianca/.env` (this folder is gitignored):
```
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_ALLOWED_CHAT_ID=xxxxx     # your chat ID — reject everyone else
```

## 5. WhatsApp Web on the mini (Phase 2)
Choose the sender:
- **Recommended: `whatsapp-web.js`** — a Node library that runs its own
  Chromium and persists the login. Ask Bianca (Claude Code) to scaffold it in
  `bianca/`, then run it once and **scan the QR** shown in the terminal with
  your phone's WhatsApp (Linked Devices). Session persists after that.
- Alternative: drive your existing logged-in Chrome via Playwright to
  `web.whatsapp.com`. More fragile; only if you prefer not to add Node deps.

Test a send to your own number **before** wiring it into the flow.

## 6. Build & run
A working **scaffold** already exists — `bianca/bot.js` + `bianca/package.json`.
It's a tested *shape*, not verified end-to-end, so run it on the mini and adjust
(search `bot.js` for `TODO(mini)`).

How it splits the work on the mini:
- **`bot.js` (Node):** Telegram in/out + approval buttons + WhatsApp Web send.
- **Claude Code (`claude -p`, loads this Skill):** OCR, Airtable record,
  drafting, Gmail send. The bot shells out to it, so your Claude Code login and
  connectors stay the only place holding Airtable/Gmail creds.

```bash
cd bianca
cp .env.example .env      # fill in token, your chat id, REPO_DIR
npm install
npm start                 # first run prints the WhatsApp QR — scan it
```

Then just talk to Claude Code on the mini to iterate:
> *"Run bianca/bot.js, send a test card in Telegram, and fix any TODO(mini)
> spots — confirm `claude -p --output-format json` returns what the bot expects,
> and that a WhatsApp send to my own number works."*

## 7. Test end-to-end
1. Photo a real card in Telegram with a caption ("warm lead, mention the pilot,
   WhatsApp").
2. Confirm: row appears in the Mastersheet, draft comes back in Telegram.
3. Tap ✅ → confirm the message sends and the row flips to `Sent`.

## 8. Keep it running
Run the bot as a background service so it survives reboots (e.g. a `launchd`
`LaunchAgent` on macOS, or `pm2 start`). Ask Bianca to set this up once the
manual test passes.

---

### Notes
- Secrets live only in `bianca/.env` on the mini — never commit them.
- WhatsApp automation = low-volume 1-to-1 BD follow-ups only (ToS + ban risk).
- If the WhatsApp Web login drops, re-run the sender and re-scan the QR.
