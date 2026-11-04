"""Convert source-prepped.png into a self-typing monochrome ASCII SVG.

Each row is revealed by a left-to-right clip wipe with a block cursor riding
the edge, staggered top to bottom. Plays once, then freezes (SMIL).
Set STATIC=1 to emit a frozen frame for previews.

Usage: python scripts/make_ascii_svg.py
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "youness-ascii.svg"

COLS = 84                     # characters per row
CHAR_W, CHAR_H = 6.6, 11.0    # monospace cell size in px (font-size 11)
RAMP = " .`:-=+*cs#%@"        # sparse -> dense. Light glyphs on a dark card,
                              # so BRIGHT pixels get DENSE glyphs.
FG = "#c9d1d9"
BG = "#0d1117"
ROW_DUR = 0.22                # seconds to type one row
ROW_GAP = 0.045               # stagger between rows
PAD = 14
CROP_BOTTOM = 0.95            # trim the very bottom of the photo
STATIC = os.environ.get("STATIC") == "1"


def grid() -> list[str]:
    src = Image.open(SRC).convert("LA")
    src = src.crop((0, 0, src.width, int(src.height * CROP_BOTTOM)))
    w, h = src.size
    rows = int(h / w * COLS * CHAR_W / CHAR_H)
    lum, alpha = (b.resize((COLS, rows), Image.LANCZOS) for b in src.split())
    a = np.asarray(ImageOps.autocontrast(lum, cutoff=1)).astype(np.float32) / 255.0
    a = np.minimum(a / 0.82, 1.0) ** 1.25  # compress highlights (white shirt), deepen shadows
    a = 0.10 + 0.82 * a                    # never fully blank / never all-@ inside the subject
    a *= np.asarray(alpha).astype(np.float32) / 255.0   # background -> space
    idx = (a * (len(RAMP) - 1)).round().astype(int)
    lines = ["".join(RAMP[i] for i in r).rstrip() for r in idx]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def main() -> None:
    lines = grid()
    width = PAD * 2 + COLS * CHAR_W
    height = PAD * 2 + len(lines) * CHAR_H
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        f'font-size="11" role="img" aria-label="ASCII portrait of Youness">',
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        "<defs>",
    ]
    body = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = PAD + (i + 1) * CHAR_H - 2.5
        lw = len(line) * CHAR_W
        begin = i * ROW_GAP
        if STATIC:
            body.append(f'<text x="{PAD}" y="{y:.1f}" fill="{FG}" xml:space="preserve">{escape(line)}</text>')
            continue
        out.append(
            f'<clipPath id="r{i}"><rect x="{PAD}" y="{y - CHAR_H + 2.5:.1f}" height="{CHAR_H}" width="0">'
            f'<animate attributeName="width" from="0" to="{lw:.1f}" begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        body.append(
            f'<text x="{PAD}" y="{y:.1f}" fill="{FG}" clip-path="url(#r{i})" xml:space="preserve">{escape(line)}</text>'
        )
        # cursor block riding the wipe edge, visible only while this row types
        body.append(
            f'<rect y="{y - CHAR_H + 3:.1f}" width="{CHAR_W:.1f}" height="{CHAR_H - 1}" fill="#39d353" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + lw:.1f}" begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.9" begin="{begin:.2f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.2f}s"/>'
            f"</rect>"
        )
    out.append("</defs>")
    out.extend(body)
    out.append("</svg>")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT.name} ({len(lines)} rows x {COLS} cols)")


if __name__ == "__main__":
    main()
