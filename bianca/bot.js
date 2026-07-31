/**
 * Bianca — business-card -> follow-up bot.  Runs on the Mac mini.
 *
 * Split of responsibilities:
 *   - THIS bot (Node):  Telegram in/out + approval buttons + WhatsApp Web send.
 *   - Claude Code ("Bianca"): OCR, Airtable record, drafting, Gmail send.
 *     The bot shells out to `claude -p` so it reuses your Claude Code login and
 *     the `bianca-card-flow` Skill. Airtable/Gmail creds stay inside Claude Code
 *     only; the one thing Claude Code can't do — drive local Chrome for
 *     WhatsApp — is done here via whatsapp-web.js.
 *
 * SCAFFOLD: this is a tested *shape*, not verified end-to-end. Run and adjust on
 * the mini. Search for TODO(mini) for the spots that need a real test.
 */

import 'dotenv/config';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import TelegramBot from 'node-telegram-bot-api';
import pkg from 'whatsapp-web.js';
import qrcode from 'qrcode-terminal';

const { Client, LocalAuth } = pkg;
const execFileAsync = promisify(execFile);

const {
  TELEGRAM_BOT_TOKEN,
  TELEGRAM_ALLOWED_CHAT_ID,
  CLAUDE_BIN = 'claude',
  REPO_DIR = process.cwd(),
} = process.env;

if (!TELEGRAM_BOT_TOKEN) throw new Error('Set TELEGRAM_BOT_TOKEN in bianca/.env');

// ---------------------------------------------------------------------------
// Pending approvals. In-memory is fine for one low-volume user; if the bot
// restarts mid-approval you just re-send the card. Persist to disk if you care.
// ---------------------------------------------------------------------------
const pending = new Map(); // token -> { record, chatId }
let tokenSeq = 0;
const nextToken = () => `d${++tokenSeq}`;

// ---------------------------------------------------------------------------
// The "brain": run Claude Code headless in the repo so the Skill loads.
// Returns whatever JSON the prompt asked Bianca to produce.
// ---------------------------------------------------------------------------
async function askBianca(prompt) {
  // --output-format json returns a wrapper; the final text is in `.result`.
  // TODO(mini): confirm your Claude Code version's flags/shape with `claude -p --help`.
  const { stdout } = await execFileAsync(
    CLAUDE_BIN,
    ['-p', prompt, '--output-format', 'json'],
    { cwd: REPO_DIR, maxBuffer: 1024 * 1024 * 10 },
  );
  const outer = JSON.parse(stdout);
  const text = outer.result ?? outer.text ?? stdout;
  return extractJson(text);
}

// Pull the first JSON object out of a text blob (models sometimes add prose).
function extractJson(text) {
  if (typeof text === 'object') return text;
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start === -1 || end === -1) throw new Error(`No JSON from Bianca:\n${text}`);
  return JSON.parse(text.slice(start, end + 1));
}

// Step 1-3: OCR + record in Airtable + draft. Returns the draft for approval.
async function captureAndDraft(imagePath, caption) {
  const prompt = [
    'Use the bianca-card-flow skill.',
    `A business card image is at: ${imagePath}`,
    `Tina's instruction (caption): "${caption || '(none)'}"`,
    'Do steps 1-3 of the skill: OCR the card, record/update the contact in the',
    'BD Mastersheet (dedupe on email then phone), and draft the follow-up.',
    'Do NOT send anything. Return ONLY minified JSON with keys:',
    '{"recordId","name","company","channel","toPhone","toEmail","subject","draft","flags"}',
    'where channel is "Email" or "WhatsApp", toPhone is full international format',
    '(digits only, no +), subject is "" for WhatsApp, and flags lists any',
    'low-confidence fields to double-check (empty array if none).',
  ].join(' ');
  return askBianca(prompt);
}

// Mark a row sent (used after the bot sends WhatsApp). Email send + logging is
// done inside Claude Code in sendEmail() below.
async function logSent(recordId, channel, sentText) {
  const prompt = [
    'Use the bianca-card-flow skill.',
    `In the BD Mastersheet, set record ${recordId}: Status="Sent",`,
    `Channel="${channel}", Sent Message=${JSON.stringify(sentText)}, Sent At=now.`,
    'Return ONLY JSON: {"ok":true}.',
  ].join(' ');
  return askBianca(prompt).catch(() => ({ ok: false }));
}

// Email path: let Claude Code send via the Gmail connector AND log the row.
async function sendEmail(record) {
  const prompt = [
    'Use the bianca-card-flow skill.',
    `Send the drafted email for record ${record.recordId} via Gmail to`,
    `${record.toEmail}. Subject: ${JSON.stringify(record.subject)}. Body:`,
    `${JSON.stringify(record.draft)}. Then set that row Status="Sent",`,
    'Channel="Email", Sent Message=(the body), Sent At=now.',
    'Return ONLY JSON: {"ok":true} or {"ok":false,"error":"..."}.',
  ].join(' ');
  return askBianca(prompt);
}

// ---------------------------------------------------------------------------
// WhatsApp Web (Chrome on the mini). Scan the QR once; LocalAuth persists it.
// ---------------------------------------------------------------------------
const wa = new Client({
  authStrategy: new LocalAuth({ dataPath: path.join(REPO_DIR, 'bianca', '.wwebjs_auth') }),
  puppeteer: { headless: true },
});
let waReady = false;
wa.on('qr', (qr) => {
  console.log('\nScan this with WhatsApp > Linked Devices:\n');
  qrcode.generate(qr, { small: true });
});
wa.on('ready', () => { waReady = true; console.log('WhatsApp Web ready.'); });
wa.on('disconnected', () => { waReady = false; console.log('WhatsApp Web disconnected — re-run to re-scan.'); });
wa.initialize();

async function sendWhatsApp(record) {
  if (!waReady) throw new Error('WhatsApp Web not ready (scan the QR / re-run).');
  const chatId = `${record.toPhone}@c.us`; // digits only, country code, no +
  // TODO(mini): optionally verify the number is registered:
  //   const id = await wa.getNumberId(record.toPhone); if (!id) throw ...
  await wa.sendMessage(chatId, record.draft);
}

// ---------------------------------------------------------------------------
// Telegram: receive a card photo + caption, present the draft, handle buttons.
// ---------------------------------------------------------------------------
const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: true });

const allowed = (msg) =>
  !TELEGRAM_ALLOWED_CHAT_ID || String(msg.chat.id) === String(TELEGRAM_ALLOWED_CHAT_ID);

bot.on('message', async (msg) => {
  try {
    if (!allowed(msg)) return; // ignore everyone but Tina
    if (msg.text === '/start') {
      return bot.sendMessage(msg.chat.id, `Hi, I'm Bianca. Send me a business card photo with a caption (e.g. "hot lead, mention the pilot, WhatsApp"). Your chat id: ${msg.chat.id}`);
    }
    if (!msg.photo) return; // only act on photos

    await bot.sendChatAction(msg.chat.id, 'typing');
    // Highest-resolution photo is the last entry.
    const fileId = msg.photo[msg.photo.length - 1].file_id;
    const link = await bot.getFileLink(fileId);
    const imgPath = path.join(os.tmpdir(), `card-${fileId}.jpg`);
    const res = await fetch(link);
    await fs.writeFile(imgPath, Buffer.from(await res.arrayBuffer()));

    const record = await captureAndDraft(imgPath, msg.caption || '');
    const token = nextToken();
    pending.set(token, { record, chatId: msg.chat.id });

    const flags = record.flags?.length ? `\n\n⚠️ Double-check: ${record.flags.join(', ')}` : '';
    const head = `*${record.name}*${record.company ? ` · ${record.company}` : ''}  —  _${record.channel}_`;
    const body = record.channel === 'Email' && record.subject
      ? `*Subject:* ${record.subject}\n\n${record.draft}`
      : record.draft;

    await bot.sendMessage(msg.chat.id, `${head}\n\n${body}${flags}`, {
      parse_mode: 'Markdown',
      reply_markup: {
        inline_keyboard: [[
          { text: '✅ Send', callback_data: `send:${token}` },
          { text: '✏️ Edit', callback_data: `edit:${token}` },
          { text: '❌ Cancel', callback_data: `cancel:${token}` },
        ]],
      },
    });
  } catch (err) {
    console.error(err);
    bot.sendMessage(msg.chat.id, `Something broke: ${err.message}`);
  }
});

bot.on('callback_query', async (q) => {
  const [action, token] = (q.data || '').split(':');
  const item = pending.get(token);
  await bot.answerCallbackQuery(q.id).catch(() => {});
  if (!item) return bot.sendMessage(q.message.chat.id, 'That draft expired — re-send the card.');
  const { record, chatId } = item;

  try {
    if (action === 'cancel') {
      pending.delete(token);
      await askBianca(`Use the bianca-card-flow skill. Set record ${record.recordId} Status="Cancelled". Return ONLY JSON: {"ok":true}.`).catch(() => {});
      return bot.sendMessage(chatId, '❌ Cancelled, nothing sent.');
    }

    if (action === 'edit') {
      // Ask for a tweak; the next text message re-drafts. Kept simple: capture
      // the next message from this chat as the edit instruction.
      await bot.sendMessage(chatId, 'Reply with the tweak (e.g. "shorter, drop the emoji").');
      bot.once('message', async (m) => {
        if (!allowed(m) || m.chat.id !== chatId) return;
        await bot.sendChatAction(chatId, 'typing');
        const redraft = await askBianca([
          'Use the bianca-card-flow skill.',
          `Re-draft the follow-up for record ${record.recordId} with this change:`,
          `"${m.text}". Keep the same channel. Update Draft Message on the row.`,
          'Do NOT send. Return ONLY JSON: {"recordId","name","company","channel","toPhone","toEmail","subject","draft","flags"}.',
        ].join(' '));
        const newToken = nextToken();
        pending.set(newToken, { record: redraft, chatId });
        const body = redraft.channel === 'Email' && redraft.subject
          ? `*Subject:* ${redraft.subject}\n\n${redraft.draft}` : redraft.draft;
        await bot.sendMessage(chatId, `${redraft.name} — _${redraft.channel}_\n\n${body}`, {
          parse_mode: 'Markdown',
          reply_markup: { inline_keyboard: [[
            { text: '✅ Send', callback_data: `send:${newToken}` },
            { text: '✏️ Edit', callback_data: `edit:${newToken}` },
            { text: '❌ Cancel', callback_data: `cancel:${newToken}` },
          ]] },
        });
      });
      return;
    }

    if (action === 'send') {
      pending.delete(token);
      await bot.sendChatAction(chatId, 'typing');
      if (record.channel === 'WhatsApp') {
        await sendWhatsApp(record);
        await logSent(record.recordId, 'WhatsApp', record.draft);
      } else {
        const r = await sendEmail(record);
        if (r && r.ok === false) throw new Error(r.error || 'Gmail send failed');
      }
      return bot.sendMessage(chatId, `✅ Sent via ${record.channel}. Logged in the Mastersheet.`);
    }
  } catch (err) {
    console.error(err);
    // TODO(mini): also set Status="Send failed" with the reason.
    bot.sendMessage(chatId, `Send failed: ${err.message}`);
  }
});

console.log('Bianca bot running. Waiting for a card in Telegram…');
