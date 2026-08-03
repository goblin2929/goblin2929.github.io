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
| Where Bianca runs | **Mac mini**, as a Claude Code session (has shell + Chrome) |
| Capture + approval surface | **Claude Code Remote Control** (Claude app on the phone drives the mini session) |
| Approval | **Approve every send** — nothing leaves without a reply |
| BD Mastersheet | **Airtable** — the base Bianca already built |
| Email send | **Gmail** (Bianca's connector) |
| WhatsApp send | **Chrome / WhatsApp Web on the Mac mini** (local sender) |

### Why Remote Control (no Telegram needed)
Claude Code **Remote Control** connects the Claude phone app to a `claude`
session running on the mini. When Tina attaches a card photo in the app, **Claude
Code downloads it onto the mini** and hands it to Bianca as a file. It's a full
*local* session (real shell + Chrome, not a cloud sandbox), works with the phone
on any network (outbound HTTPS only), and Tina approves in the same chat. So one
local session does everything — capture, OCR, Airtable, draft, approve, send —
with no bot and no external bridge.

> Earlier this spec used a Telegram bot, on the assumption the phone couldn't
> reach the mini. Remote Control is the purpose-built path and replaces it. Setup:
> `claude remote-control` on the mini → scan the QR in the Claude app's Code tab.
> The only local helper still needed is the WhatsApp Web sender (Chrome can't be
> driven by a cloud session; here it's the same local box, so it's simple).

---

## 2. End-to-end flow

```
📱 Phone (Claude app · Code)   ☁️ Airtable/Gmail        🖥️ Mac mini — Bianca (one local session)
──────────────────────────     ─────────────────       ──────────────────────────────────────────

1 Attach card photo
  + caption:
  "hot lead, mention
   the pilot, WhatsApp"  ─────────────────────────────▶ 2 Remote Control downloads the
                                                           image to the mini's disk

                                                         3 Bianca OCRs the card:
                                                           name, company, title,
                                                           phone, email, website
                                                           + parses intent

                          BD Mastersheet ◀─────────────  4 write / update row
                          (Airtable)                        (dedupe on email/phone)
                          status: "Drafted"

                                                         5 draft follow-up in
                                                           Tina's voice (card +
                                                           caption + hook)

6 Draft shown in chat  ◀──────────────────────────────  6 present draft, ask to approve
  reply "send"/edit/cancel ──────────────────────────▶ 7 on "send":
                          Gmail ◀──────────────────────    • EMAIL → Gmail connector
                                                           • WHATSAPP → local sender
                                                             (curl 127.0.0.1:8787)
                                                             → Chrome/WhatsApp Web
                          Mastersheet ◀────────────────  8 update row → "Sent"
                          "Sent" + channel + time            + log sent copy
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
| Claude Code (Bianca), full-scope `/login` | Mac mini | ✅ installed |
| Bianca **Skill** | repo → mini | ✅ this repo (`.claude/skills/bianca-card-flow/`) |
| `claude remote-control` running | Mac mini | ⬜ start + scan QR in Claude app |
| Airtable BD Mastersheet | cloud | ✅ exists (add fields above) |
| Gmail send | cloud | ✅ connected |
| Chrome + WhatsApp Web login | Mac mini | ⬜ scan QR once (`wa-sender.js`) |
| WhatsApp Web sender (`bianca/wa-sender.js`) | Mac mini | ✅ scaffolded — `npm install` + run |

---

## 5. Division of labour

- **Authored in this repo:** the Bianca **Skill**
  (`.claude/skills/bianca-card-flow/SKILL.md`), the **WhatsApp Web sender**
  (`bianca/wa-sender.js`), and the **setup playbook** (`bianca/SETUP.md`).
- **Done on the Mac mini:** `git pull`, `npm install` the sender + scan the
  WhatsApp Web QR, then `claude remote-control` and pair it in the Claude app.
  Test one card end-to-end from the phone. The WhatsApp Web login must be scanned
  on the mini.

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

1. **Phase 1 — email only.** Skill + Airtable fields + `claude remote-control`
   paired to the phone. Capture, record, draft, approve, send email.
2. **Phase 2 — WhatsApp via Chrome.** Run `wa-sender.js`, scan the WhatsApp Web
   QR on the mini. Approve in the Claude app → Bianca fires the local sender.
3. **Phase 3 (optional) — background follow-ups.** Bianca auto-nudges day-3
   non-repliers (still approve-every-send), and/or move WhatsApp to the official
   Cloud API.
