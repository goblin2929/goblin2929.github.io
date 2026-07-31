Run the monthly bookkeeping close for Novastacks AI Pte Ltd using the `monthly-bookkeeping-controller` skill.

This is an UNATTENDED scheduled run (launchd, 1st of the month, ~07:00). There is no human present to answer prompts, so behave accordingly:

- Run the skill end to end: preflight → determine scan range → scan both Gmail inboxes → dedupe against Airtable → insert verified new records → mirror PDFs to the local Google Drive folder → 365-day drift audit → build the digest.
- AUTO-APPLY only the clearly-safe actions: inserting brand-new, deduped invoice records into Airtable, and mirroring their PDFs into the local Drive folder.
- Do NOT auto-apply anything that needs judgment — moving a vendor between the active / passive / cancelled lists, editing the skill's embedded subscription tables (Step 10), or reclassifying a price change. Collect all of those under a "Needs your confirmation" section instead.
- Do NOT pause for a Y/N. There is nobody to answer.

At the END, send the digest by email via the Gmail MCP:
- To: __BOOKKEEPING_EMAIL__
- Subject: Novastacks monthly bookkeeping — <the month/year of the period just closed>
- Body (plain text / inline, no attachments): the full digest in the skill's order —
  URGENT flags first (surprise charges from cancelled vendors), then invoices recorded this period + SGD total, net-new vendors discovered, likely-cancelled vendors, price changes detected, missing recurring invoices to chase, and finally the "Needs your confirmation" section listing every proposed change so you can reply Y/N by hand.
- Also print the full digest to stdout so it is captured in the run log.

Robustness:
- If any MCP (Gmail, Airtable, Google Drive) is disconnected, note it at the TOP of the email and continue with whatever is available. Do not halt.
- Treat the email as the deliverable. If the email cannot be sent, make the failure loud in stdout (print "EMAIL FAILED" and the reason) so it is obvious in the log.
- Keep the digest terse — roughly one screen.
