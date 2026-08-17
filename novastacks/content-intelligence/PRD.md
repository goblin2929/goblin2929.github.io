# PRD — Scrape-Once Content Store & Competitive Research System

> **Rev 5 — 17 Aug 2026.** Restructured as a PRD around Tina's framing: scraping already happens all over the stack — the missing piece is that its output is used once and thrown away, unseen and unreusable. This system stores everything scraped (screenshots included) in one database, tags it with a lean content taxonomy, and makes it queryable and reusable by every human and agent afterward. **Scrape once, use many times.** Storage is SQLite with full-text search; a small local web UI browses, searches, and diffs it; the monthly competitor refresh (deterministic selector + Playwright capture, from Rev 4) becomes one scheduled user of the same store. Full earlier revisions are in this file's git history.

---

## 1. Problem

Novastacks scrapes constantly — prospect audits, rival studies, citation diagnostics, social listening — and does monthly competitive strategy work on top. Five problems keep recurring:

1. **Scraped content is used once and discarded.** Every skill scrapes, uses the result, and throws it away. There is no visibility into what was captured and no reuse — the same rival pages are re-scraped by different skills in the same week, re-paying the time and re-rolling the anti-bot dice each time.
2. **Scraping gaps become hallucinated answers.** On-demand scraping silently misses pages (anti-bot walls, timeouts, unrendered JavaScript). Nothing forces the gap to be visible, so the AI fills it from general knowledge of the brand — and the analysis contains confident claims about pages that were never actually read.
3. **The SEO APIs never see page content.** Ahrefs, GSC, and DataForSEO return numbers — rankings, traffic, backlinks. Any past claim about *what a competitor's page says* that traces only to those APIs was inferred, not read.
4. **No history.** Because nothing is kept, the questions that matter most for strategy — *what changed this month, what started working* — are unanswerable at any price. Past versions of a page, once gone, cannot be bought back.
5. **Claims aren't defensible.** When a client pushes back ("their site doesn't say that"), there is no dated evidence — no stored page, no screenshot — of what the site showed on the day we analyzed it.

## 2. What we're building

A **database that keeps everything we scrape, and makes it reusable.** Scraping stays exactly where it is today — skills scrape on demand whenever work needs it. The change: every scrape's output is saved into one store as a matter of course — the screenshot, the raw HTML, the extracted text — tagged with what it is (client, site, page type, which skill captured it and why), dated, and fingerprinted. A small web UI lets a human browse and *see* what was captured, search it, and diff any page across time. Agents query the same database, and before any skill scrapes a URL it checks the store first — if a fresh-enough copy exists, it reuses it instead of hitting the web again. On top of the store, a monthly scheduled refresh keeps each client's competitive set current, with the pages chosen by performance data (AI citations, traffic, rankings), not by hand. Every analysis claim traces to a stored version with a date.

Multi-project from day one: projects are rows, not code. Example project: GoFreight vs. CargoWise, Magaya, Descartes, FreightPOP.

## 3. Users & user stories

Primary users: every scraping skill (prospect-audit, client-01-diagnosis, citation-diagnostics, social listening, rival studies), Tina and the strategist/AM agents (analysis), the BD agent (pitches).

**US-1 — Scrape once, reuse everywhere.** As any skill or agent, I want to query previously captured pages before scraping, so I don't re-scrape, re-pay, and re-risk anti-bot walls for content we already have. *Done when:* a second run over the same pages within the staleness window hits the store, not the web.

**US-2 — Competitor messaging watch.** As the GoFreight account manager, I want a monthly summary of what each competitor changed on their key pages, so my client update says "Descartes rewrote their pricing page — here's what moved" instead of generic commentary. *Done when:* after a monthly refresh, "what changed across the competitor set?" returns a page-cited summary in under 10 minutes.

**US-3 — Content gap analysis.** As the content lead, I want Claude to read a project's stored pages (client + competitors) and name the buyer questions competitors answer that the client doesn't. *Done when:* the analysis names missing topics, each citing the stored competitor page that covers it.

**US-4 — BD pitch evidence.** As Bianca preparing a first meeting, I want the prospect's audit scrapes stored and browsable, so the pitch contains observations backed by pages I can show. *Done when:* the diagnosis cites at least three stored-page comparisons, each openable in the UI.

**US-5 — Citation diagnosis.** As the strategist running an AI-citation diagnostic, I want to compare the exact content of a competitor page that AI engines cite against the client page that isn't cited. *Done when:* every "fix this page" recommendation cites a stored competitor page version as its evidence.

**US-6 — Claim provenance.** As Tina signing off a client report, I want every "competitor X says/changed Y" claim traceable to a dated stored version — text and screenshot — so pushback can be answered with evidence even if the live site has changed. *Done when:* any claim traces to URL + capture date + version in under a minute, findable in the UI.

**US-7 — New-client baseline.** As the onboarding workflow, I want a day-one capture of the client's site and competitive set, so every future report measures drift against a fixed starting point. *Done when:* onboarding includes the first selection + capture run, and month-3 reports can diff against month 0 in the UI.

## 4. Goals & success criteria

| Goal | Measure |
|---|---|
| Reuse, not re-scrape | A repeat request inside the staleness window is served from the store; store-hit vs. web-fetch is visible in run output |
| See what was captured | Every capture browsable in the UI — screenshot, text, provenance — within a minute of the scrape |
| No hallucinated page claims | 100% of page-content claims cite a stored version; zero claims about uncaptured pages |
| Gaps always visible | Every failed capture stored with status, flagged in the UI, surfaced as "not captured" in analysis |
| History accumulates | Versions never overwritten; month-vs-month diff in the UI from month 2 |
| Human self-serve | Tina answers "what did their pricing page say in June?" alone, in the UI, no Claude session |
| Lean cost | Build ~2–2.5 weeks; run ~$5–20/mo per client; selection API calls cost cents |
| Directly readable | A project's markdown (~300–500 pages ≈ 400k–1M tokens) loads into a Claude context via one query |

The bar Tina set: hit ~95% of the goals with the simplest system that does so.

## 5. Non-goals

Deliberately cut — each solved a problem we don't have at this scale:

- **No embeddings, no vector search, no chunking, no rerankers.** Full-text search (FTS5) plus direct reading covers retrieval at this size. Semantic-search machinery returns only via §12 triggers.
- **No ontology project, no AI classification in v1.** The taxonomy is a handful of structured fields; page type is derived from URL patterns deterministically. AI-assisted tagging is a §12 candidate, not a v1 feature.
- **No hosted multi-tenant SaaS, no auth or user management.** One SQLite file and one read-only local web app on the Mac mini.
- **No real-time crawling.** Capture happens when skills scrape (Path A) and monthly on schedule (Path B). Sub-day monitoring is a §12 trigger.
- **Not a replacement for the rank/traffic APIs.** Those provide the numbers; this stores the page content. They feed the selector; they don't overlap.

## 6. Functional requirements

Every FR carries its acceptance check in italics.

### Ingestion Path A — capture-on-scrape (primary)

- **FR-1** Whenever a skill scrapes, its artifacts are written to the store as a matter of course: screenshot image (file on disk, path in DB — screenshots are first-class), raw HTML when fetched, extracted markdown, URL, timestamp, content hash, fetch status, plus which skill captured it (`capture_source`) and why (`capture_purpose`). *Check: run one real scraping skill; every page it touched has a version row with screenshot path and source/purpose filled.*
- **FR-2** The wiring lands once, in the shared web-scraping skill, so every consumer inherits capture-on-scrape without per-skill changes. *Check: a skill that routes through web-scraping stores its captures with zero skill-specific code.*
- **FR-3 (reuse rule)** Before scraping a URL, skills query the store. If a version exists fresher than the per-purpose staleness threshold (default 30 days for strategy work; configurable per purpose), the stored copy is used instead of re-scraping. A miss or stale hit triggers a scrape whose result is itself stored. *Check: scrape a URL twice in one day — the second run returns the stored version and performs no web fetch; force staleness and it re-scrapes and stores a new version.*
- **FR-4 (taxonomy)** Every stored item carries: project/client, site/domain, `page_type` derived deterministically from URL pattern (`pricing | product | blog | comparison | home | about | other`), `capture_source`, `capture_purpose`, and free-form tags. Projects/sites are auto-created by domain on first capture if absent. *Check: stored items from a fresh domain acquire site + page_type without manual setup; no LLM call occurs in typing.*

### Ingestion Path B — scheduled competitor refresh (secondary)

- **FR-5** A deterministic selector derives each competitor site's URL list from four signals, in priority order: (1) pages cited by AI engines in Novastacks' own citation testing (WorkDuo runs) — always included; (2) top pages by estimated organic traffic, descending to ~80% cumulative coverage (configurable); (3) pages ranking top-10 for the client's tracked keyword panel; (4) strategic pages by URL pattern (homepage, `/pricing`, `/product*`, `/about`). Every URL carries a machine-written reason. No LLM in selection. *Check: fixed API fixtures → identical list on repeated runs; no row lacks a reason.*
- **FR-6** No fixed page count exists; sites under ~30 pages (sitemap count) are taken whole; the client's own pages are selected on GSC real data, never estimates; if a project exceeds the 1M-token budget, lowest-signal pages are dropped (cited/strategic never first) with every drop recorded and its reason. *Check: small-site fixture yields full sitemap; oversized fixture produces drop records; brand-site reasons reference GSC.*
- **FR-7** The selector consumes one provider contract — `url, estimated_traffic, panel_rankings`. Default adapter: DataForSEO (`dataforseo_labs/google/relevant_pages/live`; `dataforseo_labs/google/ranked_keywords/live` filtered to the panel). Alternate: Ahrefs. The provider is pinned per project and recorded on every selection run; raw API responses are stored with the run. All rival traffic figures are labeled `est., <provider>` everywhere; GSC numbers may be stated as measured. *Check: adapter swap changes no selector code; mismatched provider fails loudly; any selected URL's raw justification is queryable; no unlabeled rival numbers in UI or output.*
- **FR-8** The monthly refresh re-runs the selector, records adds/drops with reasons, and captures the list via the same pipeline as Path A (Playwright rendered fetch, trafilatura markdown, screenshot, hash over normalized markdown; robots.txt honored, per-domain rate limits, real user agent). Human role: skim-and-approve the annotated list once per project, then a monthly glance at adds/drops. *Check: month-2 run stores a delta; approval is a recorded field; a captured URL yields HTML + markdown + screenshot + hash.*
- **FR-9** Screaming Frog imports via an adapter: a human drops an SF export (CSV + rendered HTML) in a folder; the importer writes the same version rows stamped `crawler: screaming_frog`. *Check: imported versions are indistinguishable to UI and analysis except by crawler stamp.*

### Storage

- **FR-10** Single SQLite file per deployment on the Mac mini; screenshots as files on disk with paths in the DB. Data model in §8. *Check: migration creates all tables + FTS index from empty; system state = one DB file + one screenshot directory + code.*
- **FR-11** Versions are never overwritten or deleted; every capture appends. Failures (404, timeout, anti-bot) are stored with status and never block a run. *Check: no UPDATE/DELETE against document_versions in the codebase; a run with one dead URL completes with that URL's failure row present.*
- **FR-12** Every version carries provenance: `crawler`, `adapter_version`, `fetched_at`, `content_hash`, `fetch_status`, `capture_source`, `capture_purpose`, and (Path B) a link to its selection run — so a real content change is always distinguishable from a change of fetcher, provider, or capturing skill. *Check: any version row answers who captured it, how, when, and why.*
- **FR-13** An FTS5 full-text index covers version markdown; search filterable by project, site, month, and taxonomy fields. *Check: a phrase known to exist in one stored page returns that page; filtering by `page_type=pricing` narrows correctly.*

### UI (read-only local web app)

- **FR-14** A small web app on the Mac mini (FastAPI + server-rendered pages, own port beside the existing Control Room; no build tooling) provides project → site → page → version-history browsing, **with the screenshot displayed in the page view**. *Check: three clicks from the project list reach any page's version list; the screenshot renders.*
- **FR-15** Per page, a month-to-month diff view renders what changed between any two versions (markdown-level). *Check: edit a fixture page between runs; the diff shows exactly that edit.*
- **FR-16** Search and filters: FTS box plus taxonomy filters (project, site, page type, capture source, month). Results link to the stored version. *Check: searching a competitor slogan lands on their stored page; filters narrow it.*
- **FR-17** Every version displays provenance (capture date, hash, fetch status, crawler, source skill, purpose); failed captures are visibly flagged "not captured." The UI is read-only, unauthenticated, local-network only, and never writes to the database. *Check: dead-URL fixture shows a flagged entry; UI code path contains no write statements.*

### Agent interface

- **FR-18** Agents and skills query the same SQLite file via SQL or a thin CLI exposing six operations, one line each: `lookup <url> [--max-age]` (freshest version or miss — the reuse rule's primitive), `list <project> [--month]` (pages with status), `get <version>` (markdown/HTML/screenshot path), `diff <url> <month-a> <month-b>`, `search <query> [filters]`, `export <project> <month>` (all markdown for loading into a Claude context). *Check: each operation runs from a shell and returns in under a second at reference scale (~500 pages/month/project).*

### Analysis (the only layer where AI appears)

- **FR-19** An analysis run opens with a completeness statement produced by query — "N of M selected pages captured; these failed: …" — then loads markdown via `export`/`get`. *Check: every analysis output opens with the completeness statement.*
- **FR-20** Every page-content claim cites URL + capture date + version. No citation, no claim. Claims come from stored versions, never a live fetch or the model's general knowledge of a brand. *Check: spot-audit finds zero uncited page-content claims.*
- **FR-21** Pages stored with a failure status are reported as **"not captured"** — never described, never inferred. *Check: analysis over the dead-URL fixture names it as not captured.*
- **FR-22** Counts, URL lists, and change lists come from SQL, never from asking an LLM to count. Repeated questions become saved prompts/queries per project so analysis quality compounds. *Check: numeric statements match direct query results.*

## 7. Non-functional requirements

- **NFR-1 Deterministic outside analysis:** selection, capture, taxonomy typing, and reuse decisions are plain code — same inputs, same outputs. No LLM anywhere but analysis.
- **NFR-2 Auditable:** raw HTML beside every markdown extraction; raw API responses beside every selection; screenshots beside every capture; provenance on every row.
- **NFR-3 No silent caps:** anything bounded (token-budget drops, fetch failures, staleness fallbacks, small-site rule) is recorded where both the UI and analysis surface it.
- **NFR-4 Existing infrastructure only:** launchd on the Mac mini for the monthly refresh; the DB file and screenshot directory join the mini's existing backup routine; one local web process, no new services.
- **NFR-5 Multi-project by data:** a new client is new rows (project, sites, panel, provider pin); ad-hoc captures auto-create their project/site rows; zero code changes per client.

## 8. System design

```text
            ON-DEMAND SCRAPES                     MONTHLY REFRESH
     (prospect audit, rival study,          select.py + provider adapter
      citation diagnostic, listening)        (4 signals, reasons, no LLM)
                  │                                     │ approved list
                  ▼                                     ▼
        ┌─────────────────────────────────────────────────────┐
        │  CAPTURE (shared): Playwright fetch + screenshot    │
        │  + trafilatura markdown + hash + taxonomy typing    │
        │  — reuse rule first: store hit? → no web fetch —    │
        └──────────────────────────┬──────────────────────────┘
                                   ▼
                    SQLite (one file, FTS5) + screenshot dir
                                   │
              ┌────────────────────┼─────────────────────┐
        UI (read-only)       Agent CLI/SQL          ANALYZE (Claude)
        browse · diff ·      lookup · list · get    reads via export;
        search · screenshots · diff · search ·      every claim cites
        · provenance         export                 URL+date+version
```

**Data model (SQLite):**

```text
projects          id, slug, provider_pin, keyword_panel, cadence
sites             id, project_id, name, role (brand|competitor|reference), domain
documents         id, site_id, url, page_type (pricing|product|blog|comparison|home|about|other)
document_versions id, document_id, snapshot_month, raw_html, markdown, screenshot_path,
                  content_hash, http_status, fetched_at, fetch_status (ok|failed:<reason>),
                  crawler, adapter_version, capture_source, capture_purpose, tags,
                  selection_run_id (nullable — Path B only), changed_since_previous
selection_runs    id, project_id, month, provider, approved_by, approved_at
selection_items   id, selection_run_id, url, reason, signal, dropped, drop_reason
selection_raw     id, selection_run_id, provider_endpoint, response_json
fts_versions      FTS5 virtual table over document_versions.markdown
```

The document/version split is the load-bearing modeling decision: a page keeps one identity across time (`documents`), every capture appends an immutable version — which makes history, diffs, reuse lookups, and provenance queries one-JOIN simple. Both ingestion paths write the same rows; Path B additionally links its selection run.

Sizing: monthly refresh ≈ 300–500 pages/project (selector-derived, ~15 for a small rival to ~50–70 for a large one, × 6–8 sites); markdown ≈ 400k–1M tokens per project — loadable into a Claude context via one `export`, which is why analysis needs no retrieval machinery beyond FTS.

## 9. Milestones (~2–2.5 weeks total)

Each milestone ends with something demonstrable:

- **M1 — Store + capture-on-scrape (3–4 days).** Schema migrations; shared capture path wired into the web-scraping skill; taxonomy typing. Demo: run one real prospect-audit scrape — every page it touched is in the DB with screenshot, markdown, hash, source, purpose; one dead URL stored as failed.
- **M2 — UI (3–4 days).** Browse, version history, screenshot view, diff, FTS search + taxonomy filters over stored items. Demo: Tina opens the UI, sees yesterday's scrape's screenshots, searches a phrase, filters by page type.
- **M3 — Selector + first monthly refresh (2–3 days).** `select.py` + DataForSEO adapter populate selection tables for GoFreight; approved list captured through the same pipeline; launchd schedules it. Demo: reason-annotated list approved (recorded); full competitor set stored; adds/drops delta on the second run.
- **M4 — Reuse rule + first analysis (1–2 days).** `lookup` live in the web-scraping skill; then ask: *"What are competitors promising around implementation?"* Demo: a repeat scrape hits the store with no web fetch; analysis output opens with the completeness statement and every claim cites URL + capture date + version. **This is the acceptance test.**
- **M5 — SF importer (1 day, can trail).** Manual Screaming Frog export lands as version rows with its own crawler stamp.

Order constraints: the schema freezes at M1 (both ingestion paths and the SF importer write to it); the first Path-B selection is human-approved before the first refresh spends fetches on it.

Three-month proof (the compounding claim): the M4 question answered against a *historical* month; a "what changed this quarter" diff read; the selection adds/drops log showing which pages the market started rewarding; and a measurable share of skill runs served from the store instead of the web.

## 10. Costs

- **Build:** ~2–2.5 weeks — store + capture wiring 3–4 days; UI 3–4 days; selector + adapter + first refresh 2–3 days; reuse rule + analysis wiring 1–2 days; SF importer 1 day. (The database and UI add roughly a week over a files-only design; that is the price of seeing, searching, and reusing captures, stated plainly.)
- **Running:** ~$5–20/mo per client — analysis tokens dominate; selection API calls are cents per run (DataForSEO pay-per-call: ~$0.012/task + $0.00012/item); SQLite, screenshots, and one local web process cost nothing. Reuse *reduces* today's scraping spend: repeat lookups stop hitting the web.
- **Human time:** ~5 min/month per project — approve the selection diff, glance at the failure list.
- Reference point: the original full-platform design was estimated at ~$35–70k to build plus $50–270/mo infrastructure. This delivers the reuse loop and the same research answers at boutique scale for ~2–2.5 weeks of build.

## 11. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Anti-bot walls block captures | Retry with backoff; failures stored with status, flagged in UI, reported "not captured" in analysis; persistent blocks fall back to manual SF export; reuse rule reduces exposure by scraping less |
| Skills bypass the store (wiring adoption) | The capture + reuse wiring lands once in the shared web-scraping skill all scrapers already route through; a follow-up Ivy/stack-integrator pass audits stragglers after M4 |
| Provider estimate drift churns the refresh list | Provider pinned per project; estimates labeled `est., <provider>`; adds/drops recorded with reasons |
| New/small rivals invisible to data signals | Take-all fallback for sites under ~30 pages (FR-6) |
| DB/screenshot storage growth | Fine at reference scale (tens of MB text/month; screenshots on disk, paths in DB); if a project outgrows the repo pattern, HTML follows screenshots to file storage — the schema already isolates both columns |
| Stale reuse serves outdated content | Staleness thresholds are per-purpose and configurable (FR-3); `lookup` always reports the version's age; live-freshness needs can force a scrape, which is then stored |
| ToS exposure if capture is ever productized | Internal competitive research use only; explicit legal stance before any client-facing capture service |

## 12. Deferred: the scale-out platform

The compressed record of the original Rev 2 design (full spec in git history). Deferred, not rejected — what this PRD builds is its small, load-bearing center (document/version model, provenance, deterministic capture, one store for humans and agents); the deferred parts are scale machinery around it.

**Deferred components:** embeddings + pgvector hybrid search with reranking and a query router; AI enrichment (extracted topics, entities, typed claims for cross-site claim analytics); **AI-assisted tagging** on top of the v1 URL-pattern taxonomy; Postgres migration; hosted multi-tenant backend with auth; a client-facing product UI. Estimated ~$35–70k build, $50–270/mo infrastructure.

**Upgrade triggers — build a deferred component when its condition becomes true:**

1. A project needs more than ~2–3M tokens (~a few thousand pages) read per analysis → embeddings/hybrid search.
2. Clients (not just the team) need to log in and search → hosted backend + auth.
3. Questions span many client projects at once (industry benchmarks, pattern mining) → Postgres + enrichment.
4. Monitoring needs daily or sub-day crawl-and-diff freshness → crawl scheduler + alerting.
5. Systematic claim extraction/comparison across thousands of pages, or URL-pattern typing proves too coarse in practice → AI enrichment / AI-assisted tagging.

When a trigger fires, the accumulated version history — the thing this system exists to protect — migrates as-is: the document/version schema is the ingestion format the platform was designed around.
