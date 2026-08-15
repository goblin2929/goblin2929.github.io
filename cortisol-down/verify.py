#!/usr/bin/env python3
"""Check the rendered card, then slice it into quarters for eyeballing.

Automated here: nothing escapes the content column, no two elements collide,
the headline ink lands exactly on the content edges, and no face survives into
a rendered photo crop (with a control proving the detector would catch one).

Still a human job, via the quarter slices this writes: whether the trend line
reads as a fall rather than a strike-through, whether the frangipani reads as a
flower rather than an asterisk, and whether the spacing feels even.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CHECK = OUT / "check"

TOL = 1.0  # px of slack on the content column


def load() -> tuple[Image.Image, dict]:
    img = Image.open(OUT / "invite.png").convert("RGB")
    layout = json.loads((OUT / "layout.json").read_text())
    return img, layout


def check_containment(layout: dict) -> list[str]:
    left, right = layout["content"]
    bad = []
    for b in layout["boxes"]:
        if b["x0"] < left - TOL or b["x1"] > right + TOL:
            bad.append(f"{b['name']}: x {b['x0']:.1f}..{b['x1']:.1f} "
                       f"escapes content {left}..{right}")
    return bad


def check_collisions(layout: dict) -> list[str]:
    """Flag elements that overlap both horizontally and vertically."""
    bad = []
    boxes = layout["boxes"]
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if b["y0"] >= a["y1"] - 0.5 or a["y0"] >= b["y1"] - 0.5:
                continue
            if b["x0"] >= a["x1"] - 0.5 or a["x0"] >= b["x1"] - 0.5:
                continue
            bad.append(f"{a['name']} overlaps {b['name']}")
    return bad


def check_headline_flush(img: Image.Image, layout: dict) -> list[str]:
    """The headline has to touch both content edges exactly.

    Scanned inside the slab only — the jungle ground and the terracotta trend
    line both sit outside the ink threshold's intent.
    """
    left, right = layout["content"]
    cx0, _, cx1, _ = layout["card"]
    box = next(b for b in layout["boxes"] if b["name"].startswith("headline:CORTISOL"))
    band = np.asarray(img.convert("L"))[int(box["y0"]):int(box["y1"]),
                                        int(cx0) + 12:int(cx1) - 12]
    cols = np.where((band < 70).any(axis=0))[0] + int(cx0) + 12
    lo, hi = int(cols.min()), int(cols.max())
    msg = f"ink {lo}..{hi} vs content {left}..{right}"
    if abs(lo - left) > 2 or abs(hi - right) > 2:
        return [f"headline not flush: {msg}"]
    print(f"  flush ok ({msg})")
    return []


def _detectors():
    import cv2
    base = Path(cv2.data.haarcascades)
    return cv2, [
        ("frontal", cv2.CascadeClassifier(str(base / "haarcascade_frontalface_default.xml"))),
        ("profile", cv2.CascadeClassifier(str(base / "haarcascade_profileface.xml"))),
    ]


def _faces_in(cv2, dets, pil: Image.Image) -> list[tuple[str, tuple]]:
    """Detections at 2x crop scale.

    minNeighbors/minSize are set well above Haar's defaults: at 26px this
    cascade fires happily on teak grain and decking planks (every hit in the
    first pass was wood). Anyone actually in one of these frames fills a good
    fraction of it, so a 90px floor loses nothing real — the control below
    proves that empirically.
    """
    import numpy as np
    gray = cv2.cvtColor(np.asarray(pil.convert("RGB")), cv2.COLOR_RGB2GRAY)
    gray = cv2.equalizeHist(gray)
    found = []
    for name, det in dets:
        for box in det.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=9,
                                        minSize=(90, 90)):
            found.append((name, tuple(int(v) for v in box)))
    return found


def check_no_faces(img: Image.Image, layout: dict) -> list[str]:
    """No face or reflection may survive into a rendered crop.

    The control is a regression test on the real pipeline, not just on the raw
    file: the cold-plunge frame is pushed through prepare_photo with its
    pre-crop removed, which is exactly the mistake this guards against. If the
    detector cannot catch the person there, a clean result on the real crops
    would mean nothing, so that case fails the run.
    """
    import build

    cv2, dets = _detectors()
    bad = []

    uncropped = build.Photo("cold-plunge.jpeg", "control",
                            centering=build.PHOTOS[1].centering)
    control = build.prepare_photo_image(uncropped, 872, 600)
    control = control.resize((control.width * 2, control.height * 2), Image.LANCZOS)
    hits = _faces_in(cv2, dets, control)
    if not hits:
        return ["control failed: the person survives an un-pre-cropped "
                "cold-plunge render but the detector missed her — the clean "
                "results below cannot be trusted"]
    print(f"  control: {len(hits)} face(s) found in cold-plunge rendered "
          f"*without* its pre-crop — detector catches the real regression")

    for b in layout["boxes"]:
        if not b["name"].startswith("photo:"):
            continue
        crop = img.crop((int(b["x0"]), int(b["y0"]), int(b["x1"]), int(b["y1"])))
        crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
        hits = _faces_in(cv2, dets, crop)
        print(f"  {b['name']:28} faces: {len(hits)}")
        if hits:
            bad.append(f"{b['name']}: face detected at {hits} — fix the crop")
    return bad


def quarters(img: Image.Image, width: int = 620) -> list[Path]:
    CHECK.mkdir(parents=True, exist_ok=True)
    paths = []
    step = img.height // 4
    for i in range(4):
        top = i * step
        bottom = img.height if i == 3 else (i + 1) * step
        crop = img.crop((0, top, img.width, bottom))
        crop = crop.resize((width, round(crop.height * width / crop.width)),
                           Image.LANCZOS)
        p = CHECK / f"q{i + 1}.png"
        crop.save(p, optimize=True)
        paths.append(p)
    return paths


def main() -> int:
    img, layout = load()
    print(f"canvas {img.width}x{img.height}, card bottom {layout['card'][3]:.0f}")

    failures: list[str] = []
    print("containment:")
    failures += check_containment(layout)
    print(f"  {len(layout['boxes'])} elements checked against the content column")
    print("collisions:")
    failures += check_collisions(layout)
    print("headline:")
    failures += check_headline_flush(img, layout)
    print("photographs:")
    failures += check_no_faces(img, layout)

    for p in quarters(img):
        print(f"wrote {p.relative_to(HERE)}")

    if failures:
        print("\nFAILURES:")
        for msg in failures:
            print(f"  - {msg}")
        return 1
    print("\nall automated checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
