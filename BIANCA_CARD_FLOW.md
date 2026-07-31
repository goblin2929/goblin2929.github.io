# Bianca — Business Card → Follow-up Flow (Build Spec)

Owner: Tina · Agent: **Bianca** (BD agent, runs as Claude Code on the Mac mini)
Last updated: 2026-07-31

Bianca captures a business card from the phone, records the contact in the BD
Mastersheet, drafts a customised follow-up, waits for one-tap approval, and
sends it by **WhatsApp or email**.

---

## 1. Design decisions (locked)

| Decision | Choice |
|---|---|
| Where Bianca runs | **Mac mini**, as a Claude Code instance (has shell + Chrome) |
| Capture + approval surface | **Telegram** (phone → bot the mini watches) |
| Approval | **Approve every send** — nothing leaves without a tap |
| BD Mastersheet | **Airtable** — the base Bianca already built |
| Email send | **Gmail** |
| WhatsApp send | **Chrome / WhatsApp Web on the Mac mini** |

### Why Telegram (verified)
The phone's Claude Code app runs in Anthropic's **cloud**, and the account has
only one environment (`Default Cloud Environment`, anthropic_cloud). The Mac
mini is **not** a registered remote environment, so the phone app cannot open a
session on the mini. To get a card from the phone into Bianca-on-the-mini, the
mini must watch an outside channel. **Telegram is that channel**, and it lets
one process on the mini do everything — receive, draft, approve, and send
(including Chrome/WhatsApp Web) — with no cloud→mini hand-off.

---

## 2. End-to-end flow

```
📱 Phone (Telegram)        ☁️ Cloud (Airtable/Gmail)     🖥️ Mac mini — Bianca (Claude Code)
────────────────────       ─────────────────────────     ──────────────────────────────────

1 Send card photo
  + caption:
  "hot lead, mention
   the pilot, WhatsApp"  ───────────────────────────────▶ 2 Telegram bot receives it

                                                           3 Bianca (Claude Code) OCRs:
                                                             name, company, title,
                                                             phone, email, website
                                                             + parses intent

                           BD Mastersheet ◀──────────────  4 write / update row
                           (Airtable)                         (dedupe on email/phone)
                           status: "Drafted"

                                                           5 draft follow-up in
                                                             Tina's voice (card +
                                                             caption + hook)

6 Draft + buttons     ◀──────────────────────────────────  6 send draft to Telegram
  [✅ Send] [✏️ Edit]                                          with approval buttons
  [❌ Cancel]

7 Tap ✅              ────────────────────────────────────▶ 7 send now:
                           Gmail ◀────────────────────────    • EMAIL → Gmail
                                                              • WHATSAPP → Chrome/
                                                                WhatsApp Web
                           Mastersheet ◀──────────────────  8 update row → "Sent"
                           "Sent" + channel + time             + log sent copy
```

---

## 3. Mastersheet fields (add if missing)

Bianca's existing BD Mastersheet + these working fields:

| Field | Type | Purpose |
|---|---|---|
| Name / Company / Title | text | from card OCR |
| Phone / Email / Website | text | from card OCR |
| Source | single select | `Card scan` |
| Card Image | attachment | the original photo |
| My Note | long text | your Telegram caption/instruction |
| Channel | single select | `Email` / `WhatsApp` |
| Draft Message | long text | proposed follow-up (+ subject for email) |
| Status | single select | `Drafted` → `Sent` (also `Cancelled`, `Send failed`) |
| Sent Message | long text | exact copy that went out |
| Sent At | date/time | timestamp |

`Status` doubles as the follow-up tracker.

---

## 4. Component checklist

| Piece | Where | Status |
|---|---|---|
| Claude Code (Bianca) | Mac mini | ✅ installed |
| Bianca **Skill** | repo → mini | ⬜ this repo (`.claude/skills/bianca-card-flow/`) |
| Telegram bot token | @BotFather → mini | ⬜ 2 min |
| Telegram receive + approval buttons | Mac mini | ⬜ built on mini |
| Airtable BD Mastersheet | cloud | ✅ exists (add fields above) |
| Gmail send | cloud | ✅ connected |
| Chrome + WhatsApp Web login | Mac mini | ⬜ scan QR once |
| WhatsApp send (whatsapp-web.js or Chrome drive) | Mac mini | ⬜ built + tested on mini |

---

## 5. Division of labour

- **Authored in this repo (cloud session):** the Bianca **Skill**
  (`.claude/skills/bianca-card-flow/SKILL.md`) — her identity, voice, and the
  full flow logic — plus the **setup playbook** (`bianca/SETUP.md`).
- **Done on the Mac mini by Bianca (Claude Code):** `git pull` this repo, then
  follow the playbook — create the Telegram bot, install the WhatsApp bits,
  scan the WhatsApp Web QR, and test one card end-to-end. The Chrome/WhatsApp
  login and browser-driving must be built and tested on the mini.

---

## 6. Bianca Skill (what makes a mini session *be* Bianca)

See `.claude/skills/bianca-card-flow/SKILL.md`. It pins:
- **Identity + voice** — Tina's BD tone: warm, concise, no corporate filler.
- **Mastersheet pointer** — the Airtable BD Mastersheet + field names.
- **OCR rules** — required fields; flag low-confidence values for correction.
- **Dedupe rule** — match on email, else phone; update, don't duplicate.
- **Drafting rules** — email = subject + body; WhatsApp = shorter, warmer.
- **Channel rule** — use the caption's channel; else email if present, else WhatsApp.
- **Approval rule** — never send without an explicit ✅ in Telegram.

---

## 7. WhatsApp-via-Chrome — honest caveats

- **Unofficial** — automating WhatsApp Web is against WhatsApp ToS. Low-volume
  1-to-1 BD follow-ups are low-risk; do **not** mass-send (ban risk).
- **Session upkeep** — the WhatsApp Web login drops occasionally; re-scan on the mini.
- **Fragile to UI changes** — WhatsApp web updates can break automation.
- **Upgrade path** — if volume grows, switch to the official **WhatsApp Cloud
  API** (Meta Business account + sender number).

---

## 8. Rollout

1. **Phase 1 — email only.** Skill + Airtable fields + Telegram bot. Capture,
   record, draft, approve, send email.
2. **Phase 2 — WhatsApp via Chrome.** Log Chrome into WhatsApp Web on the mini;
   add the send step. Approve in Telegram → mini sends.
3. **Phase 3 (optional) — background follow-ups.** Bianca auto-nudges day-3
   non-repliers (still approve-every-send), and/or move WhatsApp to the official
   Cloud API.
