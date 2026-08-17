# Multi-Brand AI Content Intelligence & Competitive Research System

> **Rev 4 — 17 Aug 2026.** Page selection is now a **deterministic selector script driven by performance data** (AI citations, estimated traffic, head-to-head rankings), replacing human curation; the data provider behind it is swappable (DataForSEO default, Ahrefs alternate) and pinned per project. The analysis layer gains an explicit **anti-hallucination rule**: every page-content claim cites a snapshot file path, and failed fetches are reported as "not captured," never described. A lean pass confirmed the rest: hit ~95% of the goals with the simplest system that does so.
>
> (Rev 3, 14 Aug 2026, right-sized the plan around a snapshot library instead of a retrieval platform — the corpus at boutique client scale is small enough for Claude to read directly. Rev 2, 13 Aug 2026, made Playwright the primary crawler and demoted Screaming Frog to an import adapter. Both decisions carry forward; full earlier specs are in this file's git history.)

## 1. Objective

Build a reusable content intelligence corpus for Novastacks that snapshots websites belonging to:

- Client brands
- Competitors
- Industry/reference websites
- Publishers/media relevant to a specific research project

and lets Claude answer competitive research questions **by reading the corpus directly**, with every answer traceable to an exact page, snapshot date, and source URL.

The system is multi-tenant / multi-project from day one: per-project directories, no assumptions about competitor counts, nothing hard-coded for one client. Example project: GoFreight vs. CargoWise, Magaya, Descartes, FreightPOP.

### The three layers

```text
Layer 1 — SELECT   deterministic script; ranking/citation APIs decide WHICH
                   pages matter (no LLM anywhere in selection)
Layer 2 — CAPTURE  our own Playwright script snapshots those pages to disk
                   (raw HTML + markdown + hashed manifest; no vendor crawler)
Layer 3 — ANALYZE  Claude reads the saved files and answers with citations
```

AI appears **only in Layer 3**. Layers 1 and 2 are plain code: same inputs, same outputs, auditable after the fact.

What the system is NOT (at this scale): a database, a search UI, an API, or a chat product. Those live in Appendix A behind explicit upgrade triggers.

---

## 2. Why Right-Sized

The sizing math that drives the whole design:

```text
pages per site: selector-derived (no fixed number — see §4);
                typically ~15 for a small rival, ~50–70 for a large one
× 6–8 sites per project (brand + competitors + reference)
= roughly 300–500 pages per project
≈ ~1–2k tokens per page as clean markdown (nav/footer stripped)
= ~400k–1M tokens per project corpus; ~500k typical
```

A corpus this size is one an AI can read in one or a few passes. At that scale:

- **Retrieval infrastructure solves a problem we don't have.** pgvector, chunking, hybrid search, rerankers, and a query router exist to find the relevant 1% of a corpus too big to read. When the whole corpus fits in a few reads, retrieval is the read.
- **The parts that CAN'T be retrofitted are cheap to build now.** If we don't snapshot competitor sites monthly starting today, that history is gone forever — no later platform can recover it. Selection logs, content hashes, and provenance fields cost days, not months.
- **Cost honesty:** ~1–1.5 weeks to build, ~$5–20/mo per client to run (selection API calls are cents; compute + storage are trivial; the main cost is analysis tokens plus a monthly approval glance). The full platform was estimated at ~$35–70k to build. The lite system delivers the same research answers at this client scale.

**Project token budget: ≤1M tokens.** If the selector's output overshoots it, the lowest-signal pages are dropped and every drop is logged with its reason (§4). No silent caps — a truncated corpus that looks complete is the same disease as a hallucinated answer.

Everything below is designed so that the corpus produced by the lite system is a valid input to the full platform later (Appendix A) — the snapshots, manifests, and provenance fields ARE the ingestion format.

---

## 3. Repository Layout (Multi-Tenant)

One corpus repository (or one directory tree under the Novastacks estate), organized per project:

```text
content-intelligence/
├── PLAN.md                        # this file
├── tools/
│   ├── select.py                  # deterministic page selector (§4)
│   ├── providers/                 # data adapters behind one input contract
│   │   ├── dataforseo.py          #   default
│   │   └── ahrefs.py              #   alternate
│   ├── snapshot.py                # Playwright snapshot script (§5)
│   └── sf_import.py               # Screaming Frog export import adapter (§6.3)
└── projects/
    └── gofreight/
        ├── project.yaml           # project config: sites, roles, provider pin, cadence
        ├── selection/             # selector output, versioned with the repo
        │   ├── 2026-08.json       # selected URLs + per-URL reason + drops log
        │   └── raw/2026-08/       # raw API responses the selection was derived from
        └── snapshots/
            └── 2026-08/           # one directory per snapshot run
                ├── manifest.json  # per-run manifest (§6)
                ├── cargowise/
                │   ├── pricing.html        # raw HTML, exactly as fetched
                │   ├── pricing.md          # markdown rendering for reading
                │   └── ...
                └── ...
```

Rules:

- Every artifact lives under exactly one `projects/<slug>/` — nothing shared, nothing global. A new client is a new directory; no config elsewhere changes.
- Selection files, raw API responses, and manifests are committed to git. Raw HTML snapshots are committed too at this scale (~500 pages/month/project is well within git comfort); if a project's snapshots outgrow the repo, move HTML to object storage and keep paths in the manifest — the manifest schema (§6) already carries paths, so nothing else changes.
- Do not hard-code a competitor count anywhere. `project.yaml` lists sites; the tools iterate over whatever is listed.

`project.yaml` example:

```yaml
project: gofreight
provider: dataforseo          # pinned for the project lifetime (§4.3)
keyword_panel: panel.txt      # the client's tracked keywords (head-to-head signal)
sites:
  - name: GoFreight
    role: brand
    domain: gofreight.com
  - name: CargoWise
    role: competitor
    domain: cargowise.com
  # ... one entry per site; any number of competitors/reference sites
cadence: monthly
```

---

## 4. Page Selection: Deterministic Selector

The corpus is **derived from performance data, not curated by hand and not crawled blind.** `tools/select.py` produces each site's URL list from four signals. It is plain code — no LLM anywhere in selection; same inputs, same output.

### 4.1 Signals, in priority order

1. **AI-cited pages — always in.** Any page of the site cited by AI engines in Novastacks' own citation testing (WorkDuo prompt runs). Highest-value signal for the business; non-negotiable regardless of site size.
2. **Traffic coverage, not a page count.** The site's top pages by estimated organic traffic, taken in descending order until ~80% cumulative coverage of the domain's estimated traffic. The threshold is a config dial, not sacred. Because traffic concentrates in few pages, this is self-sizing: a small rival may hit 80% with 12 pages, a large one with 50.
3. **Head-to-head pages.** Pages ranking top-10 for keywords in the client's tracked keyword panel — the pages beating (or contesting) the client on queries that matter.
4. **Strategic pages by URL pattern.** Homepage, `/pricing`, `/product*`, `/about` — pattern-matched, not counted. These rarely rank or get cited but announce positioning changes.

Merge, dedupe, attach a reason to every URL (`"cited: Perplexity 2026-08 run"`, `"traffic rank #7 (est., dataforseo)"`, `"head-to-head: top-10 for 'freight forwarding software'"`, `"strategic: /pricing"`).

**There is no fixed page count anywhere.** Site size self-adjusts through the signals.

- **Small-site fallback:** if a rival's marketing site has under ~30 pages total (sitemap count), take all of them — new/small rivals are invisible to traffic and citation data, and selection overhead isn't worth it below that size.
- **Client's own site:** selected on **GSC real data** (actual clicks/impressions), not third-party estimates — we have the truth for our own side; use it.
- **Budget enforcement:** if the project total exceeds the ≤1M-token budget (§2), drop lowest-signal pages (strategic and cited pages are never dropped first) and **log every drop with its reason** in the selection file.

### 4.2 Monthly re-derivation

The selector re-runs at each monthly snapshot. Adds and drops are logged with reasons ("entered: newly cited by ChatGPT" / "dropped: fell out of traffic top-80%"). **This log is itself strategy signal** — which pages the market started rewarding is precisely the "learn what's working" question the system exists to answer.

Human role: **skim and approve the generated, reason-annotated list once per project** (and glance at the monthly adds/drops report). Pipelines propose; humans approve. This is a 2-minute read, not curation work.

### 4.3 Provider adapters (DataForSEO default, Ahrefs alternate)

The selector consumes one input contract — a table of `url, estimated_traffic, panel_rankings` — produced by a provider adapter:

- **DataForSEO (default):** `dataforseo_labs/google/relevant_pages/live` for per-page estimated traffic on any domain; `dataforseo_labs/google/ranked_keywords/live` (filtered to the panel) for head-to-head positions. Pay-per-call (~$0.012/task + $0.00012/item — cents per run at our volumes); already integrated in the Novastacks stack.
- **Ahrefs (alternate):** top-pages + organic-keywords equivalents behind the same contract.

**The provider is pinned per project for its lifetime and recorded in the selection file.** Different providers estimate traffic differently; mixing them across months makes pages enter and leave the list because the ruler changed, not the market — the same phantom-diff disease the crawler provenance stamps (§6.2) prevent, with the same cure.

**Estimate honesty:** all rival traffic figures are estimates and are labeled `est., <provider>` wherever they appear — in selection files, reports, and analysis output. Never stated as measured fact. (Client-side GSC numbers are measured and may be stated as such.)

### 4.4 Auditability

The selector saves the raw API responses alongside its output (`selection/raw/<YYYY-MM>/`). If a page's inclusion ever looks wrong, open the input file and see exactly what the provider said that day. Selection is reproducible and auditable, not just repeatable.

---

## 5. Snapshot Script (Playwright)

One small server-native script, `tools/snapshot.py`, run monthly per project:

```text
for each site in project.yaml:
    for each URL in the site's current selection (§4):
        fetch with Playwright (rendered DOM, JS executed)
        save raw HTML            → snapshots/<YYYY-MM>/<site>/<page>.html
        convert to markdown      → snapshots/<YYYY-MM>/<site>/<page>.md
        compute content hash     → manifest entry
write manifest.json for the run
print run report (fetched / unchanged / changed / failed)
```

Design points:

- **Playwright, rendered DOM** — carried over from Rev 2. Modern marketing sites need JS rendering; a server-native browser keeps the whole run headless and schedulable (no desktop app in the loop).
- **Polite by construction:** honor robots.txt, rate-limit per domain (1 request every few seconds is fine — a site's pages are minutes of work), identify with a real user agent. At this volume there is no load concern, but the manners are non-negotiable.
- **Markdown conversion via `trafilatura`** on the rendered HTML — the best-benchmarked maintained extractor (≈90% recall / >91% precision on content extraction), with native markdown output; Playwright supplies the JS-rendered DOM that trafilatura alone can't get. It strips navigation, footer, cookie banners, and repeated UI, keeping headings, body text, lists, tables, and FAQ content. Markdown is the representation Claude reads; the raw HTML is the representation we preserve (never discard the original).
- **Content hash** is computed over the normalized markdown (not raw HTML), so cosmetic template changes don't register as content changes.
- **Failures don't block the run:** a 404/timeout is recorded in the manifest with its status and the run continues. The run report lists failures; the manifest's failure records feed the §8 "not captured" rule.

---

## 6. Snapshot Manifest & Output Contract

### 6.1 The contract

Every snapshot run produces one `manifest.json`. This is the simplified descendant of Rev 2's normalized crawl-output contract, and it keeps the same core rule: **everything downstream reads the manifest, never a crawler's internal format.**

```json
{
  "run": {
    "project": "gofreight",
    "snapshot": "2026-08",
    "crawler": "playwright",
    "adapter_version": "1.0.0",
    "selection": "selection/2026-08.json",
    "started_at": "2026-08-14T02:00:00Z",
    "completed_at": "2026-08-14T02:41:00Z"
  },
  "pages": [{
    "url": "https://www.cargowise.com/pricing",
    "final_url": "https://www.cargowise.com/pricing",
    "site": "cargowise",
    "role": "competitor",
    "http_status": 200,
    "fetched_at": "2026-08-14T02:03:12Z",
    "raw_html_path": "cargowise/pricing.html",
    "markdown_path": "cargowise/pricing.md",
    "content_hash": "sha256:…",
    "title": "…",
    "h1": "…",
    "word_count": 1240,
    "first_seen": "2026-07",
    "changed_since_previous": true
  }]
}
```

Required core per page: `url`, `http_status`, `fetched_at`, `raw_html_path`, `content_hash`, plus the run-level `crawler` and `adapter_version`. Everything else is optional and consumers must tolerate its absence.

### 6.2 Provenance is mandatory

`crawler` + `adapter_version` on every run, `fetched_at` + `content_hash` on every page, and a pointer to the selection file that chose the pages. This is what makes month-over-month diffs trustworthy: when we compare snapshots, we can distinguish a real content change from an artifact of switching or upgrading the fetcher — and a real list change from a change of data provider (§4.3). Any analysis output must cite `url` + `snapshot` so claims trace to an exact page at an exact date.

### 6.3 Screaming Frog: import adapter

Screaming Frog stays useful for its SEO fields and for sites where a human has already run a crawl. `tools/sf_import.py` takes a manual SF export (CSV + saved rendered HTML), maps it into the same snapshot directory layout and manifest schema, and stamps `crawler: screaming_frog` with its own `adapter_version`. A human runs SF, exports, drops the files in a folder; the importer does the rest. No SF automation is assumed or required.

---

## 7. Versioning & Change Detection

- **Never overwrite a snapshot.** Each month is a new `snapshots/<YYYY-MM>/` directory; history accumulates. This is the property that can't be retrofitted — the reason to build the lite system now rather than wait for the platform.
- **Unchanged pages are cheap:** if `content_hash` matches the previous snapshot, the manifest marks the page unchanged. (Store the HTML anyway at this scale — dedup is an optimization we don't need yet, and full monthly directories keep every snapshot self-contained.)
- **Diffing is a read, not a subsystem:** "what changed on CargoWise since June" = compare two manifests for changed hashes, then read the two markdown files side by side (or hand both to Claude for a summarized diff). At this scale, reading the changed pages is the diff.
- The manifest's `changed_since_previous` flag makes "show me everything that changed this month across all competitors" a one-liner.

---

## 8. Analysis Layer: Claude Reads the Corpus

There is no retrieval infrastructure. An analysis run works like this:

```text
1. Point Claude (Claude Code session or dispatched agent) at:
   projects/<slug>/snapshots/<YYYY-MM>/  +  its manifest.json
2. Claude reads the manifest to see what exists (sites, roles, pages,
   changes, failures).
3. Claude reads the relevant markdown files — filtered by site/role via the
   manifest, or simply all of them (a few passes or a handful of parallel
   readers for a big question).
4. Claude answers with citations: every claim carries url + snapshot date
   + snapshot file path.
```

### 8.1 Anti-hallucination rules (non-negotiable)

1. **Every page-content claim cites a snapshot file path.** No path, no claim. Claims are made from files on disk, never from content that existed only in a live fetch or in the model's general knowledge of a brand.
2. **Failed pages are reported as "not captured," never described.** If the manifest marks a page failed (404, timeout, anti-bot), the analysis says so explicitly. Describing or inferring what a missing page "likely says" is the defect this rule exists to kill.
3. **The manifest is the completeness statement.** Every analysis starts from "N of M selected pages captured; these failed: …" so gaps are visible line items, not silent holes.

### 8.2 What this supports (the same research jobs the platform promised)

- **What's working:** "What do the AI-cited competitor pages have in common that ours don't?" → the selection reasons identify the cited set; read them against the client's pages.
- **Compare:** "What are competitors promising around implementation?" → read the implementation/feature pages across sites, produce themes + evidence + comparison table.
- **Gap analysis:** "What topics do competitors cover that GoFreight doesn't?" → read both sides, list the gaps.
- **Change tracking:** "What changed in competitor positioning this quarter?" → changed pages from the manifests, read old vs. new; plus the selection adds/drops log for what the market started rewarding.
- **Historical:** "What was CargoWise saying about AI in January?" → read the January snapshot.

### 8.3 Standing rules

- Deterministic first: counts, URL lists, change lists, and filters come from the manifest (a script or a `jq` line), never from asking an LLM to count.
- Repeated questions become saved prompts/scripts in the project directory, so analysis quality compounds instead of being reinvented per run.

---

## 9. Operations & Cost

- **Cadence:** monthly selector run + snapshot per project (cron/launchd), plus on-demand snapshot runs before a client meeting or after a known competitor launch. Monthly is right for marketing-site drift; sub-day freshness is a platform trigger (Appendix A), not a lite feature.
- **Runtime:** ~300–500 pages at polite rate limits ≈ under an hour per project, unattended.
- **Human time:** ~5 min/month per project — approve the selection diff, glance at the failure list.
- **Cost:** ~$5–20/mo per client — analysis tokens dominate; selection API calls are cents per month (DataForSEO pay-per-call); compute/storage roughly nothing. Build: ~1–1.5 weeks (snapshot script + manifest 2–3 days; selector + DataForSEO adapter ~2 days; SF importer ~1 day; scaffolding + first end-to-end GoFreight run in the remainder).
- **Legal/manners:** honor robots.txt and rate limits; snapshots are for internal competitive research (standard practice), but take an explicit stance on ToS exposure before ever productizing snapshot-taking as a client-facing service.

---

## 10. Build Plan (~1–1.5 weeks)

```text
1. Scaffold projects/gofreight/ — project.yaml (provider pin, keyword panel)
2. tools/select.py + providers/dataforseo.py — signals → reason-annotated
   selection + raw API responses saved; Tina approves the first list
3. tools/snapshot.py — Playwright fetch → raw HTML + trafilatura markdown
   + manifest; hash-based change detection against the previous snapshot
4. tools/sf_import.py — SF export → same layout + manifest
5. First full GoFreight snapshot; verify manifest + spot-check markdown quality
6. First analysis run (the §12 acceptance question) under the §8.1 rules
```

Order matters in two places: the manifest schema (§6) is frozen before the SF importer is written (both writers target the same contract), and the first selection is human-approved before the first snapshot spends fetches on it.

---

## 11. Engineering Rules

1. **Never throw away raw source content.** Raw HTML is preserved alongside every markdown rendering; raw API responses are preserved alongside every selection.
2. **Never overwrite historical snapshots.** Every run is a new directory.
3. **Never let an analysis claim exist without provenance.** URL + snapshot date + file path on everything; failed pages reported as not captured (§8.1).
4. **Never hard-code competitor counts, page counts, or per-client logic.** Projects are directories + config; page lists are derived, not fixed.
5. **Never depend on one vendor's internals.** Fetchers sit behind the manifest contract; data providers sit behind the selector's input contract; both are pinned and stamped so switching is deliberate, never silent.
6. **Deterministic before LLM.** Selection, counts, filters, and change lists come from scripts and the manifest. AI appears only in Layer 3.
7. **No silent caps.** Anything bounded (token budget drops, fetch failures, small-site fallbacks) is logged where the analysis will see it.

---

## 12. Definition of Done

The lite system is done when, for the GoFreight project, we can ask:

> What are competitors promising around implementation?

and get back themes + evidence + a brand-vs-competitor comparison in which **every claim cites an exact URL, snapshot date, and file path**, produced by Claude reading that month's snapshot directory — with zero infrastructure beyond the repo, three small scripts, and a scheduled monthly run. Any page that failed to capture is named as such in the output.

And, three months in: the same question answered against a *historical* snapshot, a "what changed this quarter" read across manifests, and a selection log showing which pages the market started rewarding — proving the versioning and selection discipline paid for themselves.

---

# Appendix A — The Full Platform (Deferred)

This is the compressed record of the Rev 2 design (full spec: git history of this file). It is deferred, not rejected — the architecture was judged sound; the corpus size at boutique client scale removed its justification. The lite system's snapshots, manifests, and provenance fields are deliberately shaped to be the platform's ingestion format, so upgrading is additive.

## A.1 Architecture sketch

```text
Crawl configs → Crawler adapters (Playwright / SF import / Firecrawl)
             → Normalized crawl-output contract
             → Document pipeline (documents / document_versions split,
               semantic sections, 300–700-token chunks)
             → AI enrichment (topics, entities, claims, commercial signals)
             → Shared retrieval layer (Postgres FTS + pgvector hybrid search,
               metadata filters, reranking)
             → FastAPI backend (one API for humans AND agents)
             → Next.js UI (Explore search, Source viewer, Compare mode,
               Ask-the-Corpus) + AI tool interface
```

## A.2 What each component was for

- **PostgreSQL + document/version data model** — a canonical `documents` table (URL-independent identity) with immutable `document_versions` per crawl; the queryable version of what the lite system does with directories and manifests.
- **Semantic sections** — heading-based section extraction so retrieval returns "the Pricing section," not an arbitrary chunk. Flagged as the hardest, highest-leverage subsystem (template diversity); a dedicated spike, not a routine step.
- **Chunking + pgvector embeddings** — 300–700-token semantic chunks with heading paths, for finding the relevant slice of a corpus too large to read. Embedding model/version tracked per chunk for re-embedding.
- **Hybrid search** — keyword + vector + metadata filters + optional reranking; a query router classifying LOOKUP / SEARCH / COUNT / COMPARE / AGGREGATE / TREND / SYNTHESIZE / GAP_ANALYSIS so analytical questions go to SQL, not vector search.
- **AI enrichment** — extracted topics, entities, and claims (e.g., "implementation within 30 days," typed + confidence-scored + section-linked) enabling cross-corpus claim comparison at scale.
- **Change detection subsystem** — section-identity matching across crawls (hash + fuzzy heading + embedding similarity) so page redesigns don't read as total rewrites; crawler provenance consulted to suppress phantom diffs.
- **Shared retrieval API + UI** — one FastAPI backend serving both the human UI (Explore, Source viewer with evidence inspection, Compare tables with click-through-to-source cells) and AI agent tools (`search_content()`, `compare_sources()`, `find_claims()`, …), so humans and agents never diverge onto two sources of truth.
- **Tenant isolation** — workspace/project scoping enforced at the database/API layer.

Estimated at ~$35–70k to build (MVP), ~$50–270/mo platform infra, ~$60–180/mo per client in API costs at 10k-page scale.

## A.3 Upgrade triggers — build the platform when any of these is true

1. **Corpus outgrows direct reading:** a project needs more than ~2–3M tokens (~a few thousand pages) read per analysis — e.g., full-site crawls, many-competitor sweeps, or deep blog/archive coverage become requirements.
2. **Self-serve human search:** multiple team members (or clients) need to search/compare the corpus themselves, interactively, without a Claude session in the loop.
3. **Cross-project querying:** questions span many client corpora at once (industry benchmarks, cross-client pattern mining).
4. **Freshness below monthly-to-weekly:** monitoring/alerting use cases needing daily or sub-day crawl-and-diff.
5. **Claim-level analytics at scale:** systematic claim extraction and comparison across thousands of pages, where reading is no longer the bottleneck-free path.

Until one of these fires, the platform is scope we chose not to carry. When one does, the accumulated snapshot history — the thing the lite system exists to protect — becomes the platform's day-one corpus.
