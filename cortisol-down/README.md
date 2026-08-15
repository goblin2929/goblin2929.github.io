# Cortisol Down — invitation card

A single vertical invitation card (1080 px wide, ~5,030 px tall), generated as
SVG by Python and rasterised with cairosvg. Balinese sandstone-relief direction:
carved arcade bands, frangipani dividers, jungle silhouettes at the edges,
lantern glow top and bottom.

## Build

```bash
pip install fonttools brotli cairosvg pillow numpy opencv-python-headless --break-system-packages

# fetch the upstream fonts (once)
mkdir -p fonts
BASE=https://raw.githubusercontent.com/google/fonts/main/ofl
curl -sL -o fonts/Bricolage-VF.ttf "$BASE/bricolagegrotesque/BricolageGrotesque%5Bopsz,wdth,wght%5D.ttf"
curl -sL -o fonts/IBMPlexMono-Regular.ttf "$BASE/ibmplexmono/IBMPlexMono-Regular.ttf"

python3 make_fonts.py   # pin the variable axes, install to ~/.fonts, fc-cache
python3 build.py        # -> out/invite.png, out/invite.pdf, out/invite-compact.png
python3 verify.py       # checks + out/check/q1..q4.png
```

`make_fonts.py` only needs re-running when the fonts change.

## Photographs

`assets/` is **not** committed — it holds personal photographs, and this
repository is a public GitHub Pages site. Drop these four files in before
building:

| File | Caption |
|---|---|
| `sauna.jpeg` | `THE SAUNA` |
| `cold-plunge.jpeg` | `THE COLD PLUNGE` |
| `roof-deck.jpeg` | `THE ROOF DECK` |
| `changing-room.jpeg` | `THE CHANGING ROOM` |

Each is EXIF-transposed, optionally pre-cropped, then fitted to 872 × 600 and
embedded as base64 JPEG (quality 86) rendered at 1.6× display size.

The pre-crop runs *before* the fit on purpose. `ImageOps.fit(centering=...)`
only shifts the crop along the axis it is actually trimming, so on a landscape
source no centering value can push something out of frame horizontally. The
cold-plunge frame has a person occupying its right half; `precrop=(0, 0, 0.505, 1)`
removes her, and `verify.py` guards against that regression.

## How the layout is driven

No text size is hardcoded. Sizes come from measuring the real font with
`PIL.ImageFont` and solving for the size that fills a target width; the headline
additionally calibrates against an actual cairosvg render, because glyph
bearings and negative tracking leave about a percent on the table and it has to
sit flush to both content edges.

Every vertical position accumulates from a running `y` cursor. The card height
and the canvas height are derived at the very end, after the last element.

Two things worth knowing if you edit it:

- Pick the widest string with `widest()`, never `max(..., key=len)`. "Sauna,
  food, good company — and one" is shorter than "No toys, no catalogue, no
  starter kit." but sets wider, and sizing on length clipped it off the card.
- The content width is 872 px, centred, which makes the inner padding 58 rather
  than 56. 872 is the number everything measures against, so it wins.

## What verify.py checks

Automated:

- every recorded element sits inside the 872 px content column
- no two elements overlap
- the headline's rendered ink lands on the content edges (±2 px)
- no face in any rendered photo crop — with a control that pushes the
  cold-plunge frame through the pipeline *without* its pre-crop and fails the
  run if the detector misses the person there

Haar's defaults fire constantly on teak grain and decking planks (every hit in
the first pass was wood), hence `minNeighbors=9` and a 90 px floor.

Left to the eye, via `out/check/q1..q4.png`: whether the trend line reads as a
fall rather than a strike-through, whether the frangipani reads as a flower
rather than an asterisk, and whether the spacing feels even.
