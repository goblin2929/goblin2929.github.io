# Expired / repurposed .sg domains as an SEO affiliate play

Working notes. Status: **thesis, partially verified.** Written 26 Aug 2026.

---

## 1. The observation: thebespokeclub.sg

`thebespokeclub.sg` used to be a **bespoke tailoring boutique** — suits, shirts,
made-to-measure, Savile Row positioning, private suite with a single malt.
It is now a **landscaping and garden maintenance company**. Same domain, same
brand name, entirely different industry.

**Verified** (via search, 26 Aug 2026):

| | Old (tailoring) | Now (landscaping) |
|---|---|---|
| Address | 17 Carpenter Street #04-01, S059906 | BLK 627 Bukit Batok Central #01-6368, S650627 |
| Phone | +65 6224 0609 | +65 8305 3314 |
| Email | (boutique enquiry address) | hello@thebespokeclub.sg |
| Live URLs | `/boutique/`, `/bespoke/`, `/product-category/shirts/`, `/promotions/` | `/services/`, `/services/indoor-landscaping/`, `/landscaping-maintenance-contracts/`, `/starting-a-garden-singapore/` |

Different premises, different number, different service line. This is a new
operator on an old domain — not the original tailor pivoting into plants.

**Not verified:** whether it was *bought* (private sale / drop-catch) or
transferred some other way. "Bought by a landscaper" is the working assumption,
not an established fact. See §5 for how to close that gap.

---

## 2. Why this particular domain was worth taking

Three things line up, and all three have to line up for the play to work:

1. **Aged .sg with real press equity.** The tailoring business earned genuine
   editorial links and citations — Time Out Singapore, local shopping
   directories, ZoomInfo, an Instagram and Facebook presence. That is a
   referring-domain profile a new landscaping site cannot buy honestly.

2. **The brand name is category-agnostic.** This is the actual insight.
   "The Bespoke Club" carries no industry in it. *Bespoke tailoring* →
   *bespoke landscaping* is a legal move; the existing brand-name anchor text
   ("The Bespoke Club", "thebespokeclub.sg") keeps pointing at something that
   still makes sense. If the domain had been `carpenterstreettailors.sg`, every
   inherited anchor would read as a mismatch and the equity would be dead weight.

3. **Search still remembers it.** Old boutique URLs are *still indexed* alongside
   the new landscaping pages — the index has not fully turned over. Whoever took
   this over inherited a domain Google already trusts and already crawls often.

The transferable rule: **the asset is not the traffic, it's the name's
portability across the link graph.** Screen dropped domains for names that
survive a category change.

---

## 3. Where this breaks

Do not treat inherited authority as free. The honest risks:

- **Topical reset.** Google discounts links whose surrounding context no longer
  matches the site's subject. Fashion-press links pointing at a landscaping site
  decay in value — not to zero, but the "DR 40 for free" framing is a fantasy.
- **Anchor mismatch.** Historic anchors are apparel-flavoured. They help brand
  queries, not `landscaping singapore`.
- **404 debt.** The old product URLs will die eventually. Redirecting
  `/product-category/shirts/` → `/services/` is an irrelevant redirect and gets
  treated as a soft 404.
- **Reputation carryover.** You inherit the previous owner's review history,
  trademark exposure, and any spam the domain accumulated while parked.

The genuinely durable inheritance is narrower than it looks: **domain age,
crawl familiarity, and brand-name recognition.** Everything topical has to be
re-earned.

---

## 4. The affiliate angle

The pattern generalises to an affiliate site build:

1. **Screen SG drops for category-agnostic names.** Filter on: pronounceable
   English brand name, no industry noun locked in, .sg or .com.sg, prior real
   business (not a parked flip), referring domains from editorial rather than
   directories.
2. **Pick the destination niche to fit the inherited anchors,** not the other way
   round. Look at what the old anchors actually say, then choose a vertical those
   anchors can plausibly support.
3. **Rebuild, don't redirect.** New content on the same domain (what the
   landscaper did) beats 301'ing the old domain into a money site. Redirects
   across a topical gap are the single most common way these get flagged.
4. **Affiliate fit is best where SG intent is high and merchant programs exist:**
   home services lead-gen, insurance/finance comparison, travel, tuition,
   equipment rental. Landscaping is itself lead-gen — this operator may already
   be monetising exactly this way.
5. **Bring the old brand forward honestly.** Do not impersonate the previous
   business or imply continuity of the old operation. Reuse the *name*, not the
   *identity*. Anything that claims to still be the old company is a trademark
   and consumer-deception problem, not an SEO tactic.

---

## 5. To verify before acting on any of this

Blocked in this session — the Ahrefs plan available here returns
`Insufficient plan` for Site Explorer backlinks/DR endpoints, and direct fetches
to `thebespokeclub.sg` are blocked by the network egress proxy.

- [ ] SGNIC WHOIS — registrant change and date. Confirms sale vs. pivot.
- [ ] Wayback Machine — pin the month the site flipped from tailoring to landscaping.
- [ ] Ahrefs Site Explorer (on a plan with backlinks access) — referring domains,
      DR history, and whether DR fell after the flip. **DR trajectory across the
      transition is the whole ballgame** for whether this pattern is repeatable.
- [ ] Ahrefs organic keywords — is it ranking for landscaping terms, or coasting
      on brand queries?
- [ ] Check what the old boutique URLs return now (200 / 301 / 404).

---

## Sidebar: stock imagery

**Unsplash over Pexels** for client and staging pages. Better editorial quality,
less of the over-saturated stock look. Watch the licence on both — Unsplash
allows commercial use without attribution but does not clear model or property
releases, so no identifiable faces or branded storefronts in client work.

---

## Open thread

"blood and done seminar.com domain searching" from the original note is
unresolved — could not decode whether that is a domain to look at, a project
codename, or a note that a seminar-domain search is already finished. Needs a
sentence from Tina before it goes anywhere.
