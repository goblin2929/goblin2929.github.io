# PRD — Content Intelligence (Beta): Scrape-Once Content Store & Competitive Research System

> **Rev 6.5 — 17 Aug 2026.** **Content inventory added (FR-31).** Field finding during the Novastacks test build: the ranked-keyword landscape showed stridec.com at 25 pages when the site's real published estate is 580 posts (~888 indexed) — a keyword-seeded landscape only sees what Google already ranks for tracked terms, which reproduces the exact blindness this system exists to remove ("never judge an AEO rival by ranked pages" — validated methods in `company/market-intel/sg-rival-content-map-2026-08.md`). New per-rival monthly inventory of the full published estate (sitemap / sitemap-index / blog-index crawl / WP REST, real titles) stored as its own entity `inventory_pages`; topic suggestions now discover from the inventory (what rivals publish) with ranked keywords as a performance overlay (what of it ranks); competitor overview shows published vs ranked vs captured counts. Schema freeze amended with one additive table. Estimate ~3.5–4 weeks.
> **Rev 6.4 — 17 Aug 2026.** Final pre-build audit fixes: `topics` / `suggested_topics` / `action_log` added to the §6 data model (matching the schema as built in M1); FR-28(c)'s suggestion clustering defined as a concrete SQL grouping by shared `ranking_url`; FR-28/29/30 assigned to milestones M2–M3 and the estimate revised to ~3–3.5 weeks; Path A labeled in the diagram; §4 scope line updated to read-plus-actions.
> **Rev 6.3 — 17 Aug 2026.** Human-in-the-loop UI actions added after mockup review: topic curation with business value + approve/dismiss of suggested topics (FR-28), per-page "Refresh content now" with staleness note (FR-29), per-competitor SEO overview + site structure (FR-30); UI is now read-plus-scoped-actions, not read-only. Also: stable per-page URLs with concurrent page details (FR-14) and multi-user access over the tailnet with WAL + per-device action log (FR-17). Approved mockup: `mockup/ui-mockup.html` (screens in `mockup/screens/`).
> **Rev 6.2 — 17 Aug 2026.** System ships as **Beta** (label carried in the UI header) — first internal release, iterated in production on real client projects. Cost section corrected: analysis runs on the existing Claude Code subscription; real dollar cost is under ~$1–2/mo per client.
> **Rev 6.1 — 17 Aug 2026.** Technical PM format. Adds the **landscape layer** — the selector's API data stored as first-class queryable data, with every competitor URL **mapped back to the client's own topics** via the keywords it ranks for — and **topic-triggered capture** (third ingestion path: pick a client topic, capture just the top competing pages). Three evidence rules now govern analysis: coverage claims cite the landscape dataset; content claims cite stored page versions; rank-cause statements stay observable-only. Rev 5 recentered the system on scrape-once/use-many with a SQLite store and local UI. Full earlier revisions are in this file's git history.

---

## 1. Overview & Background

Novastacks scrapes constantly — prospect audits, rival studies, citation diagnostics, social listening — and does monthly competitive strategy work on top. Five problems keep recurring:

1. **Scraped content is used once and discarded.** Every skill scrapes, uses the result, and throws it away. No visibility into what was captured, no reuse — the same rival pages are re-scraped by different skills in the same week, re-paying the time and re-rolling the anti-bot dice.
2. **Scraping gaps become hallucinated answers.** On-demand scraping silently misses pages (anti-bot walls, timeouts, unrendered JavaScript). Nothing forces the gap to be visible, so the AI fills it from general knowledge of the brand.
3. **Claims about the competitive landscape come from narrow samples.** An on-demand scrape sees a handful of pages; "they focus on X" generalized from that sample is how hallucinated competitor claims happen. The SEO APIs (Ahrefs/GSC/DataForSEO) hold the actual breadth — every page, its traffic, its keyword footprint — but return numbers only, never page content, and today their responses are used once by whoever called them and lost.
4. **No history.** Because nothing is kept, *what changed this month* and *what started working* are unanswerable at any price. Past versions of a page cannot be bought back.
5. **Claims aren't defensible.** When a client pushes back ("their site doesn't say that"), there is no dated evidence — no stored page, no screenshot — of what the site showed on the day we analyzed it.

**What we're building:** a database that keeps everything we scrape and makes it reusable, plus the bird's-eye layer above it. Scraping stays where it is today; every scrape's output (screenshot, raw HTML, extracted text) is saved, tagged, dated, and fingerprinted. Alongside the pages, the store keeps the monthly **landscape** — every competitor page with estimated traffic and its keyword footprint, **mapped back to the client's own topics and keywords** — so the map is organized around the question that matters: *for the topics my client needs to win, who is winning them, with what content, and what does it take.* Analysis sees the whole map, not a keyhole. A small local web UI browses, searches, and diffs all of it; agents query the same database; before any skill scrapes, it checks the store first. **Scrape once, use many times.** Multi-project from day one (projects are rows, not code). Example project: GoFreight vs. CargoWise, Magaya, Descartes, FreightPOP.

## 2. Objectives & Success Metrics

Each metric ties to the pain it retires:

| # | Objective | Metric | Pain |
|---|---|---|---|
| O1 | Reuse, not re-scrape | Repeat request inside the staleness window is served from the store; store-hit vs. web-fetch visible in run output | 1 |
| O2 | See what was captured | Every capture browsable in the UI (screenshot, text, provenance) within a minute of the scrape | 1 |
| O3 | No hallucinated content claims | 100% of page-content claims cite a stored version; failed captures surfaced as "not captured", never described | 2 |
| O4 | No narrow-sample landscape claims | 100% of coverage/performance claims cite the breadth datasets — publishing coverage from `inventory_pages`, ranking performance from the landscape, labeled `est., <provider>` | 3 |
| O5 | History accumulates | Versions never overwritten; month-vs-month page diffs and landscape shifts visible in the UI from month 2 | 4 |
| O6 | Defensible evidence | Any claim traces to URL + capture date + version (or landscape row) in under a minute, findable in the UI | 5 |
| O7 | Human self-serve | Tina answers "what did their pricing page say in June?" and "what topics does CargoWise own?" alone, in the UI | 1, 3 |
| O8 | Lean | Build ~3.5–4 weeks; running cost under ~$1–2/mo per client in dollars (analysis runs on the existing Claude Code subscription) | — |

The bar Tina set: hit ~95% of the goals with the simplest system that does so.

## 3. Users & Use Cases

Primary users: every scraping skill (prospect-audit, client-01-diagnosis, citation-diagnostics, social listening, rival studies), Tina and the strategist/AM agents, the BD agent.

- **US-1 — Scrape once, reuse everywhere.** As any skill, I query the store before scraping so I don't re-scrape, re-pay, and re-risk anti-bot walls. *Done when:* a second run over the same pages within the staleness window hits the store, not the web.
- **US-2 — Competitor messaging watch.** As the GoFreight AM, I want a monthly summary of what each competitor changed on their key pages. *Done when:* "what changed across the competitor set?" returns a page-cited summary in under 10 minutes after the refresh.
- **US-3 — Topic battleground view.** As the strategist, I pick one of MY client's topics and see every competitor page competing on it, sorted by importance (positions, est. traffic, breadth), with capture status — before reading any page. *Done when:* the UI answers "who is winning 'freight visibility' and with which pages?" with no scraping and no Claude session.
- **US-4 — Topic deep-dive (the core flow).** As a strategist, from a topic battleground I capture the top competing pages (~10–20, not a site-wide crawl) and have Claude analyze what they wrote and the observable reasons they rank — content structure, depth, coverage of the topic's queries, E-E-A-T signals, available off-page data — citing stored versions. *Done when:* one topic run yields captured, topic-tagged pages plus an analysis framed as "what the winning pages have that ours don't," with zero definitive causal claims.
- **US-5 — Content gap analysis.** As the content lead, I want Claude to name the buyer questions competitors answer that the client doesn't. *Done when:* the analysis names missing topics, citing the landscape for coverage and stored pages for content.
- **US-6 — BD pitch evidence.** As Bianca, I want prospect-audit scrapes stored and browsable, so the pitch contains observations backed by pages I can show. *Done when:* the diagnosis cites at least three stored-page comparisons, each openable in the UI.
- **US-7 — Claim provenance.** As Tina signing off a report, I want every competitor claim traceable to dated stored evidence. *Done when:* any claim traces to its version or landscape row in under a minute.
- **US-8 — New-client baseline.** As onboarding, I want a day-one capture + landscape of the client's competitive set. *Done when:* month-3 reports diff against month 0 in the UI.

## 4. Scope

**In scope (v1):**
- One SQLite store (+ screenshot/file directory) holding: captured page versions (screenshot, raw HTML, markdown, hash, provenance, taxonomy) and monthly landscape data per competitor (pages × est. traffic; keywords × topics).
- Three ingestion paths: capture-on-scrape (skills), monthly selector-driven refresh, topic-triggered capture.
- Reuse rule (store-first lookup with per-purpose staleness) wired once into the shared web-scraping skill.
- Local web UI, read plus scoped human actions (FR-26/28/29): browse / search / screenshots / provenance / page diffs / per-competitor bird's-eye view / topic curation / refresh + capture triggers.
- Agent CLI over the same DB; analysis evidence rules (coverage → landscape; content → versions).
- Screaming Frog manual-export importer.

**Out of scope (v1)** — each returns only via a §9 trigger:
- Embeddings, vector search, chunking, rerankers (FTS5 + direct reading suffices at 300–500 captured pages/project).
- AI classification/tagging (topic grouping and page typing are deterministic; AI-assisted tagging is deferred).
- Hosted multi-tenant SaaS, auth, client-facing UI. One local app — read plus a small set of human actions (topic curation, capture/refresh triggers); no free-form editing of stored content.
- Real-time / sub-day crawling. Live "right now" questions still use on-demand scraping under the same evidence rules.
- Replacing the rank/traffic APIs — they feed the landscape; this stores what they return plus the page content they never see.

## 5. Requirements

P0 = system is wrong without it · P1 = core value, ships in v1 · P2 = v1 if time allows, else first follow-up.

| ID | Pri | Requirement | Acceptance criterion |
|---|---|---|---|
| FR-1 | P0 | Every scrape's artifacts stored: screenshot (file, path in DB), raw HTML when fetched, markdown, URL, timestamp, content hash, fetch status, `capture_source` (skill), `capture_purpose` | One real skill run → every touched page has a version row with screenshot path and source/purpose filled |
| FR-2 | P0 | Capture wiring lands once, in the shared web-scraping skill; consumers inherit it | A skill routing through web-scraping stores captures with zero skill-specific code |
| FR-3 | P1 | Reuse rule: store-first `lookup`; per-purpose staleness threshold (default 30 days, configurable); miss/stale → scrape, result stored | Same URL twice in a day → second run serves stored version, no web fetch; forced staleness → re-scrape + new version |
| FR-4 | P0 | Taxonomy on every stored item: project, site/domain, `page_type` from URL pattern (pricing/product/blog/comparison/home/about/other), source, purpose, tags; projects/sites auto-created by domain | Fresh-domain capture acquires site + page_type with no manual setup and no LLM call |
| FR-5 | P1 | Deterministic selector, four signals in priority order: AI-cited (always in) → est.-traffic coverage to ~80% cumulative (configurable) → top-10 on client keyword panel → strategic URL patterns; every URL carries a machine-written reason; no LLM | Fixed API fixtures → identical list on repeated runs; no row lacks a reason |
| FR-6 | P1 | No fixed page counts; <~30-page sites taken whole; client's own pages on GSC real data; 1M-token project budget enforced by dropping lowest-signal pages (cited/strategic never first), every drop recorded with reason | Small-site fixture yields full sitemap; oversized fixture yields drop records; brand-site reasons reference GSC |
| FR-7 | P1 | One provider contract (`url, estimated_traffic, panel_rankings`); DataForSEO default (`relevant_pages/live`, `ranked_keywords/live`), Ahrefs alternate; provider pinned per project, recorded per run; raw API responses stored; rival figures labeled `est., <provider>` everywhere | Adapter swap changes no selector code; mismatched provider fails loudly; any URL's raw justification queryable; no unlabeled rival numbers |
| FR-8 | P1 | Monthly refresh: selector re-run, adds/drops recorded with reasons, approved list captured via the shared pipeline (Playwright rendered fetch, trafilatura markdown, screenshot, hash over normalized markdown; robots.txt, rate limits, real UA); human skims/approves once per project, then monthly glance | Month-2 run stores a delta; approval is a recorded field; captured URL yields HTML + markdown + screenshot + hash |
| FR-9 | P2 | Screaming Frog import adapter: manual export (CSV + rendered HTML) dropped in a folder → same version rows, stamped `crawler: screaming_frog` | Imported versions indistinguishable to UI/analysis except by crawler stamp |
| FR-10 | P0 | Single SQLite file on the Mac mini; screenshots as files with DB paths; schema per §6 | Migration builds all tables + FTS from empty; system state = DB file + screenshot dir + code |
| FR-11 | P0 | Append-only history: versions never overwritten or deleted; failures stored with status, never blocking a run | No UPDATE/DELETE against document_versions in the codebase; dead-URL run completes with the failure row present |
| FR-12 | P0 | Full provenance per version: crawler, adapter_version, fetched_at, hash, fetch_status, source, purpose, selection-run link (Path B) | Any version row answers who captured it, how, when, why |
| FR-13 | P0 | FTS5 index over version markdown; filterable by project/site/month/taxonomy | Known phrase returns its page; `page_type=pricing` filter narrows correctly |
| FR-14 | P0 | Local web app (FastAPI, server-rendered, own port beside the Control Room): project → site → page → version history, screenshot displayed in page view. **Every page and version has a stable URL** (e.g. `/gofreight/pages/1423`); every page reference in Topics, Search, and Competitors links to it — plain click navigates, ⌘-click opens a new browser tab, so any number of page details can be open concurrently (server-rendered and stateless, so this costs nothing). Read-mostly, plus the scoped human actions of FR-28/FR-29 and the capture trigger of FR-26 — no other writes | Three clicks from project list to any page's versions; screenshot renders; a page's URL pasted into a fresh browser tab renders that page's detail; two details open side-by-side |
| FR-15 | P2 | Month-to-month diff view between any two versions of a page (markdown-level) | Fixture edit between runs → diff shows exactly that edit |
| FR-16 | P0 | Search box (FTS) + taxonomy filters; results link to stored versions | Competitor slogan search lands on their stored page |
| FR-17 | P0 | Every version shows provenance; failed captures visibly flagged "not captured"; UI unauthenticated — **the tailnet is the access boundary** (served on the mini, reached over the existing Tailscale network; team members like Eki are invited to the tailnet, nothing public). Multi-user concurrent access supported (SQLite WAL mode; read-mostly load). Every human action (FR-26/28/29) records the acting device (tailnet hostname/IP) — provenance, not accounts. DB writes limited to those named actions; stored versions and history are never editable from the UI | Dead-URL fixture shows a flagged entry; the only UI write paths are topic curation and capture/refresh triggers; two devices browsing concurrently work; an action row shows which device performed it |
| FR-18 | P1 | Agent CLI/SQL over the same DB, seven ops: `lookup <url> [--max-age]`, `list <project> [--month]`, `get <version>`, `diff <url> <a> <b>`, `search <q> [filters]`, `export <project> <month>`, `landscape <site> [--month]` | Each op runs from a shell, returns <1 s at reference scale (~500 pages/month/project) |
| FR-19 | P0 | Every analysis opens with a query-produced completeness statement: "N of M selected pages captured; these failed: …" | Every analysis output opens with it |
| FR-20 | P0 | **Evidence rule (content):** claims about what a page says cite URL + capture date + version; no citation, no claim; never from live fetches or model knowledge of a brand | Spot-audit finds zero uncited page-content claims |
| FR-21 | P0 | Failed-capture pages reported "not captured" — never described, never inferred | Analysis over the dead-URL fixture names it as not captured |
| FR-22 | P1 | Counts, URL lists, change lists come from SQL, never from asking an LLM to count; analysis prompts used per project are saved in the repo and reused on the next run | Numeric statements match direct query results; month-2 analysis references month-1's saved prompt file |
| FR-23 | P1 | **Landscape storage, mapped to client topics:** monthly API data stored per competitor domain — every page with est. traffic and its ranked keywords, each keyword assigned to a CLIENT topic by the client's tracked panel's own grouping (deterministic; no LLM); out-of-panel keywords land in an `unmapped` bucket, never force-matched; a URL may map to multiple topics, weighted by position × search volume. Per-topic page **importance** is queryable: positions on the topic's keywords, est. traffic, breadth (how many of the topic's keywords the page ranks for) | For any client topic-month: competitor pages ranked by importance answerable by SQL; mapping reproducible from stored keywords + panel; unmapped bucket present and queryable |
| FR-24 | P1 | **Topic-first bird's-eye UI:** client topic list → per-topic competitor page table (importance-sorted, capture status shown, one-click/one-command topic capture for uncaptured pages via FR-26) → drill-down into captured versions. Per-competitor view (SEO overview, expandable site structure, topic coverage with page counts, MoM shifts) is the secondary lens. All figures labeled `est., <provider>` | From the topic list, two clicks reach an importance-sorted competitor page table and a third opens a captured version; uncaptured rows expose the capture trigger; no unlabeled figures |
| FR-25 | P0 | **Evidence rule (coverage):** claims about what a competitor focuses on / what's winning cite the stored breadth datasets — never generalized from captured-page samples. Publishing-coverage claims ("they publish heavily on X") cite `inventory_pages`; ranking-performance claims ("they win X in search") cite the ranked landscape; the two are never conflated — a rival can publish 580 posts and rank 25 (stridec, Aug 2026). (Rationale: on-demand scraping is a narrow sample; generalizing from it is how hallucinated competitor claims happen.) | Spot-audit: every coverage claim cites inventory or landscape rows, correctly typed; performance figures labeled `est., <provider>` |
| FR-26 | P1 | **Topic-triggered capture (Path C):** a topic question → the landscape's per-topic importance ranking (FR-23) yields the short list (~10–20) of top competing URLs → Playwright captures just those, tagged with the topic as `capture_purpose`. Caveat: pages ranking for nothing are invisible to topic queries; the refresh's citation signal + strategic URL patterns are the backstop | Topic run captures ≈10–20 pages, all tagged with the topic; no site-wide crawl occurs; captured pages reusable via `lookup` |
| FR-27 | P0 | **Evidence rule (rank causes):** topic analyses report observable content attributes (structure, depth, coverage of the topic's queries, E-E-A-T signals) and available off-page data points (e.g. referring domains from the provider) — never a definitive causal "why they rank." Outputs are framed as "what the winning pages have that ours don't" | Spot-audit of a topic analysis finds zero unqualified causal rank claims; every attribute cited to a stored version or landscape/provider row |
| FR-28 | P1 | **Human topic curation (pipelines propose, humans decide):** in the Topics view a human can (a) define a new topic and assign panel keywords to it, (b) set each topic's business value (HIGH/MED/LOW — drives topic ordering and capture depth), (c) review system-suggested topics from two deterministic sources, no LLM, same input → same suggestions. PRIMARY — the published inventory (FR-31): recurring normalized title keyphrases across rival `inventory_pages` (site-name suffixes stripped, fixed stopword list, phrases on ≥5 pages become candidates, longest phrase wins over nested shorter ones), evidence = per-rival page counts + sample titles + a ranked overlay (whether any landscape keywords match — publishing without ranking is itself signal). SECONDARY — the `unmapped` keyword bucket: keywords grouped by shared best `ranking_url` (groups sharing ≥50% of their pages merge, ≥5 keywords become a candidate named after the highest-volume keyword). Discovery leads with what rivals PUBLISH, not just what already ranks. The human approves or dismisses; nothing enters the topic list without an explicit approve | Suggested topic appears with evidence chips + Approve/Dismiss; approving moves its keywords out of `unmapped`; dismissing suppresses the suggestion; value changes reorder the topic list |
| FR-29 | P1 | **On-demand page refresh:** every page view shows the stored version's age ("stored version is N days old — live page may differ") and a "Refresh content now" action (UI button + CLI op) that recaptures the page immediately through the normal capture path, creating a new version with `source: manual_refresh`; history is never replaced | Refresh on a fixture page creates a new version row with `manual_refresh` provenance; the old version remains; the staleness note shows the correct age |
| FR-30 | P1 | **Per-competitor SEO overview + site structure** (derived from landscape data already fetched — no new API calls): pages in landscape, pages captured in our DB, est. site traffic/mo, keywords ranked. Site structure = ALL subfolders (first URL path segment), each an expandable row (page count + share of est. traffic collapsed; expanded, the folder's pages with their actual titles and est. traffic). Topic coverage list shows up to ~10 topics by default with a per-topic competitor-page count, expandable to every topic — the bird's-eye is complete, never silently truncated | Competitor view shows the four overview numbers; every subfolder present and expandable to titled pages; topic list shows counts and expands to all topics; totals reconcile with the landscape rows by SQL; all traffic figures labeled `est., <provider>` |
| FR-31 | P1 | **Content inventory (published estate):** monthly per-rival inventory of ALL published pages read from the site's own surfaces — sitemap / sitemap-index children / paginated blog-index crawl with card extraction / WP REST API (SSL bypass where a cert is expired, recorded) — collection method pinned per site in the project config; each row stores the real `<title>`, URL, path section, and lastmod/published date where available, in `inventory_pages` (a separate entity from ranked `landscape_pages` — published ≠ ranking; ranked-pages showed stridec at 20–25 pages against a real 580-post estate). Competitor overview and site structure show published vs ranked vs captured counts side by side | Inventory count per rival within ~5% of the validated manual map (`market-intel/sg-rival-content-map-2026-08.md`); every row has a real title, never a slug; re-run in the same month replaces that month's inventory only; ranked landscape untouched |

## 6. Technical Design

```text
   ON-DEMAND SCRAPES          MONTHLY REFRESH            TOPIC QUESTIONS
       (Path A)                  (Path B)                   (Path C)
  (audits, diagnostics,    selector.py + provider     "who wins <client topic>
   listening, studies)     adapter — 4 signals,        and how?" → landscape
         │                 reasons, no LLM; writes     importance ranking
         │                 LANDSCAPE (client-topic     → top ~10–20 URLs
         │                 mapped)                            │
         │                        │ approved list             │
         ▼                        ▼                           ▼
   ┌────────────────────────────────────────────────────────────────┐
   │ CAPTURE (shared): reuse-rule lookup first → Playwright fetch   │
   │ + screenshot + trafilatura markdown + hash + taxonomy typing   │
   └───────────────────────────────┬────────────────────────────────┘
                                   ▼
              SQLite (one file, FTS5) + screenshot directory
              pages: document_versions · map: landscape tables
                                   │
          ┌────────────────────────┼──────────────────────────┐
    UI (read + actions)          Agent CLI/SQL               ANALYZE (Claude)
    topic battlegrounds ·   lookup · list · get ·      landscape says WHERE
    browse · search ·       diff · search · export ·   to look; content says
    screenshots · diffs ·   landscape                  WHAT they did; claims
    per-competitor lens                                cite rows/versions
```

**Data model (SQLite):**

```text
projects            id, slug, provider_pin, keyword_panel, cadence
sites               id, project_id, name, role (brand|competitor|reference), domain
documents           id, site_id, url, page_type
document_versions   id, document_id, snapshot_month, raw_html, markdown, screenshot_path,
                    content_hash, http_status, fetched_at, fetch_status (ok|failed:<reason>),
                    crawler, adapter_version, capture_source, capture_purpose, tags,
                    selection_run_id (nullable), changed_since_previous
selection_runs      id, project_id, month, provider, approved_by, approved_at
selection_items     id, selection_run_id, url, reason, signal, dropped, drop_reason
selection_raw       id, selection_run_id, provider_endpoint, response_json
panel_keywords      id, project_id, keyword, client_topic   -- the client's tracked panel,
                                                            -- topics per its own grouping
landscape_pages     id, site_id, month, url, est_traffic, provider, serp_title
                    -- serp_title: page title as shown in Google results, taken from the
                    -- ranked-keywords rows already fetched (no extra API call). Used by the
                    -- UI for uncaptured pages; a captured page's exact <title> supersedes it.
landscape_keywords  id, site_id, month, keyword, client_topic ('unmapped' if out-of-panel),
                    position, est_volume, ranking_url, provider
                    -- topic assignment = join against panel_keywords; deterministic, no LLM;
                    -- a ranking_url may appear under multiple topics (weight: position × volume)
topics              id, project_id, name, value (high|med|low), created_by_device, created_at
                    -- FR-28: human-curated topic list; value drives ordering + capture depth
suggested_topics    id, project_id, name, evidence, status (pending|approved|dismissed),
                    decided_by_device, decided_at
                    -- FR-28(c): deterministic clusters of the unmapped bucket await a human decision
inventory_pages     id, site_id, month, url, title, path_section, lastmod, source_method
                    -- FR-31: the site's own published estate (sitemap/blog-index/WP REST),
                    -- real titles; distinct from ranked landscape_pages
action_log          id, action, detail, device, created_at
                    -- FR-17: every human action records the acting device (tailnet hostname/IP)
fts_versions        FTS5 virtual table over document_versions.markdown
```

Two decisions carry the design: the **document/version split** (a page keeps one identity; every capture appends an immutable version — history, diffs, reuse, provenance become one-JOIN simple), and the **landscape/content split** (the map of what's working is data the APIs already return — storing it costs cents even for a 1,000-page competitor because no content is scraped; content capture stays small and targeted because the map says where to look). The map's organizing dimension is the **client's topic set**: every competitor URL maps back to client topics through the keywords it ranks for, so importance, capture, and analysis all answer "who is winning the topics my client needs to win, with what content." All three ingestion paths write the same version rows; Path B additionally writes landscape + selection tables.

Sizing: monthly refresh ≈ 300–500 captured pages/project (~15 small rival to ~50–70 large, × 6–8 sites) ≈ 400k–1M markdown tokens — loadable into a Claude context via one `export`; landscape tables add thousands of small rows, trivial for SQLite.

## 7. Milestones (~3.5–4 weeks total)

The landscape layer + bird's-eye view added ~1–2 days over Rev 5's estimate; the Rev 6.3 human-action surfaces (FR-28 topic curation, FR-29 refresh, FR-30 competitor overview) add ~2–3 more, and the Rev 6.5 content inventory (FR-31) another ~2 — stated, not shaded. Each milestone ends demonstrable:

- **M1 — Store + capture path (3–4 days).** Schema frozen — ALL tables of §6 including landscape, `topics`/`suggested_topics`, and `action_log` (the three paths, the importer, and every UI action write to this schema, so it must be complete here even though the UI that uses the curation tables arrives in M2–M3); capture pipeline + CLI; taxonomy typing. (Wiring into the shared web-scraping skill lands in M4 with the reuse rule.) Demo: a real scrape lands in the DB with screenshots, hashes, source/purpose; one dead URL stored as failed.
- **M2 — UI core (4–5 days).** Browse, version history, screenshots, FTS search + filters, provenance display, stable per-page URLs (FR-14), per-page staleness note + "Refresh content now" (FR-29), action log recording the acting device (FR-17). Demo: Tina sees yesterday's scrape's screenshots, searches a phrase, refreshes a page from her laptop and the action row names her device.
- **M3 — Selector + landscape + topic surfaces + first refresh (4–5 days).** Client keyword panel imported (`panel_keywords`); selector populates selection AND landscape tables for GoFreight with keyword→client-topic mapping; topic-first bird's-eye in the UI plus topic curation (FR-28: add topic, set value, approve/dismiss suggestions) and the per-competitor SEO overview + expandable site structure (FR-30); approved list captured; launchd schedules it. Demo: pick a GoFreight topic → importance-sorted competitor page table; approve a suggested topic and watch its keywords leave `unmapped`; competitor overview reconciles with landscape rows by SQL; adds/drops delta on the second run.
- **M3b — Content inventory (~2 days).** `inventory_pages` migration (the one amendment to the M1 schema freeze — additive table only); per-method collectors driven by project config; inventory-primary topic suggestions with ranked overlay; competitor view shows published vs ranked vs captured. Demo: stridec inventory within ~5% of the validated 580-post map; suggestions cite published titles; the overview's three counts visibly disagree where they should.
- **M4 — Reuse rule + topic capture + first analysis (2 days).** `lookup` live in web-scraping; Path C end-to-end from a topic battleground; then ask *"For 'freight visibility', what do the winning competitor pages have that GoFreight's don't?"* Demo: repeat scrape hits the store; the topic run captures ~10–20 tagged pages; analysis opens with the completeness statement, coverage claims cite landscape rows, content claims cite versions, rank-cause statements stay observable-only (FR-27). **This is the acceptance test.**
- **M5 — SF importer + diff view (1–2 days, can trail).** SF export lands as version rows; month-to-month diff view.

Order constraints: schema freezes at M1 (all three paths + importer write to it); the first Path-B selection is human-approved before the first refresh spends fetches.

Three-month proof: the M4 question against a historical month; a what-changed-this-quarter read (page diffs + landscape shifts); the adds/drops log showing which pages the market started rewarding; a measurable share of skill runs served from the store.

## 8. Costs, Risks & Mitigations

**Costs**
- **Build:** ~3.5–4 weeks (M1 3–4d · M2 4–5d · M3 4–5d · M3b 2d · M4 2d · M5 1–2d). The DB + UI + landscape are ~1.5 weeks of that; the price of seeing, searching, and reusing captures.
- **Running:** under ~$1–2/mo per client in actual dollars. Playwright, SQLite, screenshots, and the local web UI cost nothing (open-source, on the existing Mac mini). The only per-use dollar cost is DataForSEO: ~$0.012/task + $0.00012/item — a full monthly landscape + selection pull is under $1 per project (covering a 1,000-page competitor's landscape costs cents because no content is scraped). Claude analysis runs through the existing Claude Code subscription like the mini's scheduled agent fleet — no API bill; it consumes subscription capacity (~500k tokens read per project per month), not dollars. If the analysis ever becomes a standalone client-facing product outside the subscription, it moves to API billing at roughly $2–5 per monthly analysis run per client — a future decision, not a build cost. Reuse reduces today's scraping spend.
- **Human:** ~5 min/month per project (approve selection diff, glance at failures).
- Reference point: the original platform design was ~$35–70k build + $50–270/mo infra. This delivers the reuse loop, the landscape view, and the same research answers for ~3.5–4 weeks of build.

**Risks & mitigations**

| Risk | Mitigation |
|---|---|
| Anti-bot walls block captures | Retry with backoff; failures stored + flagged + reported "not captured"; persistent blocks → manual SF export; reuse rule shrinks exposure |
| Skills bypass the store | Wiring lands once in the shared web-scraping skill; then a defined wiring pass over consuming skills — owner: stack-integrator agent; trigger: M4 complete; check: each named skill's procedure references the store-first rule |
| Provider estimate drift churns lists/landscape | Provider pinned per project; all figures labeled `est., <provider>`; adds/drops recorded with reasons |
| New/small rivals invisible to data signals | Take-all fallback under ~30 pages (FR-6); topic-blind new pages backstopped by citation signal + strategic patterns (FR-26) |
| DB/screenshot growth | Tens of MB text/month at reference scale; screenshots already on disk; HTML column can follow to files if a project outgrows it — schema isolates both |
| Stale reuse serves outdated content | Per-purpose staleness thresholds (FR-3); `lookup` reports version age; freshness-critical calls force a scrape, which is stored |
| ToS exposure if capture is productized | Owner: Tina; artifact: a one-page internal policy note on scraping scope (public marketing pages only, robots/ToS posture) before the system is offered as a client-facing service; internal use proceeds meanwhile |

## 9. Open Questions & Deferred

**Open questions**
1. Staleness defaults per purpose: 30 days fits strategy work; do citation-diagnostics or BD audits need tighter windows? Settle at M4 with real usage.
2. The `unmapped` keyword bucket: out-of-panel keywords competitors rank for are themselves strategy signal (topics the client's panel doesn't track yet). Who reviews it, and on what cadence — fold into the monthly approval glance, or a quarterly panel-refresh step?
3. Which consuming skills are in the first wiring pass (post-M4) — proposed: citation-diagnostics, client-01-diagnosis, prospect-audit-v3, content strategy.

**Deferred (the scale-out platform)** — compressed record of the original Rev 2 design (full spec in git history). What this PRD builds is its working core; deferred parts are scale machinery: embeddings + pgvector hybrid search + query router; AI enrichment (topics/entities/typed claims) and AI-assisted tagging; Postgres migration; hosted multi-tenant backend with auth; client-facing product UI. (~$35–70k build, $50–270/mo infra.)

**Upgrade triggers** — build a deferred component when its condition becomes true:
1. A project needs >~2–3M tokens read per analysis → embeddings/hybrid search.
2. Clients (not just the team) need to log in and search → hosted backend + auth.
3. Questions span many client projects (benchmarks, pattern mining) → Postgres + enrichment.
4. Monitoring needs daily/sub-day crawl-and-diff → scheduler + alerting.
5. Claim analytics across thousands of pages, or deterministic topic grouping proves too coarse → AI enrichment / AI-assisted tagging.

When a trigger fires, the accumulated history — the thing this system exists to protect — migrates as-is: the document/version + landscape schema is the ingestion format the platform was designed around.
