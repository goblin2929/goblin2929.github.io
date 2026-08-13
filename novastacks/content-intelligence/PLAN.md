# Multi-Brand AI Content Intelligence & Competitive Research System

> **Rev 2 — 13 Aug 2026.** Crawler strategy changed: **Playwright is the primary (bootstrap) crawler**; Screaming Frog is now an **import adapter**, not the pipeline backbone (its automation setup isn't ready, and a desktop app shouldn't gate a multi-tenant cloud pipeline). See §9. Everything downstream consumes one normalized crawl contract, so crawlers stay swappable (Rule 7).

## 1. Objective

Build a reusable content intelligence system for Novastacks that ingests websites belonging to:

- Client brands
- Competitors
- Industry/reference websites
- Publishers/media
- Other websites relevant to a specific research project

The system must support both:

### Human use

A human should be able to:

- Search all collected content
- Search within a specific brand
- Compare brands
- Filter by topic, page type, language, date, competitor, etc.
- Inspect the original page
- Read the relevant section surrounding a match
- See why a result was retrieved
- Compare multiple pages side by side
- Export results
- Ask natural-language questions
- Save useful queries/research findings

### AI use

An AI agent should be able to:

- Search the corpus semantically
- Search exact terms
- Filter by metadata
- Retrieve relevant sections rather than entire pages
- Compare multiple brands
- Identify themes and gaps
- Analyze claims and positioning
- Detect changes between crawls
- Answer questions with citations to the exact source pages
- Perform structured analysis across hundreds/thousands of pages

The system should be multi-tenant / multi-project from day one.

Do NOT build a single database specifically for one client.

---

# 2. Core Design Principle

Do not think:

> "Scrape websites and put them into a vector database."

Think:

> "Build a versioned research corpus with structured documents, searchable text, semantic indexes, relationships and provenance."

The architecture should look like:

```text
                    ┌──────────────────┐
                    │  Brand / Project │
                    └────────┬─────────┘
                             │
                             ▼
                     Crawl Configuration
                             │
                             ▼
                    ┌──────────────────────┐
                    │   Crawler Adapters   │
                    │ Playwright (primary) │
                    │ Screaming Frog import│
                    │ Firecrawl / others   │
                    └────────┬─────────────┘
                             │
                             ▼
                Normalized Crawl Output (contract)
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
          Raw HTML       Clean Content    SEO Data
              │              │           (optional)
              └──────────────┼──────────────┘
                             ▼
                     Document Pipeline
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
           Sections        Chunks       Metadata
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                   AI Enrichment Pipeline
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
           Entities        Topics        Claims
                             │
                             ▼
                   Search / Retrieval Layer
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
          Full Text       Vector          Metadata
          Search          Search           Filters
             │               │               │
             └───────────────┼───────────────┘
                             ▼
                       Human UI / AI
```

---

# 3. Multi-Tenant Data Model

Every object must belong to a `workspace_id` or `project_id`.

Recommended hierarchy:

```text
Workspace
    └── Project
          ├── Brand
          ├── Competitors
          ├── Reference Sites
          ├── Crawl Jobs
          ├── Documents
          ├── Document Versions
          ├── Sections
          ├── Chunks
          ├── Entities
          ├── Topics
          ├── Claims
          └── Research Queries
```

Example:

```text
Workspace: Novastacks

Project: GoFreight Competitive Intelligence

Brand:
    GoFreight

Competitors:
    CargoWise
    Magaya
    Descartes
    FreightPOP
    ...

Reference:
    industry publications
    logistics blogs
    analyst sites
```

Another project may have:

```text
Project: Fintech Client A

Brand:
    Client A

Competitors:
    5 competitors

Reference:
    50 industry sites
```

The system must not assume that every project has the same number of competitors.

---

# 4. Database

Use PostgreSQL as the primary application database.

Use:

- PostgreSQL
- pgvector
- PostgreSQL full-text search initially
- Object storage for raw HTML/assets

Do NOT introduce Pinecone/Qdrant/Elasticsearch unless there is a demonstrated scaling problem.

At the initial scale, PostgreSQL + pgvector + full-text search is sufficient.

Note on pgvector at scale: pre-filter by `project_id` / metadata in the SQL predicate *before* the vector search (not post-hoc), and use HNSW indexes with deliberate tuning once chunk counts reach the millions.

---

# 5. Core Tables

## projects

```text
id
workspace_id
name
description
created_at
updated_at
```

## sources

Represents a website/domain.

```text
id
project_id
domain
name
source_type
role
language
country
is_active
created_at
```

role examples:

```text
brand
competitor
reference
publisher
industry
other
```

Do not hard-code a maximum competitor count.

---

## crawl_jobs

```text
id
project_id
source_id
started_at
completed_at
status
crawler            -- playwright | screaming_frog | firecrawl | ...
adapter_version    -- version of the adapter that produced this crawl
url_count
success_count
error_count
crawl_config
```

`crawler` + `adapter_version` are required provenance: when comparing crawls over time, we must be able to tell a real content change from an artifact of switching crawlers (e.g., rendered vs. raw HTML differences would otherwise show up as phantom diffs in §23).

---

## documents

A canonical page independent of crawl version.

```text
id
project_id
source_id
canonical_url
url
path
page_type
language
first_seen_at
last_seen_at
current_version_id
status
```

Important:

A URL is NOT the same thing as a document version.

---

# 6. Document Versioning

Every crawl creates a version.

Example:

```text
documents
    │
    ├── version 1 — Jan 2026
    ├── version 2 — Apr 2026
    ├── version 3 — Aug 2026
    └── version 4 — Nov 2026
```

Table:

## document_versions

```text
id
document_id
crawl_job_id

content_hash
html_hash

raw_storage_path
clean_text
markdown

title
meta_description

h1
word_count

published_at
modified_at

http_status
canonical_url

created_at
```

Never overwrite the historical version.

If the content hasn't changed:

```text
content_hash == previous_hash
```

then don't regenerate embeddings or expensive AI enrichment.

---

# 7. Raw Storage

Store raw HTML outside PostgreSQL.

Use:

- S3
- Cloudflare R2
- Supabase Storage
- equivalent object storage

Example:

```text
/project_id/
    /source_id/
        /document_id/
            /crawl_id/
                raw.html
                screenshot.png
                rendered.html
```

The database stores the storage path.

Never make the raw HTML the primary searchable representation.

---

# 8. Content Normalization

For every page create:

### Raw HTML

Preserve the original.

### Clean HTML

Remove:

- navigation
- footer
- cookie banners
- ads
- repeated UI
- unrelated widgets

### Markdown

Create a clean LLM-readable representation.

Example:

```markdown
# Enterprise Freight Management

Introductory paragraph...

## Automated Documentation

...

## Pricing

...

## Implementation

...
```

### Structured page representation

Store:

```json
{
  "title": "...",
  "h1": "...",
  "headings": [],
  "sections": [],
  "paragraphs": [],
  "lists": [],
  "tables": [],
  "faqs": [],
  "links": [],
  "images": [],
  "schema": []
}
```

---

# 9. Crawler Strategy — Adapter-First

**Revised (Rev 2).** The pipeline is crawler-agnostic. Every crawler is an adapter that emits one normalized crawl output contract; everything downstream (normalization → sections → chunks → embeddings) consumes only that contract.

## 9.1 The contract comes first

Define and freeze the normalized crawl output schema before building any crawler:

```json
{
  "crawl_manifest": {
    "source_id": "...",
    "crawler": "playwright | screaming_frog | firecrawl",
    "adapter_version": "1.0.0",
    "started_at": "...",
    "config": {}
  },
  "pages": [{
    "url": "...",
    "final_url": "...",
    "http_status": 200,
    "fetched_at": "...",
    "raw_html_path": "s3://...",
    "rendered_html_path": "s3://... | null",
    "title": "...",
    "meta_description": "...",
    "h1": "...",
    "canonical_url": "...",
    "headers": {},
    "links": [],
    "extractions": {},
    "seo": {}
  }]
}
```

The schema has a small **required core** (url, http_status, raw_html_path, title, fetched_at) plus **optional** `extractions` / `seo` blocks. Downstream features must degrade gracefully when the optional blocks are absent — otherwise we re-create a single-crawler dependency through the back door.

## 9.2 Primary crawler: PlaywrightAdapter

The primary (bootstrap) crawler is a server-native Playwright crawler:

- Runs natively in our workers — no desktop app, no per-seat licensing, no human-in-the-loop step
- Handles JS rendering (needed for modern marketing sites anyway)
- Raw HTML stays fully under our control (Rule 1)
- Polite by construction: robots.txt, rate limits, same-domain scoping, max-depth / max-pages caps

Scope: a polite BFS crawler is ~2–3 days of work. Ship the whole pipeline end-to-end on Playwright output first — this de-risks the hard parts (sectioning, normalization, versioning) immediately instead of blocking on Screaming Frog readiness.

## 9.3 Screaming Frog: import adapter, not runner

`ScreamingFrogAdapter` is designed around SF's **exports** (CSV/crawl exports + custom extraction outputs + saved rendered HTML), not around driving SF programmatically.

Workflow for now: a human runs the crawl in SF, exports, drops the files into a bucket/folder, and the pipeline picks them up. When the SF automation plan matures (CLI scheduling, database storage mode), only the adapter's *input mechanism* is upgraded — nothing downstream changes.

SF remains valuable for its rich SEO fields (crawl depth, inlinks, indexability, structured extraction) which populate the optional `seo` block. Configure SF custom extraction for:

```text
main content
article body
author
publish date
updated date
breadcrumbs
FAQ schema
product information
pricing
```

## 9.4 Future adapters

```text
FirecrawlAdapter
Crawl4AIAdapter
ApifyAdapter
```

All adapters output the same normalized document schema. Do NOT make the system dependent on any crawler's internal format.

---

# 10. Ingestion Pipeline

Pipeline:

```text
crawl
 ↓
crawl manifest
 ↓
raw capture
 ↓
content extraction
 ↓
normalization
 ↓
document version creation
 ↓
section extraction
 ↓
chunking
 ↓
metadata enrichment
 ↓
entity extraction
 ↓
topic classification
 ↓
claim extraction
 ↓
embedding
 ↓
indexing
```

Each stage must be independently retryable.

Do NOT create one giant script.

Use separate pipeline stages.

---

# 11. Sections

Do NOT immediately split everything into arbitrary 500-token chunks.

First identify semantic sections.

Example:

```text
Page
│
├── Introduction
├── What is freight management?
├── Key features
├── Pricing
├── Implementation
├── Integrations
├── FAQ
└── Conclusion
```

Table:

## sections

```text
id
document_version_id
parent_section_id
heading
heading_level
section_order
content
content_hash
```

This makes human retrieval much better.

When someone searches:

> pricing

show:

```text
Pricing

[full relevant section]

Source: Competitor A Enterprise Freight Management URL
```

rather than an arbitrary chunk of text.

Note: reliable semantic sectioning across thousands of different site templates is the hardest, highest-leverage part of the system — it determines the quality of retrieval, compare, and change detection. Treat it as a dedicated spike, not a routine pipeline step.

---

# 12. Chunking

Chunks exist for AI retrieval.

They should NOT be the primary user-facing object.

Recommended initial target:

```text
300–700 tokens
```

with semantic boundaries.

Avoid splitting:

- tables
- lists
- FAQs
- code
- headings from their content

A chunk should retain:

```text
project_id
source_id
document_id
document_version_id
section_id

text

heading_path

chunk_index

token_count

embedding
```

Example heading path:

```text
Enterprise Freight Management > Features > Automated Documentation
```

---

# 13. Hybrid Search

Do NOT use vector search alone.

Implement:

```text
Exact keyword search
        +
Semantic vector search
        +
Metadata filtering
        +
Optional reranking
```

Example query:

> Which competitors talk about implementation time?

Keyword search finds:

```text
implementation
deployment
go-live
setup
onboarding
```

Semantic search finds pages that discuss the concept without using exactly those words.

Then rerank the candidates.

---

# 14. Metadata Filters

Human and AI search must be able to filter:

```text
project
brand
competitor
source
source role
page type
language
country
topic
entity
date
crawl date
content status
```

Example:

```text
Project = GoFreight
Source Role = Competitor
Topic = Implementation
Language = English
```

Then search.

This is extremely important.

Do NOT send all competitors into one vector search and hope the model figures out which ones matter.

---

# 15. AI Enrichment

Do not use an LLM to summarize every page indiscriminately.

Use deterministic extraction first.

Then LLM enrichment.

For each page/section, optionally extract:

### Topics

```text
pricing
implementation
features
integrations
security
AI
automation
customer support
```

### Entities

```text
companies
products
people
technologies
industries
locations
```

### Claims

Example:

```json
{
  "claim": "Implementation can be completed within 30 days",
  "type": "implementation",
  "source_section_id": "...",
  "confidence": 0.91
}
```

### Commercial signals

Extract:

```text
pricing mentioned
free trial
demo CTA
implementation time
customer size
industry
feature claims
differentiators
guarantees
certifications
integrations
```

This is much more useful for competitive intelligence than generic summaries.

---

# 16. Human Search UI

The UI should NOT look like a generic ChatGPT box.

Have two modes:

## Explore

A search interface.

Example:

```text
Search competitor content...

[ implementation time ]

Filters:

Source ☑ Competitors ☐ Brand ☐ Reference

Topic ☑ Implementation

Date [ Any ]

Language [ English ]

--------------------------------

42 results

CargoWise Implementation "...implementation can..."

Magaya Implementation "...deployment..."

Descartes Onboarding "...customers can..."
```

Clicking a result opens the source page representation.

---

# 17. Source Viewer

When a user clicks a result, show:

```text
SOURCE

Magaya Enterprise TMS

URL https://...

Crawl date 13 Aug 2026

Page type Product page


RELEVANT SECTION

Implementation

[full section]


CONTEXT

Previous section ...

Next section ...


AI EXTRACTIONS

Topics Implementation Enterprise software

Entities Magaya

Claims ...

[Open original page]
```

The user should always be able to inspect the evidence.

---

# 18. Compare Mode

This is one of the highest-value features.

Allow:

```text
Compare:

☑ Brand ☑ Competitor A ☑ Competitor B ☑ Competitor C
```

Then:

```text
TOPIC: IMPLEMENTATION

              Brand    Comp A    Comp B    Comp C

Mentions      ✓        ✓         ✓         ✓

Implementation time
              —        30 days   4 weeks   —

Self-service  ✓        —         ✓         —

Migration     ✓        ✓         —         ✓
```

Click any cell → source evidence.

This is much more useful to a marketer than simply "chat with your documents."

---

# 19. AI Query Interface

Add a second mode:

## Ask the Corpus

Example:

> What are the five most common positioning claims competitors make around implementation?

The system should NOT simply dump everything into an LLM.

Pipeline:

```text
User question
 ↓
Query classification
 ↓
Metadata extraction
 ↓
Hybrid retrieval
 ↓
Candidate sections
 ↓
Reranking
 ↓
Evidence grouping
 ↓
LLM synthesis
 ↓
Citations
```

The answer should look like:

```text
The dominant competitor positioning falls into 4 themes:

1. Faster implementation
2. Lower migration effort
3. Dedicated onboarding
4. Integration support

### 1. Faster implementation

CargoWise... [claim]

Magaya... [claim]

Evidence: 7 pages across 4 competitors
```

Every statement should be traceable.

---

# 20. Analytical Queries

The AI layer must support more than semantic search.

Some questions require SQL/aggregation.

Example:

> How many competitor pages mention AI?

This should use structured metadata / SQL.

Not vector search.

Another:

> Which competitor has the most pages about automation?

Again:

```text
SQL aggregation
```

Another:

> What are competitors saying about automation?

Use:

```text
retrieval + LLM synthesis
```

The AI query router should determine which approach is appropriate.

---

# 21. Query Types

Implement a lightweight classifier:

```text
LOOKUP
SEARCH
COUNT
COMPARE
AGGREGATE
TREND
SUMMARIZE
SYNTHESIZE
GAP_ANALYSIS
```

Examples:

```text
"Find pages mentioning implementation" → SEARCH

"How many pages does CargoWise have?" → COUNT

"Compare pricing positioning" → COMPARE

"What changed since last crawl?" → TREND

"What topics are competitors covering that our brand isn't?" → GAP_ANALYSIS
```

---

# 22. Competitive Content Gap

Eventually support:

```text
Brand content
        VS
Competitor corpus
```

Generate:

```text
Topics competitors cover
Topics brand covers
Topics missing from brand

Competitor-only claims

Competitor-only FAQs

Competitor-only entities

Competitor content clusters
```

This is much more valuable than generic "content gap analysis."

---

# 23. Crawl History

Every crawl should produce:

```text
new pages
deleted pages
changed pages
unchanged pages
```

For changed pages calculate:

```text
title change
H1 change
content change
section change
topic change
claim change
CTA change
pricing change
```

Example:

```text
CargoWise /pricing

Previous: No public pricing

Current: "Contact us for enterprise pricing"

Change: Pricing positioning added
```

This should become queryable.

Section-level diffs require a section *identity/matching* strategy across crawls (content-hash + fuzzy heading match + embedding similarity to align old↔new sections) — section boundaries and IDs shift when a page is redesigned, and naive diffing marks everything as changed. Diffs must also account for `crawler` provenance (§5) so crawler switches don't produce phantom changes.

---

# 24. Version-Aware Retrieval

When retrieving content, support:

```text
current
latest
historical
between dates
```

Example:

> What was Competitor A saying about AI six months ago?

The system should retrieve the historical document version.

---

# 25. Cost Control

LLM calls are expensive.

Use this hierarchy:

```text
HTML parser
    ↓
regex / XPath / CSS
    ↓
SQL
    ↓
full-text search
    ↓
vector search
    ↓
reranker
    ↓
LLM
```

Only escalate to an LLM when necessary.

Do not use an LLM for:

```text
word count
title extraction
H1 extraction
URL classification
status codes
basic metadata
exact keyword matching
```

---

# 26. Embedding Strategy

Embed sections/chunks.

Do not embed:

- raw HTML
- navigation
- footer
- entire website
- giant pages

Store:

```text
embedding_model
embedding_version
embedding_dimension
embedded_at
```

This lets us re-embed the corpus later without losing track of which model generated an embedding. Plan for incremental/lazy re-embedding — re-embedding a large historical corpus on a model change is a real cost/latency event.

---

# 27. Search Ranking

Initial ranking:

```text
0.35 semantic similarity
0.25 keyword relevance
0.15 metadata relevance
0.15 source/page authority
0.10 freshness
```

Do not hard-code these permanently.

Make ranking configurable.

---

# 28. Human + AI Shared Retrieval

This is important.

The human UI and AI agent should use the same retrieval API.

For example:

```text
POST /search

POST /retrieve

POST /compare

POST /aggregate

POST /ask
```

The UI calls the same backend that the AI calls.

Do NOT create:

```text
human search database + AI vector database
```

That creates two sources of truth.

---

# 29. API

Create APIs approximately like:

```text
GET /projects

GET /sources

GET /documents

GET /documents/:id

GET /documents/:id/versions

GET /sections/:id

POST /search

POST /retrieve

POST /compare

POST /ask

POST /crawl

GET /crawl/:id/status

GET /crawl/:id/changes
```

---

# 30. AI Tool Interface

Expose tools to your agent:

```text
search_content()
get_document()
get_section()
compare_sources()
list_topics()
list_entities()
find_claims()
search_changes()
aggregate_content()
```

Example:

```text
search_content(
    project_id,
    query,
    source_roles=["competitor"],
    topics=["implementation"],
    limit=20
)
```

The AI should never need to know the underlying PostgreSQL schema.

---

# 31. Citations / Provenance

Every retrieved chunk MUST carry:

```text
project
source domain
document URL
document version
section
crawl date
```

AI answers must cite those IDs.

Example:

```text
[CargoWise — Implementation]
[Magaya — Deployment]
[Descartes — Onboarding]
```

Clicking the citation should open the exact section.

This is non-negotiable.

---

# 32. Security / Tenant Isolation

Every query must be scoped by:

```text
workspace_id
project_id
```

Never allow an AI query for Project A to retrieve Project B's documents.

Enforce tenant isolation at the database/API layer, not only in the UI.

Crawling itself must also be responsible: honor robots.txt, rate-limit per domain, and take an explicit stance on ToS/legal exposure before productizing crawls run on behalf of clients.

---

# 33. Recommended Initial Stack

Use:

```text
Crawler Playwright (primary, server-native) + Screaming Frog (import adapter)

Backend Python + FastAPI

Database PostgreSQL

Vector pgvector

Object storage Cloudflare R2 / S3

Search Postgres FTS + pgvector

Queue Redis initially

Workers Python

LLM OpenAI / Anthropic

Frontend Next.js

Charts whatever is already used by the product
```

Do not over-engineer the infrastructure at 1,000–100,000 pages.

---

# 34. First MVP

Do NOT build everything above in V1.

Build this first:

```text
1. Project creation

2. Add sources
   - brand
   - competitors
   - reference

3. Normalized crawl output contract (§9.1)

4. PlaywrightAdapter crawl (primary)

5. ScreamingFrogAdapter import (manual export drop)

6. Store raw HTML

7. Normalize page content

8. Create sections

9. Create chunks

10. Generate embeddings

11. PostgreSQL + pgvector

12. Full-text search

13. Human search UI

14. Source viewer

15. AI question interface

16. Citations

17. Basic competitor comparison

18. Crawl versioning
```

That gives us the foundation.

Build order within the MVP: contract first (item 3), then Playwright end-to-end through search UI. The SF import adapter (item 5) can land any time after the contract exists — it must never block the pipeline.

---

# 35. V2

Then add:

```text
AI topic classification

Entity extraction

Claim extraction

Content gap analysis

Change detection

Historical search

Competitive positioning analysis

Saved searches

Saved reports

Export to CSV

Export to Markdown

AI-generated research reports

Screaming Frog automation (upgrade the import adapter's input mechanism: CLI scheduling, database storage mode)
```

---

# 36. V3

Eventually:

```text
Automated competitor monitoring

Scheduled crawling

Automatic change alerts

Topic clustering

Entity graphs

Claim graphs

Content opportunity scoring

AEO-specific analysis

LLM visibility correlation

Cross-project benchmarks

Industry benchmarks
```

---

# 37. Critical Engineering Rules

### Rule 1

Never throw away raw source content.

### Rule 2

Never overwrite historical versions.

### Rule 3

Never rely exclusively on vector search.

### Rule 4

Never make chunks the primary document model.

### Rule 5

Never let AI answers exist without source provenance.

### Rule 6

Never hard-code competitor counts.

### Rule 7

Never make the architecture dependent on one crawler. All crawlers are adapters behind one normalized contract; downstream features must degrade gracefully when a crawler's optional fields are absent.

### Rule 8

Never send the entire corpus to an LLM.

### Rule 9

Human search and AI retrieval must use the same backend.

### Rule 10

Every expensive AI operation must be cacheable and versioned.

---

# 38. Definition of Done

The system is successful when a marketer can select:

```text
Project: GoFreight

Sources: Brand CargoWise Magaya Descartes FreightPOP

Topic: Implementation
```

and ask:

> What are competitors promising around implementation?

The system should return:

```text
Summary
────────

4 dominant positioning themes.

1. Faster deployment
2. Guided migration
3. Dedicated implementation support
4. Integration assistance


Evidence
────────

CargoWise [relevant section]

Magaya [relevant section]

Descartes [relevant section]


Comparison
──────────

                 Brand   CargoWise   Magaya   Descartes

Fast deployment   —        ✓          ✓          —
Migration         ✓        ✓          —          ✓
Dedicated team    ✓        ✓          ✓          —
Integration       ✓        —          ✓          ✓
```

And the marketer must be able to click any result and immediately see:

```text
exact page
exact section
exact text
crawl date
source URL
```

That is the product.

Not "a chatbot over scraped websites."

It is a searchable, versioned competitive intelligence corpus with an AI research layer on top.

Note: the full Definition of Done depends on topic + claim extraction (V2). The MVP's definition of done is the smaller loop: *filtered hybrid retrieval with clickable provenance* — search, filter by source role, open the exact section, see the crawl date and URL.
