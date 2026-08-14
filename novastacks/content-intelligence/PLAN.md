# Multi-Brand AI Content Intelligence & Competitive Research System

> **Rev 3 — 14 Aug 2026.** Plan right-sized around a **snapshot library**, not a retrieval platform. The decisive observation: for boutique-scale client projects, only ~70 pages per site actually matter. A whole project (client + 4–6 competitors + a few reference sites) is ~400–500 pages ≈ ~500k tokens — small enough for Claude to read directly. That removes the justification for pgvector, chunking, hybrid search, a search UI, and a FastAPI backend at current scale. What we keep is everything that cannot be retrofitted later: snapshot discipline, versioning, curation, and provenance. The full platform design survives as Appendix A with explicit upgrade triggers. (Rev 2, 13 Aug 2026, made Playwright the primary crawler and demoted Screaming Frog to an import adapter; that decision carries forward. The full Rev 2 platform spec is preserved in git history at this file's previous revision.)

## 1. Objective

Build a reusable content intelligence corpus for Novastacks that snapshots websites belonging to:

- Client brands
- Competitors
- Industry/reference websites
- Publishers/media relevant to a specific research project

and lets Claude answer competitive research questions **by reading the corpus directly**, with every answer traceable to an exact page, snapshot date, and source URL.

The system is multi-tenant / multi-project from day one: per-project directories, no assumptions about competitor counts, nothing hard-coded for one client. Example project: GoFreight vs. CargoWise, Magaya, Descartes, FreightPOP.

What it is NOT (at this scale): a database, a search UI, an API, or a chat product. Those live in Appendix A behind explicit upgrade triggers.

---

## 2. Why Right-Sized

The sizing math that drives the whole design:

```text
~70 pages that matter per site
× 6–8 sites per project (brand + competitors + reference)
= ~400–500 pages per project
≈ ~500k tokens as markdown
```

500k tokens is a corpus an AI can read in one or a few passes. At that scale:

- **Retrieval infrastructure solves a problem we don't have.** pgvector, chunking, hybrid search, rerankers, and a query router exist to find the relevant 1% of a corpus too big to read. When the whole corpus fits in a few reads, retrieval is the read.
- **The parts that CAN'T be retrofitted are cheap to build now.** If we don't snapshot competitor sites monthly starting today, that history is gone forever — no later platform can recover it. Curated URL lists, content hashes, and provenance fields cost days, not months.
- **Cost honesty:** ~1 week to build, ~$5–20/mo per client to run (compute + storage are trivial; the cost is a monthly curation glance). The full platform was estimated at ~$35–70k to build. The lite system delivers the same research answers at this client scale.

Everything below is designed so that the corpus produced by the lite system is a valid input to the full platform later (Appendix A) — the snapshots, manifests, and provenance fields ARE the ingestion format.

---

## 3. Repository Layout (Multi-Tenant)

One corpus repository (or one directory tree under the Novastacks estate), organized per project:

```text
content-intelligence/
├── PLAN.md                        # this file
├── tools/
│   ├── snapshot.py                # Playwright snapshot script (§5)
│   └── sf_import.py               # Screaming Frog export import adapter (§6.3)
└── projects/
    └── gofreight/
        ├── project.yaml           # project config: sites, roles, cadence
        ├── urls/                  # curated URL lists (§4), versioned with the repo
        │   ├── gofreight.txt
        │   ├── cargowise.txt
        │   ├── magaya.txt
        │   ├── descartes.txt
        │   └── freightpop.txt
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
- URL lists and manifests are committed to git. Raw HTML snapshots are committed too at this scale (~500 pages/month/project is well within git comfort); if a project's snapshots outgrow the repo, move HTML to object storage and keep paths in the manifest — the manifest schema (§6) already carries paths, so nothing else changes.
- Do not hard-code a competitor count anywhere. `project.yaml` lists sites; the tools iterate over whatever is listed.

`project.yaml` example:

```yaml
project: gofreight
sites:
  - name: GoFreight
    role: brand
    domain: gofreight.com
    urls: urls/gofreight.txt
  - name: CargoWise
    role: competitor
    domain: cargowise.com
    urls: urls/cargowise.txt
  # ... one entry per site; any number of competitors/reference sites
cadence: monthly
```

---

## 4. Curated URL Lists

The corpus is **human-curated, not crawled**. Each site gets a plain-text URL list (~70 URLs) selected by whoever runs the project: product pages, pricing, feature pages, key blog posts, comparison pages, about/positioning pages.

Why curation instead of BFS crawling:

- At ~70 pages/site, a human picks better than a crawler filters. Curation IS the relevance model.
- It eliminates the crawler's hardest problems (scope control, trap avoidance, junk-page filtering) by not having them.
- The list is versioned in git, so "what we track and since when" is itself provenance.

Maintaining the list:

- Review at each monthly snapshot: the snapshot script reports fetch failures (404/redirects) so dead URLs get pruned, and a quick pass over the competitor's sitemap/nav catches important new pages. Budget ~15 minutes per project per month.
- Adding a URL mid-cycle is fine — the next snapshot picks it up; `first_seen` in the manifest records when tracking began.

Seeding a new project: a one-off discovery pass (sitemap fetch or a shallow Playwright crawl of nav links) proposes candidates; a human trims to the ~70 that matter. The discovery pass is a convenience script, not part of the pipeline.

---

## 5. Snapshot Script (Playwright)

One small server-native script, `tools/snapshot.py`, run monthly per project:

```text
for each site in project.yaml:
    for each URL in the site's list:
        fetch with Playwright (rendered DOM, JS executed)
        save raw HTML            → snapshots/<YYYY-MM>/<site>/<page>.html
        convert to markdown      → snapshots/<YYYY-MM>/<site>/<page>.md
        compute content hash     → manifest entry
write manifest.json for the run
print run report (fetched / unchanged / changed / failed)
```

Design points:

- **Playwright, rendered DOM** — carried over from Rev 2. Modern marketing sites need JS rendering; a server-native browser keeps the whole run headless and schedulable (no desktop app in the loop).
- **Polite by construction:** honor robots.txt, rate-limit per domain (1 request every few seconds is fine — 70 pages is minutes of work), identify with a real user agent. At this volume there is no load concern, but the manners are non-negotiable.
- **Markdown conversion** strips navigation, footer, cookie banners, and repeated UI, keeping headings, body text, lists, tables, and FAQ content. This is the representation Claude reads; the raw HTML is the representation we preserve (never discard the original).
- **Content hash** is computed over the normalized markdown (not raw HTML), so cosmetic template changes don't register as content changes.
- **Failures don't block the run:** a 404/timeout is recorded in the manifest with its status and the run continues. The run report lists failures for the curation pass (§4).

Effort: this script plus the manifest writer is ~2–3 days of the ~1 week build.

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

`crawler` + `adapter_version` on every run, `fetched_at` + `content_hash` on every page. This is what makes month-over-month diffs trustworthy: when we compare snapshots, we can distinguish a real content change from an artifact of switching or upgrading the fetcher (rendered vs. raw HTML differences would otherwise show up as phantom changes). Any analysis output must cite `url` + `snapshot` so claims trace to an exact page at an exact date.

### 6.3 Screaming Frog: import adapter

Screaming Frog stays useful for its SEO fields and for sites where a human has already run a crawl. `tools/sf_import.py` takes a manual SF export (CSV + saved rendered HTML), maps it into the same snapshot directory layout and manifest schema, and stamps `crawler: screaming_frog` with its own `adapter_version`. A human runs SF, exports, drops the files in a folder; the importer does the rest. No SF automation is assumed or required — if SF automation matures later, only the importer's input mechanism changes.

---

## 7. Versioning & Change Detection

- **Never overwrite a snapshot.** Each month is a new `snapshots/<YYYY-MM>/` directory; history accumulates. This is the property that can't be retrofitted — the reason to build the lite system now rather than wait for the platform.
- **Unchanged pages are cheap:** if `content_hash` matches the previous snapshot, the manifest marks the page unchanged. (Store the HTML anyway at this scale — dedup is an optimization we don't need yet, and full monthly directories keep every snapshot self-contained.)
- **Diffing is a read, not a subsystem:** "what changed on CargoWise since June" = compare two manifests for changed hashes, then read the two markdown files side by side (or hand both to Claude for a summarized diff). No section-identity matching, no diff tables — at ~70 pages/site, reading the changed pages is the diff.
- The manifest's `changed_since_previous` flag makes "show me everything that changed this month across all competitors" a one-liner.

---

## 8. Analysis Layer: Claude Reads the Corpus

There is no retrieval infrastructure. An analysis run works like this:

```text
1. Point Claude (Claude Code session or dispatched agent) at:
   projects/<slug>/snapshots/<YYYY-MM>/  +  its manifest.json
2. Claude reads the manifest to see what exists (sites, roles, pages, changes).
3. Claude reads the relevant markdown files — filtered by site/role via the
   manifest, or simply all of them (~500k tokens is fine across a few passes
   or a handful of parallel readers for a big question).
4. Claude answers with citations: every claim carries url + snapshot date.
```

What this supports today (the same research jobs the platform promised):

- **Compare:** "What are competitors promising around implementation?" → read the implementation/feature pages across sites, produce the themes + evidence + comparison table.
- **Gap analysis:** "What topics do competitors cover that GoFreight doesn't?" → read both sides, list the gaps.
- **Change tracking:** "What changed in competitor positioning this quarter?" → changed pages from the manifests, read old vs. new.
- **Historical:** "What was CargoWise saying about AI in January?" → read the January snapshot.

Rules that carry over unchanged from the platform design:

- Deterministic first: counts, URL lists, change lists, and filters come from the manifest (a script or a `jq` line), never from asking an LLM to count.
- No answer without provenance: analysis output cites exact URL + snapshot. Non-negotiable.
- Repeated questions become saved prompts/scripts in the project directory, so analysis quality compounds instead of being reinvented per run.

---

## 9. Operations & Cost

- **Cadence:** monthly snapshot per project (cron/launchd), plus on-demand runs before a client meeting or after a known competitor launch. Monthly is right for marketing-site drift; sub-day freshness is a platform trigger (Appendix A), not a lite feature.
- **Runtime:** ~500 pages at polite rate limits ≈ under an hour per project, unattended.
- **Human time:** ~15 min/month per project on the curation pass (§4).
- **Cost:** ~$5–20/mo per client — API tokens for the monthly analysis reads, roughly nothing for compute/storage. Build: ~1 week (snapshot script + manifest 2–3 days; SF importer ~1 day; project scaffolding, discovery-seed script, and the first end-to-end GoFreight run in the remainder).
- **Legal/manners:** honor robots.txt and rate limits; snapshots are for internal competitive research (standard practice), but take an explicit stance on ToS exposure before ever productizing snapshot-taking as a client-facing service.

---

## 10. Build Plan (~1 week)

```text
1. Scaffold projects/gofreight/ — project.yaml + curated URL lists
   (seed via sitemap discovery, human-trim to ~70/site)
2. tools/snapshot.py — Playwright fetch → raw HTML + markdown + manifest
3. Hash-based change detection against the previous snapshot
4. tools/sf_import.py — SF export → same layout + manifest
5. First full GoFreight snapshot; verify manifest + spot-check markdown quality
6. First analysis run (the §12 acceptance question) with citations
```

Order matters only in that the manifest schema (§6) is frozen before the SF importer is written — both writers target the same contract.

---

## 11. Engineering Rules

Carried forward from Rev 2, trimmed to what the lite system needs:

1. **Never throw away raw source content.** Raw HTML is preserved alongside every markdown rendering.
2. **Never overwrite historical snapshots.** Every run is a new directory.
3. **Never let an analysis claim exist without provenance.** URL + snapshot date on everything.
4. **Never hard-code competitor counts or per-client logic.** Projects are directories + config.
5. **Never depend on one fetcher's internals.** Everything downstream reads the manifest contract; Playwright and the SF importer are peers behind it.
6. **Deterministic before LLM.** Counts, filters, and change lists come from the manifest, not from a model.
7. **Curation is the corpus.** If a page isn't worth a human adding it to the list, it isn't worth snapshotting.

---

## 12. Definition of Done

The lite system is done when, for the GoFreight project, we can ask:

> What are competitors promising around implementation?

and get back themes + evidence + a brand-vs-competitor comparison in which **every claim cites an exact URL and snapshot date**, produced by Claude reading that month's snapshot directory — with zero infrastructure beyond the repo, the snapshot script, and a scheduled monthly run.

And, three months in: the same question answered against a *historical* snapshot, and a "what changed this quarter" read across manifests — proving the versioning discipline paid for itself.

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
