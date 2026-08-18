#!/usr/bin/env python3
"""Build the web version of the invitation as a self-contained HTML page.

Shares its copy, palette and ornament with build.py so the card and the page
cannot drift apart. Three things differ, because the medium does:

- the headline ships as outline paths rather than live text, so it fills the
  column exactly at any viewport width with no font-loading flash
- the sandstone speckle is one seamless tiling PNG instead of several thousand
  SVG circles, which would be that many DOM nodes for no visible gain
- the phone number and the address are actionable
"""
from __future__ import annotations

import base64
import io
import random
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image

import build as card

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

CONTENT_W = card.CONTENT_W
GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2"
    "?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800"
    "&family=IBM+Plex+Mono:wght@400&display=swap"
)


# ------------------------------------------------------------------ helpers ---


def data_uri(payload: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}"


def svg_wrap(body: str, x: float, y: float, w: float, h: float,
             cls: str = "", extra: str = "") -> str:
    return (f'<svg class="{cls}" viewBox="{card.f(x)} {card.f(y)} {card.f(w)} '
            f'{card.f(h)}" role="presentation" aria-hidden="true" {extra}>'
            f"{body}</svg>")


# ----------------------------------------------------------------- headline ---


def headline_svg() -> str:
    """CORTISOL / DOWN as outline paths, with the falling trend line.

    Drawing the glyphs as paths pins the flush-to-both-edges fit that the print
    card calibrates for — the page can then scale the whole thing with a
    viewBox and it stays exact at every width.
    """
    face = TTFont(card.FONT_FILES[card.DISPLAY])
    glyphs = face.getGlyphSet()
    cmap = face.getBestCmap()
    upem = face["head"].unitsPerEm
    hmtx = face["hmtx"]

    size, _ = card.fit_ink_flush(card.DISPLAY, card.HEADLINE[0], CONTENT_W,
                                 card.TIGHT_TRACK)
    scale = size / upem
    track = card.TIGHT_TRACK * size
    cap = card.cap_per_em(card.DISPLAY) * size
    lead = size * 0.90

    def line_paths(text: str, baseline: float) -> tuple[list[str], float, float]:
        cursor = 0.0
        out: list[str] = []
        lo, hi = None, None
        for ch in text:
            name = cmap[ord(ch)]
            pen = SVGPathPen(glyphs)
            glyphs[name].draw(pen)
            d = pen.getCommands()
            if d:
                out.append(
                    f'<path d="{d}" transform="translate({card.f(cursor)},'
                    f'{card.f(baseline)}) scale({scale:.6f},{-scale:.6f})"/>'
                )
                xmin, xmax = glyph_extent(glyphs, name, scale)
                lo = cursor + xmin if lo is None else min(lo, cursor + xmin)
                hi = cursor + xmax if hi is None else max(hi, cursor + xmax)
            cursor += hmtx[name][0] * scale + track
        return out, (lo or 0.0), (hi or 0.0)

    base1, base2 = cap, cap + lead
    l1, lo1, hi1 = line_paths(card.HEADLINE[0], base1)
    dx = -lo1  # slide so the first line's ink starts exactly at x = 0
    l2, _, hi2 = line_paths(card.HEADLINE[1], base2)

    # rebuild the scale factor so the ink of line one spans exactly the column
    fit = CONTENT_W / (hi1 - lo1)
    down_w = (hi2 + dx) * fit

    glyph_layer = (
        f'<g transform="scale({fit:.6f}) translate({card.f(dx)},0)" '
        f'fill="{card.INK}">{"".join(l1 + l2)}</g>'
    )

    base1, base2, cap = base1 * fit, base2 * fit, cap * fit
    lead = lead * fit
    p0 = (-8, -40)
    c1 = (CONTENT_W * 0.17, -58)
    c2 = (CONTENT_W * 0.32, -14)
    p3 = (CONTENT_W * 0.42, cap * 0.80)
    c3 = (CONTENT_W * 0.52, base1 + lead * 0.34)
    c4 = (down_w + 46, base2 - cap * 0.34)
    p5 = (down_w + 116, base2 + cap * 0.26)
    import math

    ang = math.degrees(math.atan2(p5[1] - c4[1], p5[0] - c4[0]))
    tri = "M 0 0 L -40 -20 L -28.8 0 L -40 20 Z"
    trend = (
        f'<path d="M {card.f(p0[0])} {card.f(p0[1])} '
        f"C {card.f(c1[0])} {card.f(c1[1])} {card.f(c2[0])} {card.f(c2[1])} "
        f"{card.f(p3[0])} {card.f(p3[1])} "
        f"C {card.f(c3[0])} {card.f(c3[1])} {card.f(c4[0])} {card.f(c4[1])} "
        f'{card.f(p5[0])} {card.f(p5[1])}" fill="none" stroke="{card.TERRACOTTA}" '
        f'stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="{tri}" fill="{card.TERRACOTTA}" '
        f'transform="translate({card.f(p5[0] + 12)},{card.f(p5[1] + 5)}) '
        f'rotate({card.f(ang)})"/>'
    )

    top = -72
    bottom = base2 + cap * 0.26 + 34
    return svg_wrap(glyph_layer + trend, -14, top, CONTENT_W + 28, bottom - top,
                    cls="headline")


def glyph_extent(glyphs, name: str, scale: float) -> tuple[float, float]:
    from fontTools.pens.boundsPen import BoundsPen

    pen = BoundsPen(glyphs)
    glyphs[name].draw(pen)
    if pen.bounds is None:
        return 0.0, 0.0
    return pen.bounds[0] * scale, pen.bounds[2] * scale


# ------------------------------------------------------------------ texture ---


def speckle_tile(size: int = 256) -> str:
    """A seamless porous-sandstone tile, so the page repeats one small PNG."""
    rng = random.Random(4711)
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = tile.load()
    for _ in range(size * size // 26):
        cx, cy = rng.randrange(size), rng.randrange(size)
        dark = rng.random() < 0.62
        r, g, b = (156, 127, 91) if dark else (255, 250, 240)
        a = rng.randint(10, 34) if dark else rng.randint(26, 70)
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if abs(ox) + abs(oy) == 2 and rng.random() < 0.7:
                    continue
                x, y = (cx + ox) % size, (cy + oy) % size
                fade = a if ox == oy == 0 else a // 3
                old = px[x, y]
                px[x, y] = (r, g, b, min(255, old[3] + fade))
    buf = io.BytesIO()
    tile.save(buf, "PNG", optimize=True)
    return data_uri(buf.getvalue(), "image/png")


# ---------------------------------------------------------------- ornaments ---


def band_svg() -> str:
    holder = card.Svg()
    card.carved_band(holder, 0, 0, CONTENT_W, 84)
    return svg_wrap("".join(holder.body), -1, -1, CONTENT_W + 2, 86, cls="band")


def divider_svg() -> str:
    holder = card.Svg()
    card.frangipani_divider(holder, 0, 0, CONTENT_W)
    return svg_wrap("".join(holder.body), 0, -26, CONTENT_W, 52, cls="divider")


def edge_leaves(side: str) -> str:
    """Jungle silhouettes bleeding in from one edge of the slab."""
    rng = random.Random(90210 if side == "left" else 31337)
    parts = []
    for i in range(7):
        cy = 90 + i * 150 + rng.uniform(-30, 30)
        if i % 3 == 1:
            shape, scale = card.monstera(rng.uniform(120, 170)), None
            deg = (128 if side == "left" else -128) + rng.uniform(-18, 18)
        else:
            shape = card.palm_frond(rng.uniform(210, 320))
            deg = (122 if side == "left" else -122) + rng.uniform(-22, 22)
        cx = -18 if side == "left" else 218
        parts.append(
            f'<g transform="translate({card.f(cx)},{card.f(cy)}) '
            f'rotate({card.f(deg)})" fill="{card.JUNGLE}" '
            f'opacity="{card.f(rng.uniform(0.075, 0.13))}">{shape}</g>')
    return svg_wrap("".join(parts), 0, 0, 200, 1160, cls=f"leaves leaves--{side}")


# --------------------------------------------------------------------- page ---


def photo_figures() -> str:
    out = []
    w = int(CONTENT_W * card.PHOTO_SCALE)
    h = int(card.PHOTO_H * card.PHOTO_SCALE)
    for photo in card.PHOTOS:
        uri = data_uri(
            _jpeg(card.prepare_photo_image(photo, w, h)), "image/jpeg")
        out.append(
            f'<figure class="shot">{divider_svg()}'
            f'<figcaption>{escape(photo.caption)}</figcaption>'
            # no loading="lazy": the bytes are already inline, so it only delays
            # the decode and leaves the lower frames blank in a full-page capture
            f'<img src="{uri}" width="{w}" height="{h}" decoding="async" '
            f'alt="{escape(photo.caption.title())} at The Calla Project"></figure>'
        )
    return "".join(out)


def _jpeg(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=card.JPEG_QUALITY, optimize=True,
            progressive=True)
    return buf.getvalue()


MAPS = "https://maps.google.com/?q=271A+Holland+Ave+Singapore+278991"


def details_rows() -> str:
    rows = []
    for label, value, sub in card.DETAILS:
        if label == "RSVP":
            digits = value.split()[0]
            body = (f'<a class="link" href="tel:+65{digits}">{escape(digits)}</a>'
                    f'{escape(value[len(digits):])}')
        else:
            body = escape(value)
        extra = ""
        if sub:
            extra = (f'<a class="sub link" href="{MAPS}" target="_blank" '
                     f'rel="noopener">{escape(sub.upper())}</a>')
        rows.append(f'<dt>{escape(label)}</dt><dd>{body}{extra}</dd>')
    return "".join(rows)


def build_page() -> str:
    # The card's line break is hand-set for a fixed 872px column; in a fluid one
    # it strands "and / one". Same sentence, wrapped by the browser instead.
    closing = f"<p>{escape(' '.join(line for line, _ in card.CLOSING))}</p>"
    return f"""<title>Cortisol Down</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{GOOGLE_FONTS}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
  --sandstone:{card.SANDSTONE}; --ink:{card.INK}; --muted:{card.MUTED};
  --terracotta:{card.TERRACOTTA}; --gold:{card.GOLD}; --jungle:{card.JUNGLE};
  --ground:{card.GROUND};
  --display:"Bricolage Grotesque","Helvetica Neue",Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Consolas,monospace;
  --track:0.14em;
  --pad:clamp(20px,5.4vw,58px);
}}
*,*::before,*::after {{ box-sizing:border-box; }}
html {{ -webkit-text-size-adjust:100%; }}
body {{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:var(--display); line-height:1.5;
  padding:clamp(10px,2.4vw,46px) clamp(8px,2.4vw,46px);
  overflow-x:hidden;
}}
.slab {{
  position:relative; max-width:988px; margin:0 auto; isolation:isolate;
  background:var(--sandstone);
  background-image:url("{speckle_tile()}");
  border-radius:6px;
  outline:1.8px solid rgba(176,128,40,.85); outline-offset:-1px;
  padding:var(--pad);
  box-shadow:0 24px 70px rgba(0,0,0,.42);
}}
/* lantern falling from above, a softer pool at the foot */
.slab::before, .slab::after {{
  content:""; position:absolute; left:0; right:0; pointer-events:none; z-index:0;
}}
.slab::before {{
  top:0; height:34%; border-radius:6px 6px 0 0;
  background:radial-gradient(120% 100% at 50% 0%,
    rgba(255,239,203,.85) 0%, rgba(255,227,174,.30) 45%, rgba(255,227,174,0) 100%);
}}
.slab::after {{
  bottom:0; height:26%; border-radius:0 0 6px 6px;
  background:radial-gradient(110% 100% at 50% 100%,
    rgba(255,231,188,.5) 0%, rgba(255,231,188,0) 100%);
}}
.keyline {{
  position:absolute; inset:9px; border:1px solid rgba(176,128,40,.5);
  border-radius:3px; pointer-events:none; z-index:2;
}}
.inner {{ position:relative; z-index:1; }}
.leaves {{
  position:absolute; top:0; width:min(200px,26vw); height:100%;
  pointer-events:none; z-index:0;
}}
.leaves--left {{ left:0; }}
.leaves--right {{ right:0; }}
svg {{ display:block; width:100%; height:auto; }}

.eyebrow {{
  display:flex; align-items:center; gap:26px;
  margin:clamp(28px,5vw,58px) 0 0;
  font-family:var(--mono); font-size:clamp(11px,2.1vw,23px);
  letter-spacing:var(--track); color:var(--muted); text-transform:uppercase;
}}
.eyebrow::before, .eyebrow::after {{
  content:""; flex:1; height:1px; background:rgba(176,128,40,.4);
}}
.eyebrow span {{ white-space:nowrap; }}

.headline {{ margin-top:clamp(22px,4.4vw,50px); }}

.subhead {{
  font-weight:600; font-size:clamp(19px,4.35vw,47px); line-height:1.16;
  letter-spacing:-0.012em; margin:clamp(20px,3.8vw,44px) 0 0;
  text-wrap:balance;
}}
.dateline {{
  font-family:var(--mono); font-size:clamp(11px,2.35vw,25px);
  letter-spacing:var(--track); color:var(--terracotta);
  text-transform:uppercase; margin:clamp(12px,2.2vw,26px) 0 0;
}}

.shots {{ margin-top:clamp(28px,5vw,58px); }}
.shot {{ margin:0; padding-top:clamp(24px,4.6vw,52px); }}
.shot figcaption {{
  font-family:var(--mono); font-size:clamp(10px,1.95vw,21px);
  letter-spacing:var(--track); color:var(--gold); text-transform:uppercase;
  margin:clamp(16px,2.9vw,34px) 0 clamp(10px,1.9vw,22px);
}}
.shot img {{
  display:block; width:100%; height:auto; aspect-ratio:872/600;
  object-fit:cover; border:1.2px solid rgba(176,128,40,.65);
}}

.divider {{ overflow:visible; }}

.facts {{
  display:grid; grid-template-columns:minmax(96px,150px) 1fr;
  align-items:baseline; column-gap:clamp(8px,1.6vw,18px); row-gap:0;
  margin:clamp(24px,4.4vw,50px) 0 0;
}}
.facts dt {{
  font-family:var(--mono); font-size:clamp(10px,1.87vw,20px);
  letter-spacing:var(--track); color:var(--muted); text-transform:uppercase;
  padding-block:clamp(8px,1.5vw,17px);
}}
.facts dd {{
  margin:0; font-weight:600; font-size:clamp(17px,3.7vw,40px);
  line-height:1.12; padding-block:clamp(6px,1.15vw,13px);
}}
.facts .sub {{
  display:block; font-family:var(--mono); font-weight:400;
  font-size:clamp(10px,1.95vw,21px); letter-spacing:var(--track);
  color:var(--muted); text-transform:uppercase; line-height:1.5;
  margin-top:clamp(5px,1vw,11px);
}}

.closing {{ margin:clamp(26px,4.6vw,52px) 0 0; }}
.closing p {{
  margin:0; font-weight:600; font-size:clamp(21px,4.7vw,51px);
  line-height:1.34; letter-spacing:-0.012em; text-wrap:balance;
}}

.link {{ color:inherit; text-decoration-color:rgba(176,128,40,.75);
  text-underline-offset:0.16em; }}
.link:hover {{ color:var(--terracotta); }}
.link:focus-visible {{
  outline:2px solid var(--terracotta); outline-offset:3px; border-radius:2px;
}}

.foot {{ margin-top:clamp(26px,4.6vw,52px); }}

@media (max-width:560px) {{
  .facts {{ grid-template-columns:1fr; }}
  .facts dt {{ padding-block:14px 0; }}
  .facts dd {{ padding-block:0; }}
  .eyebrow {{ gap:14px; font-size:11px; }}
}}
@media (prefers-reduced-motion:no-preference) {{
  .slab {{ animation:rise .7s cubic-bezier(.22,.68,.32,1) both; }}
  @keyframes rise {{ from {{ opacity:0; transform:translateY(14px); }} }}
}}
</style>

<main class="slab">
  <div class="keyline"></div>
  {edge_leaves("left")}
  {edge_leaves("right")}
  <div class="inner">
    {band_svg()}
    <p class="eyebrow"><span>{escape(card.EYEBROW)}</span></p>
    <h1 class="visually-hidden" style="position:absolute;width:1px;height:1px;
      overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap">Cortisol Down</h1>
    {headline_svg()}
    <p class="subhead">{escape(card.SUBHEAD)}</p>
    <p class="dateline">{escape(card.DATELINE.upper())}</p>

    <div class="shots">{photo_figures()}</div>

    <div class="foot">{divider_svg()}</div>
    <dl class="facts">{details_rows()}</dl>

    <div class="foot">{divider_svg()}</div>
    <div class="closing">{closing}</div>

    <div class="foot">{divider_svg()}</div>
    <div class="foot">{band_svg()}</div>
  </div>
</main>
"""


PAGES_URL = "https://goblin2929.github.io/cortisol-down/"


def preview_jpeg() -> bytes:
    """A 1200x630 link-preview crop, so the URL unfurls as the invitation.

    Taken from the rendered card rather than the web page: same artwork, and it
    is already sitting at full resolution.
    """
    import json

    src = Image.open(OUT / "invite.png").convert("RGB")
    layout = json.loads((OUT / "layout.json").read_text())
    heads = [b for b in layout["boxes"] if b["name"].startswith("headline:")]
    # biased up so the frame ends in clear space under the arrowhead rather
    # than slicing through the subhead
    mid = (min(b["y0"] for b in heads) + max(b["y1"] for b in heads)) / 2 - 64

    target_h = round(src.width * 630 / 1200)
    top = max(0, min(round(mid - target_h / 2), src.height - target_h))
    crop = src.crop((0, top, src.width, top + target_h))
    crop = crop.resize((1200, 630), Image.LANCZOS)
    buf = io.BytesIO()
    crop.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    return buf.getvalue()


def standalone(body: str) -> str:
    """Wrap the page for GitHub Pages.

    The artifact host supplies a document skeleton; a file served straight off
    Pages has to bring its own, plus the link-preview tags that make the URL
    unfurl properly when it is pasted into a chat.
    """
    head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<!-- an invitation for one group of people, not something to be found in search -->
<meta name="robots" content="noindex, nofollow">
<meta property="og:type" content="website">
<meta property="og:title" content="Cortisol Down">
<meta property="og:description" content="{escape(card.SUBHEAD)} {escape(card.DATELINE)}">
<meta property="og:url" content="{PAGES_URL}">
<meta property="og:image" content="{PAGES_URL}preview.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="{card.GROUND}">
"""
    return head + body + "</head>\n<body>\n</body>\n</html>\n"


def main() -> None:
    import sys

    OUT.mkdir(exist_ok=True)
    page = build_page()
    path = OUT / "invite.html"
    path.write_text(page, encoding="utf-8")
    print(f"wrote {path.relative_to(HERE)}  {len(page.encode()) / 1e6:.2f} MB")

    if "--pages" in sys.argv:
        # split the fragment so <style>/<meta> stay in head and markup in body
        marker = "<main class="
        head_part, _, body_part = page.partition(marker)
        doc = (standalone(head_part).replace("</head>\n<body>\n</body>\n</html>\n",
                                             "</head>\n<body>\n")
               + marker + body_part + "</body>\n</html>\n")
        out = HERE / "index.html"
        out.write_text(doc, encoding="utf-8")
        print(f"wrote {out.relative_to(HERE)}  {len(doc.encode()) / 1e6:.2f} MB")

        jpg = HERE / "preview.jpg"
        jpg.write_bytes(preview_jpeg())
        print(f"wrote {jpg.relative_to(HERE)}  {jpg.stat().st_size / 1e3:.0f} kB")


if __name__ == "__main__":
    main()
