#!/usr/bin/env python3
"""Pin Bricolage Grotesque's variable axes into two static cuts.

cairosvg (via Pango/fontconfig) will not honour variable-font axes, so we
instance wght=800 and wght=600 at opsz=72 / wdth=100 and give each instance a
unique family name the SVG can reference by name.
"""
import shutil
import subprocess
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
USER_FONTS = Path.home() / ".fonts"

VF = FONTS / "Bricolage-VF.ttf"
MONO = FONTS / "IBMPlexMono-Regular.ttf"

CUTS = [
    ("Bricolage800", 800, "fonts/Bricolage800.ttf"),
    ("Bricolage600", 600, "fonts/Bricolage600.ttf"),
]

# name IDs we rewrite so fontconfig sees a distinct family per cut
NAME_FAMILY = 1
NAME_FULL = 4
NAME_TYPO_FAMILY = 16
NAME_SUBFAMILY = 2
NAME_TYPO_SUBFAMILY = 17
NAME_UNIQUE = 3
NAME_PS = 6


def instance_cut(family: str, weight: int, out_rel: str) -> Path:
    font = TTFont(VF)
    instancer.instantiateVariableFont(
        font, {"wght": weight, "opsz": 72, "wdth": 100}, inplace=True, updateFontNames=False
    )

    name = font["name"]
    for record in list(name.names):
        nid = record.nameID
        if nid in (NAME_FAMILY, NAME_TYPO_FAMILY):
            value = family
        elif nid in (NAME_SUBFAMILY, NAME_TYPO_SUBFAMILY):
            value = "Regular"
        elif nid == NAME_FULL:
            value = family
        elif nid == NAME_UNIQUE:
            value = f"{family};pinned-wght{weight}"
        elif nid == NAME_PS:
            value = f"{family}-Regular"
        else:
            continue
        name.setName(value, nid, record.platformID, record.platEncID, record.langID)

    # A pinned cut must not advertise itself as bold/italic; we select by family.
    font["OS/2"].usWeightClass = 400
    font["OS/2"].fsSelection = (font["OS/2"].fsSelection & ~0b100001) | 0b1000000  # REGULAR
    font["head"].macStyle = 0

    out = HERE / out_rel
    out.parent.mkdir(parents=True, exist_ok=True)
    font.save(out)
    return out


def main() -> None:
    USER_FONTS.mkdir(parents=True, exist_ok=True)
    produced = []
    for family, weight, out_rel in CUTS:
        path = instance_cut(family, weight, out_rel)
        produced.append(path)
        print(f"instanced {family} (wght={weight}) -> {path.relative_to(HERE)}")
    produced.append(MONO)

    for path in produced:
        shutil.copy2(path, USER_FONTS / path.name)
    subprocess.run(["fc-cache", "-f"], check=True, capture_output=True)

    for family in ("Bricolage800", "Bricolage600", "IBM Plex Mono"):
        found = subprocess.run(
            ["fc-match", family], check=True, capture_output=True, text=True
        ).stdout.strip()
        print(f"fc-match {family!r:18} -> {found}")


if __name__ == "__main__":
    main()
