# Bianca — Mac mini setup playbook (Claude Code Remote Control)

Run these on the **Mac mini**. Tina drives Bianca from her phone via **Claude
Code Remote Control** — she attaches a card photo in the Claude app, Claude Code
downloads it to the mini, and Bianca (this local session, with the Skill) does
the rest: OCR → Airtable → draft → approve-in-chat → send (Gmail / WhatsApp Web).

No Telegram, no bot. Two things run on the mini:
1. **`claude remote-control`** — Bianca's brain, controlled from the phone.
2. **`bianca/wa-sender.js`** — a localhost WhatsApp Web sender Bianca calls on approval.

---

## 0. Prereqs
- Claude Code installed and signed in with a **full-scope `/login`** (Remote
  Control needs this — an API key alone won't work) on a Claude.ai plan.
- Airtable + Gmail connected in Claude Code.
- Chrome installed. Node 18+ installed.

## 1. Get the code
```bash
git clone https://github.com/goblin2929/goblin2929.github.io.git
cd goblin2929.github.io
git checkout claude/business-card-capture-flow-u7pk5n
```
The Skill at `.claude/skills/bianca-card-flow/SKILL.md` loads automatically when
Claude Code runs in this repo.

## 2. Prep the BD Mastersheet
On the BD Mastersheet Bianca built, ensure these fields exist (see
`BIANCA_CARD_FLOW.md` §3): `Source, Card Image, My Note, Channel, Draft Message,
Status, Sent Message, Sent At`. `Status` options: `Drafted, Sent, Cancelled,
Send failed`.

## 3. Start the WhatsApp Web sender (Phase 2 — skip if email-only to start)
```bash
cd bianca
cp .env.example .env          # set REPO_DIR to this repo's absolute path
echo "REPO_DIR=$(cd .. && pwd)" >> .env
npm install
node wa-sender.js             # prints a QR — scan: WhatsApp > Linked Devices
```
Leave it running (see §6). Test it once from another terminal:
```bash
curl -s localhost:8787/health          # {"ready":true} after you scan
curl -s -X POST localhost:8787/send -H 'content-type: application/json' \
  -d '{"phone":"<your own intl number, digits only>","text":"Bianca test ✅"}'
```

## 4. Turn on Remote Control (Bianca's brain)
In the repo root on the mini:
```bash
claude                        # run once, accept the workspace-trust dialog, then /exit
claude remote-control         # prints a session URL + QR; keep this running
```
On your **phone**: open the Claude app → **Code** tab → scan the QR (or pick the
session by name; green dot = online).

## 5. Use it
From your phone, in that session:
1. Attach the **business-card photo** + a caption
   (e.g. "hot lead, mention the AI pilot, WhatsApp").
2. Bianca OCRs it, writes the Airtable row, and shows you the **draft**.
3. Reply **"send"** (or "make it shorter", or "cancel"). On send she emails via
   Gmail or fires the WhatsApp sender, then logs the row.

## 6. Keep both alive across disconnects/reboots
Run each in its own `tmux` window so they survive you closing the terminal:
```bash
tmux new -s wa    'cd ~/goblin2929.github.io/bianca && node wa-sender.js'
tmux new -s bianca 'cd ~/goblin2929.github.io && claude remote-control'
```
For auto-start on reboot, wrap each in a `launchd` LaunchAgent. (Ask Bianca to
generate the plists once the manual flow works.) If the mini loses network,
Remote Control times out after ~10 min and reconnects automatically when it's back.

---

### Notes
- Secrets/login state stay on the mini: `.env` and `.wwebjs_auth/` are gitignored.
- WhatsApp automation = low-volume 1-to-1 BD follow-ups only (ToS + ban risk).
- If the WhatsApp login drops, restart `wa-sender.js` and re-scan the QR.
- Start **email-first** (skip §3) to prove the flow with zero WhatsApp risk.
