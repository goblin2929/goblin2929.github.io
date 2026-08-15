#!/usr/bin/env python3
"""Build the "Cortisol Down" invitation card.

SVG is generated here and rasterised with cairosvg. Every text size is derived
by measuring the actual font with PIL rather than being hardcoded, and every
vertical position accumulates from a running `y` cursor, so the card height
falls out of the content at the end.

Outputs: out/invite.png, out/invite.pdf, out/invite-compact.png
"""
from __future__ import annotations

import base64
import io
import math
import random
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

import cairosvg
from PIL import Image, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
ASSETS = HERE / "assets"
OUT = HERE / "out"

# ---------------------------------------------------------------- palette ---

SANDSTONE = "#F1E5D2"
INK = "#3A2617"
MUTED = "#8B7355"
TERRACOTTA = "#BF5B33"
GOLD = "#B08028"
JUNGLE = "#26402F"
FRANGIPANI = "#FBF3E4"

GROUND = "#1B2E22"  # the darker jungle the sandstone slab sits on
CARVE_FACE = "#F0E4D0"  # relief face sits at the stone value; the emboss
#                         edges alone carry the carving, so it stays low-contrast

DISPLAY = "Bricolage800"
DISPLAY_MED = "Bricolage600"
MONO = "IBM Plex Mono"

FONT_FILES = {
    DISPLAY: FONTS / "Bricolage800.ttf",
    DISPLAY_MED: FONTS / "Bricolage600.ttf",
    MONO: FONTS / "IBMPlexMono-Regular.ttf",
}

MONO_TRACK = 0.14  # em
TIGHT_TRACK = -0.035  # em, display headline

# ----------------------------------------------------------------- canvas ---

CANVAS_W = 1080
MARGIN = 46  # ground visible around the slab
CONTENT_W = 872  # authoritative measuring width
CONTENT_X = (CANVAS_W - CONTENT_W) // 2  # 104
CARD_X = MARGIN
CARD_W = CANVAS_W - 2 * MARGIN
CARD_TOP = MARGIN
PAD_TOP = CONTENT_X - CARD_X  # 58, the inner padding that 872 implies
PAD_BOTTOM = PAD_TOP

PHOTO_H = 600
PHOTO_SCALE = 1.6  # render photos at 1.6x display size so they stay sharp
JPEG_QUALITY = 86

RNG = random.Random(20260826)

# ------------------------------------------------------------------- copy ---

EYEBROW = "THANK GOD SUMMER IS OVER · VOL. II"
HEADLINE = ["CORTISOL", "DOWN"]
SUBHEAD = "A moms-only evening at The Calla Project."
DATELINE = "Wednesday 26 August · 6–9 pm"

DETAILS = [
    ("WHEN", "Wednesday 26 August"),
    ("TIME", "6 – 9 pm"),
    ("WHERE", "The Calla Project"),
    ("BRING", "A swimsuit. That's it."),
    ("FOOD", "Good food, light and clean"),
    ("WHO", "Moms. All of you."),
]

CLOSING = [
    ("Nothing to buy.", TERRACOTTA),
    ("No toys, no catalogue, no starter kit.", TERRACOTTA),
    ("Sauna, food, good company — and one", INK),
    ("evening of nobody needing you.", INK),
]


@dataclass
class Photo:
    filename: str
    caption: str
    # pre-crop box as fractions of the exif-corrected source (l, t, r, b),
    # applied *before* fitting so unwanted regions leave the frame entirely
    precrop: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)
    # ImageOps.fit centering, applied to whatever axis is actually trimmed
    centering: tuple[float, float] = (0.5, 0.5)


PHOTOS = [
    Photo("sauna.jpeg", "THE SAUNA", centering=(0.5, 0.52)),
    # the right half of this frame is a person facing camera; pre-crop removes
    # her entirely, which centering alone cannot do on a landscape source
    Photo("cold-plunge.jpeg", "THE COLD PLUNGE", precrop=(0.0, 0.0, 0.505, 1.0),
          centering=(0.5, 0.74)),
    Photo("roof-deck.jpeg", "THE ROOF DECK", centering=(0.5, 0.44)),
    Photo("changing-room.jpeg", "THE CHANGING ROOM", centering=(0.5, 0.44)),
]


# --------------------------------------------------------------- measuring ---

_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
REF = 1000  # measure at this size, scale linearly (SVG text is unhinted)


def _face(family: str) -> ImageFont.FreeTypeFont:
    key = (family, REF)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(str(FONT_FILES[family]), REF)
    return _FONT_CACHE[key]


def advance_per_em(family: str, text: str) -> float:
    """Advance width of `text` at font-size 1."""
    return _face(family).getlength(text) / REF


def ink_per_em(family: str, text: str) -> tuple[float, float]:
    """(left bearing, ink width) of `text` at font-size 1."""
    x0, _, x1, _ = _face(family).getbbox(text)
    return x0 / REF, (x1 - x0) / REF


def cap_per_em(family: str) -> float:
    _, y0, _, y1 = _face(family).getbbox("H")
    return (y1 - y0) / REF


def text_width(family: str, text: str, size: float, track_em: float = 0.0) -> float:
    """Rendered advance width, matching cairosvg (no trailing letter-spacing)."""
    n = max(len(text) - 1, 0)
    return advance_per_em(family, text) * size + track_em * size * n


def fit_size(family: str, text: str, target_w: float, track_em: float = 0.0,
             cap: float | None = None) -> float:
    """Largest size whose rendered width is exactly `target_w` (capped)."""
    per_em = advance_per_em(family, text) + track_em * max(len(text) - 1, 0)
    size = target_w / per_em
    return min(size, cap) if cap else size


def widest(family: str, texts, track_em: float = 0.0) -> str:
    """The text that actually renders widest — character count is not a proxy.

    "Sauna, food, good company — and one" is shorter than "No toys, no
    catalogue, no starter kit." yet sets wider; sizing on len() clipped it.
    """
    return max(texts, key=lambda t: text_width(family, t, 1000.0, track_em))


_PROBE_CACHE: dict[tuple, tuple[float, float]] = {}


def probe_ink(text: str, family: str, size: float,
              track_em: float) -> tuple[float, float]:
    """Ink extent of `text` as cairosvg actually renders it, relative to origin.

    PIL's glyph bboxes get us close, but negative tracking and bearings leave a
    percent or so on the table. The headline has to be flush, so we ask the
    renderer instead of trusting the estimate.
    """
    import numpy as np

    key = (text, family, round(size, 4), track_em)
    if key in _PROBE_CACHE:
        return _PROBE_CACHE[key]

    pad = 240
    w = int(text_width(family, text, size, track_em) + 2 * pad)
    h = int(size * 2.0)
    markup = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
        f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>'
        f'{text_el(pad, size * 1.35, text, family, size, "#000000", track_em)}</svg>'
    )
    png = cairosvg.svg2png(bytestring=markup.encode(), output_width=w, output_height=h)
    arr = np.asarray(Image.open(io.BytesIO(png)).convert("L"))
    cols = np.where((arr < 128).any(axis=0))[0]
    _PROBE_CACHE[key] = (float(cols.min() - pad), float(cols.max() + 1 - pad))
    return _PROBE_CACHE[key]


def fit_ink_flush(family: str, text: str, target_w: float,
                  track_em: float) -> tuple[float, float]:
    """Size + x nudge so the *ink* of `text` spans exactly `target_w`.

    Used for the headline, which has to touch both content edges. Seeded from
    the font metrics, then corrected against a real render.
    """
    lsb, ink = ink_per_em(family, text)
    size = target_w / (ink + track_em * max(len(text) - 1, 0))
    lo = -lsb * size
    for _ in range(4):
        lo, hi = probe_ink(text, family, size, track_em)
        measured = hi - lo
        if abs(measured - target_w) <= 0.5:
            break
        size *= target_w / measured
    return size, -lo


# ------------------------------------------------------------- svg helpers ---


class Svg:
    def __init__(self) -> None:
        self.defs: list[str] = []
        self.body: list[str] = []

    def add(self, markup: str) -> None:
        self.body.append(markup)

    def define(self, markup: str) -> None:
        self.defs.append(markup)

    def render(self, width: int, height: int) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<defs>{"".join(self.defs)}</defs>'
            f'{"".join(self.body)}</svg>'
        )


def f(value: float) -> str:
    """Compact float formatting — keeps the SVG from bloating."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


BOXES: list[dict] = []


def record(name: str, x0: float, y0: float, x1: float, y1: float) -> None:
    """Log a placed element so verify.py can assert nothing escapes the box."""
    BOXES.append({"name": name, "x0": round(x0, 2), "y0": round(y0, 2),
                  "x1": round(x1, 2), "y1": round(y1, 2)})


def record_text(name: str, x: float, baseline: float, content: str, family: str,
                size: float, track_em: float = 0.0, ink: bool = False) -> None:
    if ink:
        lsb, w = ink_per_em(family, content)
        w = w * size + track_em * size * max(len(content) - 1, 0)
        x = x + lsb * size
    else:
        w = text_width(family, content, size, track_em)
    cap = cap_per_em(family) * size
    record(name, x, baseline - cap, x + w, baseline + size * 0.22)


def text_el(x: float, y: float, content: str, family: str, size: float,
            fill: str, track_em: float = 0.0, anchor: str = "start",
            opacity: float | None = None) -> str:
    attrs = [
        f'x="{f(x)}"', f'y="{f(y)}"',
        f'font-family="{family}"', f'font-size="{f(size)}"',
        f'fill="{fill}"',
    ]
    if track_em:
        attrs.append(f'letter-spacing="{f(track_em * size)}"')
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if opacity is not None:
        attrs.append(f'opacity="{f(opacity)}"')
    return f'<text {" ".join(attrs)}>{escape(content)}</text>'


def rot(px: float, py: float, deg: float) -> tuple[float, float]:
    a = math.radians(deg)
    return px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)


# ----------------------------------------------------------------- motifs ---


def emboss(path_d: str, depth: float = 1.8, face: str = CARVE_FACE,
           shadow_op: float = 0.26, light_op: float = 0.50,
           rule: str = "nonzero") -> str:
    """Carved-relief treatment: shadow below-right, highlight above-left, face on top.

    Deliberately low contrast — the motif should read as pressed into the stone
    under the lantern, not drawn on top of it.
    """
    fr = f' fill-rule="{rule}"' if rule != "nonzero" else ""
    return (
        f'<path d="{path_d}"{fr} fill="#6B4A2E" opacity="{f(shadow_op)}" '
        f'transform="translate({f(depth)},{f(depth)})"/>'
        f'<path d="{path_d}"{fr} fill="#FFFFFF" opacity="{f(light_op)}" '
        f'transform="translate({f(-depth)},{f(-depth)})"/>'
        f'<path d="{path_d}"{fr} fill="{face}"/>'
    )


def lotus_arch(cx: float, base_y: float, w: float, h: float) -> str:
    """Pointed ogee arch — the lotus-arch niche used across the relief bands."""
    hw = w / 2
    return (
        f"M {f(cx - hw)} {f(base_y)} "
        f"L {f(cx - hw)} {f(base_y - h * 0.42)} "
        f"C {f(cx - hw)} {f(base_y - h * 0.80)} {f(cx - w * 0.30)} {f(base_y - h * 0.92)} "
        f"{f(cx)} {f(base_y - h)} "
        f"C {f(cx + w * 0.30)} {f(base_y - h * 0.92)} {f(cx + hw)} {f(base_y - h * 0.80)} "
        f"{f(cx + hw)} {f(base_y - h * 0.42)} "
        f"L {f(cx + hw)} {f(base_y)} Z"
    )


def temple_gate(cx: float, base_y: float, w: float, h: float) -> str:
    """Candi bentar — a split gate, two mirrored stepped towers with a gap."""
    gap = w * 0.15
    half = (w - gap) / 2
    parts = []
    for sign in (-1, 1):
        outer = cx + sign * (gap / 2 + half)
        inner = cx + sign * (gap / 2)
        # stepped taper from base to tip, four tiers
        pts = [(outer, base_y)]
        for i in range(4):
            t0 = i / 4
            t1 = (i + 1) / 4
            x0 = outer + (inner - outer) * 0.62 * t0
            x1 = outer + (inner - outer) * 0.62 * t1
            pts.append((x0, base_y - h * t1))
            pts.append((x1, base_y - h * t1))
        pts.append((inner, base_y - h))
        pts.append((inner, base_y))
        parts.append("M " + " L ".join(f"{f(px)} {f(py)}" for px, py in pts) + " Z")
    return " ".join(parts)


def lotus_bud(cx: float, base_y: float, r: float) -> str:
    return (
        f"M {f(cx)} {f(base_y)} "
        f"C {f(cx - r)} {f(base_y - r * 0.35)} {f(cx - r * 0.55)} {f(base_y - r * 1.7)} "
        f"{f(cx)} {f(base_y - r * 2.0)} "
        f"C {f(cx + r * 0.55)} {f(base_y - r * 1.7)} {f(cx + r)} {f(base_y - r * 0.35)} "
        f"{f(cx)} {f(base_y)} Z"
    )


def carved_band(svg: Svg, x: float, y: float, w: float, h: float) -> float:
    """A running relief band: an arcade cut *into* a solid field.

    Carving the arches out as niches (rather than standing them up as separate
    shapes with gaps between) is what makes this read as a temple wall instead
    of a row of headstones.
    """
    top = y + 13
    base = y + h - 13
    field_h = base - top

    unit = w / max(round(w / 76), 1)  # whole motifs only, no partial at the edge
    count = round(w / unit)

    # solid field, with arch niches and carved spandrel dots as evenodd holes
    field = f"M {f(x)} {f(top)} H {f(x + w)} V {f(base)} H {f(x)} Z"
    holes = []
    for i in range(count):
        cx = x + unit * (i + 0.5)
        holes.append(lotus_arch(cx, base, unit * 0.50, field_h * 0.70))
    for i in range(count + 1):
        bx = x + unit * i
        bx = min(max(bx, x + 5), x + w - 5)
        holes.append(f"M {f(bx)} {f(top + field_h * 0.24)} "
                     f"a 3.4 3.4 0 1 0 0.01 0 Z")
    svg.add(emboss(field + " " + " ".join(holes), rule="evenodd"))

    # candi-bentar finials standing on the pilasters between the niches
    finials = []
    for i in range(count + 1):
        bx = x + unit * i
        if bx < x + 8 or bx > x + w - 8:
            continue
        finials.append(temple_gate(bx, top + 1, unit * 0.20, 11))
    if finials:
        svg.add(emboss(" ".join(finials), depth=1.2, light_op=0.46))

    # lotus buds hanging in the springline between adjacent arches
    buds = [lotus_bud(x + unit * i, base - 2, 4.2) for i in range(1, count)]
    svg.add(emboss(" ".join(buds), depth=1.2, light_op=0.46))

    for ry, op, sw in ((y, 0.55, 1.6), (y + 6, 0.28, 0.9),
                       (y + h, 0.55, 1.6), (y + h - 6, 0.28, 0.9)):
        svg.add(f'<line x1="{f(x)}" y1="{f(ry)}" x2="{f(x + w)}" y2="{f(ry)}" '
                f'stroke="{GOLD}" stroke-width="{f(sw)}" opacity="{f(op)}"/>')
    return y + h


def frangipani(cx: float, cy: float, r: float, opacity: float = 1.0,
               twist: float = 0.0) -> str:
    """Five fat overlapping petals with a gold throat.

    The petals deliberately span more arc than the 72° they are spaced by, so
    they overlap. Narrow petals would read as an asterisk, not a flower.
    """
    petal = (
        "M 0 0 "
        f"C {f(-0.60 * r)} {f(-0.26 * r)} {f(-0.74 * r)} {f(-0.74 * r)} "
        f"{f(-0.16 * r)} {f(-1.00 * r)} "
        f"C {f(0.34 * r)} {f(-1.14 * r)} {f(0.72 * r)} {f(-0.52 * r)} 0 0 Z"
    )
    shadow, faces = [], []
    for i in range(5):
        deg = twist + 72 * i
        shadow.append(f'<path d="{petal}" transform="rotate({f(deg)})"/>')
        faces.append(f'<path d="{petal}" transform="rotate({f(deg)})"/>')
    return (
        f'<g transform="translate({f(cx)},{f(cy)})" opacity="{f(opacity)}">'
        f'<g transform="translate(0.8,2.4)" fill="{MUTED}" opacity="0.20">'
        f'{"".join(shadow)}</g>'
        f'<g fill="{FRANGIPANI}" stroke="#C6A374" stroke-width="{f(max(r * 0.028, 0.7))}" '
        f'stroke-opacity="0.60">{"".join(faces)}</g>'
        f'<circle r="{f(r * 0.21)}" fill="{GOLD}" opacity="0.85"/>'
        f'<circle r="{f(r * 0.11)}" fill="#DCB45C"/>'
        f"</g>"
    )


def frangipani_divider(svg: Svg, x: float, y: float, w: float) -> float:
    """A hairline rule broken by a frangipani, used between sections."""
    r = 21.0
    gap = r * 2.4
    cx = x + w / 2
    for x1, x2 in ((x, cx - gap), (cx + gap, x + w)):
        svg.add(f'<line x1="{f(x1)}" y1="{f(y)}" x2="{f(x2)}" y2="{f(y)}" '
                f'stroke="{GOLD}" stroke-width="1" opacity="0.42"/>')
    for side in (-1, 1):
        bx = cx + side * (gap + 16)
        svg.add(f'<circle cx="{f(bx)}" cy="{f(y)}" r="2.4" fill="{GOLD}" '
                f'opacity="0.5"/>')
    svg.add(frangipani(cx, y, r, twist=-14))
    return y


def monstera(size: float) -> str:
    """Monstera leaf pointing +y, with real fenestrations (evenodd holes)."""
    s = size
    outline = (
        "M 0 0 "
        f"C {f(0.60 * s)} {f(0.12 * s)} {f(0.88 * s)} {f(0.56 * s)} {f(0.48 * s)} {f(0.98 * s)} "
        f"C {f(0.28 * s)} {f(1.19 * s)} {f(0.09 * s)} {f(1.24 * s)} 0 {f(1.32 * s)} "
        f"C {f(-0.09 * s)} {f(1.24 * s)} {f(-0.28 * s)} {f(1.19 * s)} {f(-0.48 * s)} {f(0.98 * s)} "
        f"C {f(-0.88 * s)} {f(0.56 * s)} {f(-0.60 * s)} {f(0.12 * s)} 0 0 Z"
    )
    slits = []
    for side in (-1, 1):
        for j in range(4):
            t = 0.22 + j * 0.20
            base_x = side * 0.055 * s
            base_y = t * 1.10 * s
            length = (0.52 - 0.09 * j) * s
            width = 0.055 * s
            ang = 34 + 9 * j
            # a lens pointing +x, rotated outward, then mirrored for the left half
            pts = [(0, -width), (length, -width * 0.32),
                   (length, width * 0.32), (0, width)]
            rp = [rot(px, py, ang) for px, py in pts]
            rp = [(base_x + side * px, base_y + py) for px, py in rp]
            slits.append("M " + " L ".join(f"{f(px)} {f(py)}" for px, py in rp) + " Z")
    return f'<path fill-rule="evenodd" d="{outline} {" ".join(slits)}"/>'


def palm_frond(length: float) -> str:
    """A single arcing frond: rachis plus tapering leaflets on both sides."""
    parts = [
        f"M 0 0 C {f(0.10 * length)} {f(0.34 * length)} {f(0.14 * length)} "
        f"{f(0.70 * length)} 0 {f(length)} "
        f"C {f(-0.03 * length)} {f(0.70 * length)} {f(-0.04 * length)} "
        f"{f(0.34 * length)} 0 0 Z"
    ]
    n = 15
    for i in range(1, n):
        t = i / n
        # rachis curves; sample its position and normal
        rx = 0.11 * length * (3 * (1 - t) ** 2 * t + 3 * (1 - t) * t ** 2)
        ry = t * length
        leaf = (0.40 - 0.26 * t) * length * (0.35 + 0.65 * math.sin(math.pi * t))
        for side in (-1, 1):
            tip_x = rx + side * leaf * 0.86
            tip_y = ry + leaf * 0.46
            parts.append(
                f"M {f(rx)} {f(ry)} "
                f"Q {f(rx + side * leaf * 0.55)} {f(ry + leaf * 0.05)} "
                f"{f(tip_x)} {f(tip_y)} "
                f"Q {f(rx + side * leaf * 0.34)} {f(ry + leaf * 0.16)} "
                f"{f(rx)} {f(ry + leaf * 0.10)} Z"
            )
    return f'<path d="{" ".join(parts)}"/>'


# ------------------------------------------------------------------ images ---


def prepare_photo_image(photo: Photo, out_w: int, out_h: int) -> Image.Image:
    """EXIF-correct, optionally pre-crop, then fit to the frame.

    The pre-crop runs first and on purpose: ImageOps.fit only shifts the crop
    along the axis it is actually trimming, so on a landscape source no amount
    of centering can push something out of frame horizontally.
    """
    src = ASSETS / photo.filename
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    w, h = im.size
    l, t, r, b = photo.precrop
    if (l, t, r, b) != (0.0, 0.0, 1.0, 1.0):
        im = im.crop((int(w * l), int(h * t), int(w * r), int(h * b)))
    return ImageOps.fit(im, (out_w, out_h), method=Image.LANCZOS,
                        centering=photo.centering)


def prepare_photo(photo: Photo, out_w: int, out_h: int) -> str:
    im = prepare_photo_image(photo, out_w, out_h)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


# ------------------------------------------------------------------ layout ---


def build() -> tuple[str, int]:
    OUT.mkdir(exist_ok=True)
    svg = Svg()

    # -- measured type sizes -------------------------------------------------
    eyebrow_size = fit_size(MONO, EYEBROW, CONTENT_W * 0.66, MONO_TRACK)
    head_size, head_dx = fit_ink_flush(DISPLAY, HEADLINE[0], CONTENT_W, TIGHT_TRACK)
    sub_size = fit_size(DISPLAY_MED, SUBHEAD, CONTENT_W)
    date_size = fit_size(MONO, DATELINE.upper(), CONTENT_W * 0.60, MONO_TRACK)
    caption_size = fit_size(
        MONO, widest(MONO, [p.caption for p in PHOTOS], MONO_TRACK),
        CONTENT_W * 0.30, MONO_TRACK)
    label_size = fit_size(
        MONO, widest(MONO, [d[0] for d in DETAILS], MONO_TRACK), 72, MONO_TRACK)
    value_size = fit_size(
        DISPLAY_MED, widest(DISPLAY_MED, [d[1] for d in DETAILS]),
        CONTENT_W - 150, cap=40)
    closing_size = fit_size(
        DISPLAY_MED, widest(DISPLAY_MED, [c[0] for c in CLOSING]), CONTENT_W)

    head_cap = cap_per_em(DISPLAY) * head_size
    head_lead = head_size * 0.90

    x = CONTENT_X
    y = CARD_TOP + PAD_TOP

    # -- 1. opening carved band ---------------------------------------------
    y = carved_band(svg, x, y, CONTENT_W, 84)

    # -- 2. eyebrow ----------------------------------------------------------
    y += 58
    ey_w = text_width(MONO, EYEBROW, eyebrow_size, MONO_TRACK)
    y += cap_per_em(MONO) * eyebrow_size
    svg.add(text_el(CANVAS_W / 2 - ey_w / 2, y, EYEBROW, MONO, eyebrow_size,
                    MUTED, MONO_TRACK))
    record_text("eyebrow", CANVAS_W / 2 - ey_w / 2, y, EYEBROW, MONO,
                eyebrow_size, MONO_TRACK)
    # short gold rules either side of the eyebrow
    for x1, x2 in ((x, CANVAS_W / 2 - ey_w / 2 - 26),
                   (CANVAS_W / 2 + ey_w / 2 + 26, x + CONTENT_W)):
        svg.add(f'<line x1="{f(x1)}" y1="{f(y - eyebrow_size * 0.30)}" '
                f'x2="{f(x2)}" y2="{f(y - eyebrow_size * 0.30)}" stroke="{GOLD}" '
                f'stroke-width="1" opacity="0.40"/>')

    # -- 3. headline ---------------------------------------------------------
    # generous, because the trend line starts above the cap height and would
    # otherwise collide with the eyebrow rule
    y += 78
    head_top = y
    base1 = head_top + head_cap
    base2 = base1 + head_lead
    for i, line in enumerate(HEADLINE):
        svg.add(text_el(x + head_dx, base1 + i * head_lead, line, DISPLAY,
                        head_size, INK, TIGHT_TRACK))
        # recorded from the same calibrated render the placement uses, not from
        # the PIL estimate that only seeds it
        lo, hi = probe_ink(line, DISPLAY, head_size, TIGHT_TRACK)
        base = base1 + i * head_lead
        record(f"headline:{line}", x + head_dx + lo, base - head_cap,
               x + head_dx + hi, base + head_size * 0.22)

    # -- 4. the falling trend line ------------------------------------------
    # Holds a brief plateau clear above the cap height, then plunges steeply so
    # it crosses the letterforms on a diagonal and lands in an arrowhead in the
    # open space beside DOWN. A shallow crossing here would read as a
    # strike-through instead of a fall, which is the whole joke.
    down_w = text_width(DISPLAY, HEADLINE[1], head_size, TIGHT_TRACK)
    p0 = (x - 8, head_top - 40)
    c1 = (x + CONTENT_W * 0.17, head_top - 58)
    c2 = (x + CONTENT_W * 0.32, head_top - 14)
    p3 = (x + CONTENT_W * 0.42, head_top + head_cap * 0.80)
    c3 = (x + CONTENT_W * 0.52, base1 + head_lead * 0.34)
    c4 = (x + down_w + 46, base2 - head_cap * 0.34)
    p5 = (x + down_w + 116, base2 + head_cap * 0.26)
    svg.add(
        f'<path d="M {f(p0[0])} {f(p0[1])} '
        f"C {f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p3[0])} {f(p3[1])} "
        f'C {f(c3[0])} {f(c3[1])} {f(c4[0])} {f(c4[1])} {f(p5[0])} {f(p5[1])}" '
        f'fill="none" stroke="{TERRACOTTA}" stroke-width="13" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )
    # arrowhead aligned to the curve's exit tangent
    ang = math.degrees(math.atan2(p5[1] - c4[1], p5[0] - c4[0]))
    head_len, head_half = 40.0, 20.0
    tri = f"M 0 0 L {f(-head_len)} {f(-head_half)} L {f(-head_len * 0.72)} 0 " \
          f"L {f(-head_len)} {f(head_half)} Z"
    svg.add(f'<path d="{tri}" fill="{TERRACOTTA}" '
            f'transform="translate({f(p5[0] + 12)},{f(p5[1] + 5)}) rotate({f(ang)})"/>')

    y = base2 + head_size * 0.30

    # -- 5. subhead + dateline ----------------------------------------------
    y += 58 + cap_per_em(DISPLAY_MED) * sub_size
    svg.add(text_el(x, y, SUBHEAD, DISPLAY_MED, sub_size, INK))
    record_text("subhead", x, y, SUBHEAD, DISPLAY_MED, sub_size)

    y += 34 + cap_per_em(MONO) * date_size
    svg.add(text_el(x, y, DATELINE.upper(), MONO, date_size, TERRACOTTA, MONO_TRACK))
    record_text("dateline", x, y, DATELINE.upper(), MONO, date_size, MONO_TRACK)

    # -- 6. photographs ------------------------------------------------------
    y += 40
    px_w = int(CONTENT_W * PHOTO_SCALE)
    px_h = int(PHOTO_H * PHOTO_SCALE)
    for photo in PHOTOS:
        y += 66
        frangipani_divider(svg, x, y, CONTENT_W)
        y += 40 + cap_per_em(MONO) * caption_size
        svg.add(text_el(x, y, photo.caption, MONO, caption_size, GOLD, MONO_TRACK))
        record_text(f"caption:{photo.caption}", x, y, photo.caption, MONO,
                    caption_size, MONO_TRACK)
        y += 26
        data = prepare_photo(photo, px_w, px_h)
        svg.add(
            f'<image x="{f(x)}" y="{f(y)}" width="{CONTENT_W}" height="{PHOTO_H}" '
            f'preserveAspectRatio="none" xlink:href="data:image/jpeg;base64,{data}"/>'
        )
        svg.add(f'<rect x="{f(x)}" y="{f(y)}" width="{CONTENT_W}" height="{PHOTO_H}" '
                f'fill="none" stroke="{GOLD}" stroke-width="1.2" opacity="0.65"/>')
        record(f"photo:{photo.filename}", x, y, x + CONTENT_W, y + PHOTO_H)
        y += PHOTO_H

    # -- 7/8. details --------------------------------------------------------
    y += 72
    frangipani_divider(svg, x, y, CONTENT_W)
    y += 46

    gutter = 150
    row_h = value_size * 1.62
    for label, value in DETAILS:
        base = y + cap_per_em(DISPLAY_MED) * value_size
        svg.add(text_el(x, base - (cap_per_em(DISPLAY_MED) * value_size
                                   - cap_per_em(MONO) * label_size) / 2,
                        label, MONO, label_size, MUTED, MONO_TRACK))
        svg.add(text_el(x + gutter, base, value, DISPLAY_MED, value_size, INK))
        record_text(f"label:{label}", x, base, label, MONO, label_size, MONO_TRACK)
        record_text(f"value:{label}", x + gutter, base, value, DISPLAY_MED,
                    value_size)
        y += row_h

    # -- 9/10. closing note --------------------------------------------------
    y += 44
    frangipani_divider(svg, x, y, CONTENT_W)
    y += 52

    closing_lead = closing_size * 1.36
    for i, (line, colour) in enumerate(CLOSING):
        base = y + cap_per_em(DISPLAY_MED) * closing_size + i * closing_lead
        svg.add(text_el(x, base, line, DISPLAY_MED, closing_size, colour))
        record_text(f"closing:{i}", x, base, line, DISPLAY_MED, closing_size)
    y += cap_per_em(DISPLAY_MED) * closing_size + (len(CLOSING) - 1) * closing_lead

    # -- 11. closing frangipani + carved band --------------------------------
    y += 62
    frangipani_divider(svg, x, y, CONTENT_W)
    y += 48
    y = carved_band(svg, x, y, CONTENT_W, 84)

    card_bottom = y + PAD_BOTTOM
    canvas_h = int(math.ceil(card_bottom + MARGIN))
    card_h = card_bottom - CARD_TOP

    # ---------------------------------------------------------------- ground --
    background: list[str] = []
    svg.define(
        f'<clipPath id="card"><rect x="{CARD_X}" y="{CARD_TOP}" width="{CARD_W}" '
        f'height="{f(card_h)}" rx="6"/></clipPath>'
    )
    svg.define(
        f'<radialGradient id="lantern-top" cx="0.5" cy="0" r="0.9">'
        f'<stop offset="0" stop-color="#FFEFCB" stop-opacity="0.85"/>'
        f'<stop offset="0.45" stop-color="#FFE3AE" stop-opacity="0.30"/>'
        f'<stop offset="1" stop-color="#FFE3AE" stop-opacity="0"/></radialGradient>'
    )
    svg.define(
        f'<radialGradient id="lantern-bottom" cx="0.5" cy="1" r="0.85">'
        f'<stop offset="0" stop-color="#FFE7BC" stop-opacity="0.50"/>'
        f'<stop offset="1" stop-color="#FFE7BC" stop-opacity="0"/></radialGradient>'
    )
    svg.define(
        f'<radialGradient id="vignette" cx="0.5" cy="0.5" r="0.72">'
        f'<stop offset="0.55" stop-color="#8B7355" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="#6B5237" stop-opacity="0.22"/></radialGradient>'
    )
    svg.define(
        f'<radialGradient id="blotch"><stop offset="0" stop-color="#C4A883" '
        f'stop-opacity="0.16"/><stop offset="1" stop-color="#C4A883" '
        f'stop-opacity="0"/></radialGradient>'
    )

    background.append(f'<rect width="{CANVAS_W}" height="{canvas_h}" fill="{GROUND}"/>')

    # jungle silhouettes on the ground, mostly bleeding under the slab edges
    ground_leaves: list[str] = []
    for i in range(14):
        t = (i + 0.5) / 14
        side = -1 if i % 2 == 0 else 1
        cy = canvas_h * t + RNG.uniform(-90, 90)
        cx = 12 if side < 0 else CANVAS_W - 12
        scale = RNG.uniform(150, 290)
        deg = (118 if side < 0 else -118) + RNG.uniform(-26, 26)
        ground_leaves.append(
            f'<g transform="translate({f(cx)},{f(cy)}) rotate({f(deg)})" '
            f'fill="#31543D" opacity="0.85">{palm_frond(scale)}</g>')
    background.append("".join(ground_leaves))

    # the sandstone slab
    background.append(
        f'<rect x="{CARD_X}" y="{CARD_TOP}" width="{CARD_W}" height="{f(card_h)}" '
        f'rx="6" fill="{SANDSTONE}"/>')

    inside: list[str] = []
    # porous speckle — many tiny marks, a few soft blotches for mottling
    speckle: list[str] = []
    n_speckle = int(CARD_W * card_h / 1050)
    for _ in range(n_speckle):
        sx = RNG.uniform(CARD_X, CARD_X + CARD_W)
        sy = RNG.uniform(CARD_TOP, CARD_TOP + card_h)
        r = RNG.uniform(0.5, 2.1)
        dark = RNG.random() < 0.62
        col = "#9C7F5B" if dark else "#FFFAF0"
        op = RNG.uniform(0.05, 0.16) if dark else RNG.uniform(0.14, 0.34)
        speckle.append(f'<circle cx="{f(sx)}" cy="{f(sy)}" r="{f(r)}" fill="{col}" '
                       f'opacity="{f(op)}"/>')
    inside.append("".join(speckle))
    blotches: list[str] = []
    for _ in range(int(card_h / 62)):
        sx = RNG.uniform(CARD_X, CARD_X + CARD_W)
        sy = RNG.uniform(CARD_TOP, CARD_TOP + card_h)
        r = RNG.uniform(50, 175)
        blotches.append(f'<circle cx="{f(sx)}" cy="{f(sy)}" r="{f(r)}" '
                        f'fill="url(#blotch)"/>')
    inside.append("".join(blotches))

    # jungle green framing the outer edges from inside the slab
    frame_leaves: list[str] = []
    for i in range(16):
        t = (i + 0.5) / 16
        side = -1 if i % 2 == 0 else 1
        cy = CARD_TOP + card_h * t + RNG.uniform(-70, 70)
        cx = CARD_X - 18 if side < 0 else CARD_X + CARD_W + 18
        if i % 4 == 1:
            scale = RNG.uniform(120, 175)
            deg = (128 if side < 0 else -128) + RNG.uniform(-20, 20)
            shape = monstera(scale)
        else:
            scale = RNG.uniform(210, 330)
            deg = (122 if side < 0 else -122) + RNG.uniform(-24, 24)
            shape = palm_frond(scale)
        frame_leaves.append(
            f'<g transform="translate({f(cx)},{f(cy)}) rotate({f(deg)})" '
            f'fill="{JUNGLE}" opacity="{f(RNG.uniform(0.075, 0.13))}">{shape}</g>')
    inside.append("".join(frame_leaves))

    # frangipani scattered faintly across the stone
    scattered: list[str] = []
    for _ in range(int(card_h / 300)):
        sx = RNG.uniform(CARD_X + 40, CARD_X + CARD_W - 40)
        sy = RNG.uniform(CARD_TOP + 60, CARD_TOP + card_h - 60)
        scattered.append(frangipani(sx, sy, RNG.uniform(30, 58),
                                    opacity=RNG.uniform(0.10, 0.17),
                                    twist=RNG.uniform(0, 72)))
    inside.append("".join(scattered))

    # lantern light: strong from above, a softer pool at the foot
    inside.append(
        f'<rect x="{CARD_X}" y="{CARD_TOP}" width="{CARD_W}" height="{f(card_h * 0.34)}" '
        f'fill="url(#lantern-top)"/>')
    inside.append(
        f'<rect x="{CARD_X}" y="{f(CARD_TOP + card_h * 0.72)}" width="{CARD_W}" '
        f'height="{f(card_h * 0.28)}" fill="url(#lantern-bottom)"/>')
    inside.append(
        f'<rect x="{CARD_X}" y="{CARD_TOP}" width="{CARD_W}" height="{f(card_h)}" '
        f'fill="url(#vignette)"/>')

    background.append(f'<g clip-path="url(#card)">{"".join(inside)}</g>')

    # doubled antique-gold keyline at the slab border
    keylines = (
        f'<rect x="{CARD_X + 0.9}" y="{CARD_TOP + 0.9}" width="{CARD_W - 1.8}" '
        f'height="{f(card_h - 1.8)}" rx="6" fill="none" stroke="{GOLD}" '
        f'stroke-width="1.8" opacity="0.85"/>'
        f'<rect x="{CARD_X + 10}" y="{CARD_TOP + 10}" width="{CARD_W - 20}" '
        f'height="{f(card_h - 20)}" rx="3" fill="none" stroke="{GOLD}" '
        f'stroke-width="1" opacity="0.50"/>'
    )

    svg.body = background + svg.body + [keylines]

    report = {
        "eyebrow": eyebrow_size, "headline": head_size, "subhead": sub_size,
        "dateline": date_size, "caption": caption_size, "label": label_size,
        "value": value_size, "closing": closing_size,
    }
    import json
    (OUT / "layout.json").write_text(json.dumps({
        "canvas": [CANVAS_W, canvas_h],
        "card": [CARD_X, CARD_TOP, CARD_X + CARD_W, card_bottom],
        "content": [CONTENT_X, CONTENT_X + CONTENT_W],
        "sizes": {k: round(v, 2) for k, v in report.items()},
        "boxes": BOXES,
    }, indent=1), encoding="utf-8")
    print("measured sizes: " + ", ".join(f"{k}={v:.1f}" for k, v in report.items()))
    print(f"card height {card_h:.0f}, canvas {CANVAS_W}x{canvas_h}")
    return svg.render(CANVAS_W, canvas_h), canvas_h


def main() -> None:
    OUT.mkdir(exist_ok=True)
    markup, height = build()
    (OUT / "invite.svg").write_text(markup, encoding="utf-8")
    print(f"svg {len(markup) / 1e6:.1f} MB")

    cairosvg.svg2png(bytestring=markup.encode(), write_to=str(OUT / "invite.png"),
                     output_width=CANVAS_W, output_height=height)
    cairosvg.svg2pdf(bytestring=markup.encode(), write_to=str(OUT / "invite.pdf"))

    full = Image.open(OUT / "invite.png").convert("RGB")
    compact_w = 840
    compact = full.resize(
        (compact_w, round(full.height * compact_w / full.width)), Image.LANCZOS)
    compact.save(OUT / "invite-compact.png", optimize=True)

    for name in ("invite.png", "invite.pdf", "invite-compact.png"):
        print(f"{name:20} {(OUT / name).stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
