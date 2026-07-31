# Bianca — Business Card → Follow-up Flow (Build Spec)

Owner: Tina · Agent: **Bianca** (BD agent) · Last updated: 2026-07-31

Bianca captures a business card from the phone, records the contact in the BD
Mastersheet, drafts a customised follow-up, waits for one-tap approval, and
sends it by **WhatsApp or email**.

---

## 1. Design decisions (locked)

| Decision | Choice |
|---|---|
| Capture + approval surface | **Claude app on phone** (attach card photo + type prompt) |
| Approval | **Approve every send** — nothing leaves without a tap |
| BD Mastersheet | **Airtable** — the base Bianca already built |
| Email send | **Gmail** (cloud connector) |
| WhatsApp send | **Chrome / WhatsApp Web on the Mac mini** (logged-in session) |
| Cross-device hand-off | **Airtable is the bridge** (approved rows queue for the Mac mini) |

### Why this shape
Almost everything Bianca does is cloud (OCR, Airtable, Gmail, drafting), so the
Claude app alone handles capture → record → draft → approve → **email**.
WhatsApp-via-Chrome can only run on the logged-in Mac mini, so the **send step
for WhatsApp** hands off to Bianca on the Mac mini via an Airtable queue.

---

## 2. End-to-end flow

```
📱 Claude app (cloud)              📊 Airtable (BD Mastersheet)        🖥️ Bianca on Mac mini
──────────────────────            ────────────────────────────        ──────────────────────

1 Snap/upload card photo
  + caption:
  "hot lead, mention the
   pilot, WhatsApp"

2 OCR extracts:
  name, company, title,
  phone, email, website
  + parses intent
  (tone / channel / hook)

3 Write / update row  ──────────▶  Contact recorded
  (dedupe on email/phone)          status: "Drafted"

4 Draft follow-up in
  your voice (card + caption
  + hook). Email = subject+body,
  WhatsApp = shorter + warmer

5 Send draft back to phone
  [✅ Send] [✏️ Edit] [❌ Cancel]

6 You tap ✅
   ├─ EMAIL  ───────────────────▶  send via Gmail now
   │                                status: "Sent"
   └─ WHATSAPP ─────────────────▶  status: "Ready · WhatsApp"  ──▶ 7 Mac mini sees the row
                                    (approved message stored)          drives Chrome/WhatsApp
                                                                        Web, sends message
                                    status ◀───────────────────────    8 writes back "Sent"
                                    "Sent" + channel + timestamp           + logs sent copy
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
| My Note | long text | your caption/instruction |
| Channel | single select | `Email` / `WhatsApp` |
| Draft Message | long text | proposed follow-up (+ subject for email) |
| Status | single select | `Drafted` → `Ready · WhatsApp` → `Sent` (also `Cancelled`) |
| Sent Message | long text | exact copy that went out |
| Sent At | date/time | timestamp |

`Status` doubles as the follow-up tracker and the Mac mini's send queue.

---

## 4. Component checklist

| Piece | Status | Action |
|---|---|---|
| Vision OCR | ✅ built-in | Bianca reads card images |
| BD Mastersheet | ✅ exists | add the working fields above |
| Gmail send | ✅ connected | email follow-ups |
| **Bianca as a Skill** | ⬜ to build | pins her voice, rules, mastersheet ID so every fresh app session *is* Bianca (see §5) |
| **Chrome + WhatsApp Web on Mac mini** | ⬜ to set up | log in once (QR); keep session alive |
| **Mac mini queue-watcher** | ⬜ to build | polls Airtable for `Ready · WhatsApp`, sends via Chrome, marks `Sent` (see §6) |

---

## 5. Bianca Skill (makes any session behave as Bianca)

Because each Claude-app session starts fresh, Bianca's identity must live in a
Skill that auto-loads. It should contain:

- **Identity + voice** — Tina's BD tone; warm, concise, no corporate filler.
- **Mastersheet pointer** — the Airtable base ID + table + field names.
- **OCR rules** — required fields; flag low-confidence values (handwriting) for
  correction before saving.
- **Dedupe rule** — match on email, else phone; update existing row instead of
  creating a duplicate.
- **Drafting rules** — email = subject + body; WhatsApp = shorter, warmer, no
  subject; always weave in the caption's hook.
- **Channel rule** — use the channel named in the caption; else email if an
  email exists, else WhatsApp.
- **Approval rule** — never send without an explicit ✅; WhatsApp sends are
  queued to Airtable (`Ready · WhatsApp`), not sent from the app session.

---

## 6. Mac mini WhatsApp sender (queue-watcher)

Runs continuously on the Mac mini:

1. Poll Airtable every ~30–60s for rows where `Status = Ready · WhatsApp`.
2. For each, open Chrome/WhatsApp Web (or `whatsapp-web.js`), go to the
   contact's number, send `Draft Message`.
3. On success: set `Status = Sent`, copy `Draft Message` → `Sent Message`,
   stamp `Sent At`.
4. On failure (not logged in, number invalid): set `Status = Send failed` and
   note the reason so it surfaces on the phone.

### Honest caveats for WhatsApp-via-Chrome
- **Unofficial** — automating WhatsApp Web is against WhatsApp ToS. Low-volume
  1-to-1 BD follow-ups are low-risk; do **not** use it for mass sending (ban risk).
- **Session upkeep** — the WhatsApp Web login drops occasionally and needs a
  re-scan on the Mac mini.
- **Fragile to UI changes** — WhatsApp web updates can break automation; expect
  occasional maintenance.
- **Upgrade path** — if volume grows, switch WhatsApp to the **official Cloud
  API** (Meta Business account + sender number). Then WhatsApp can send straight
  from the cloud session and the Mac mini is no longer needed for sending.

---

## 7. Rollout

1. **Phase 1 — email only (today).** Bianca Skill + Airtable fields. Capture,
   record, draft, approve, send email. Fully cloud, nothing on the Mac mini yet.
2. **Phase 2 — WhatsApp via Chrome.** Log Chrome into WhatsApp Web on the Mac
   mini; add the queue-watcher. Approve on phone → Mac mini sends.
3. **Phase 3 (optional) — background follow-ups.** Bianca auto-nudges day-3
   non-repliers (still approve-every-send), and/or move WhatsApp to the official
   Cloud API to drop the Mac-mini dependency.
