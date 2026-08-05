/**
 * Bianca — WhatsApp Web sender.  Runs on the Mac mini alongside `claude remote-control`.
 *
 * Why this exists: Bianca (the local Claude Code session) can do everything —
 * OCR, Airtable, drafting, Gmail — except drive Chrome to send WhatsApp. This
 * tiny local service keeps WhatsApp Web logged in (scan the QR once) and exposes
 * a localhost-only endpoint Bianca calls on approval:
 *
 *   curl -s -X POST http://127.0.0.1:8787/send \
 *        -H 'content-type: application/json' \
 *        -d '{"phone":"6591234567","text":"Hi ..."}'
 *
 * Keep it running (tmux / launchd). Bound to 127.0.0.1 — never exposed off-box.
 */

import 'dotenv/config';
import http from 'node:http';
import path from 'node:path';
import pkg from 'whatsapp-web.js';
import qrcode from 'qrcode-terminal';

const { Client, LocalAuth } = pkg;
const PORT = Number(process.env.WA_SENDER_PORT || 8787);
const REPO_DIR = process.env.REPO_DIR || process.cwd();

const wa = new Client({
  authStrategy: new LocalAuth({ dataPath: path.join(REPO_DIR, 'bianca', '.wwebjs_auth') }),
  puppeteer: { headless: true },
});

let ready = false;
wa.on('qr', (qr) => {
  console.log('\nScan with WhatsApp > Linked Devices > Link a Device:\n');
  qrcode.generate(qr, { small: true });
});
wa.on('ready', () => { ready = true; console.log(`WhatsApp Web ready. Sender on http://127.0.0.1:${PORT}`); });
wa.on('disconnected', () => { ready = false; console.log('WhatsApp disconnected — restart the sender to re-scan.'); });
wa.initialize();

const json = (res, code, obj) => {
  res.writeHead(code, { 'content-type': 'application/json' });
  res.end(JSON.stringify(obj));
};

http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/health') return json(res, 200, { ready });

  if (req.method === 'POST' && req.url === '/send') {
    let body = '';
    req.on('data', (c) => (body += c));
    req.on('end', async () => {
      try {
        if (!ready) throw new Error('WhatsApp not ready (scan QR / restart sender)');
        const { phone, text } = JSON.parse(body || '{}');
        if (!phone || !text) throw new Error('need {phone, text}');
        // Validate the number is on WhatsApp and get its canonical id.
        const numberId = await wa.getNumberId(String(phone).replace(/\D/g, ''));
        if (!numberId) throw new Error(`not registered on WhatsApp: ${phone}`);
        await wa.sendMessage(numberId._serialized, text);
        json(res, 200, { ok: true });
      } catch (e) {
        json(res, 400, { ok: false, error: e.message });
      }
    });
    return;
  }
  json(res, 404, { ok: false, error: 'not found' });
}).listen(PORT, '127.0.0.1', () => console.log(`Bianca WA sender listening on 127.0.0.1:${PORT}`));
