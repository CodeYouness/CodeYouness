"""Terminal header whose tagline types itself, holds, deletes and moves to the next
phrase, looping forever. Pure SMIL, no external service.

Edit PHRASES, then run: python scripts/make_typing_svg.py
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "typing-header.svg"
STATIC = os.environ.get("STATIC") == "1"

NAME = "Hi, I'm Youness"
PHRASES = [
    "building LLM apps that actually ship",
    "PHP -> Python  ·  Laravel -> FastAPI",
    "RAG pipelines  ·  AI agents  ·  clean APIs",
    "automating the boring parts of the web",
    "football referee on weekends",
]

W, H = 860, 104
FONT = 17
CHAR_W = FONT * 0.6          # monospace advance
X0 = 46                      # text start (after the "$ " prompt)
Y_LINE = 76
SLOT = 5.0                   # seconds per phrase
C_BG, C_BORDER, C_TXT, C_DIM, C_ACC = "#0d1117", "#30363d", "#c9d1d9", "#8b949e", "#39d353"


def phrase_anim(i: int, n: int, chars: int) -> tuple[str, str]:
    """keyTimes/values for the clip width of phrase i (discrete, char by char)."""
    total = n * SLOT
    t0 = i * SLOT
    type_d, hold_d, del_d = SLOT * 0.42, SLOT * 0.36, SLOT * 0.14
    pts = [(0.0, 0.0)]
    for c in range(1, chars + 1):
        pts.append((t0 + type_d * c / chars, c * CHAR_W))
    for c in range(chars - 1, -1, -1):
        pts.append((t0 + type_d + hold_d + del_d * (chars - c) / chars, c * CHAR_W))
    pts.append((t0 + SLOT * 0.97, 0.0))  # sentinel: cursor switches off here
    kt, vals, last = [], [], -1.0
    for t, v in pts:
        f = max(t / total, last + 1e-4) if kt else 0.0
        kt.append(f"{f:.4f}")
        vals.append(f"{v:.1f}")
        last = f
    return ";".join(kt), ";".join(vals)


def main() -> None:
    n = len(PHRASES)
    total = n * SLOT
    defs, body = [], []
    for i, p in enumerate(PHRASES):
        if STATIC and i:
            continue
        if STATIC:
            body.append(f'<text x="{X0}" y="{Y_LINE}" fill="{C_TXT}" xml:space="preserve">{escape(p)}</text>')
            continue
        kt, vals = phrase_anim(i, n, len(p))
        defs.append(
            f'<clipPath id="p{i}"><rect x="{X0}" y="{Y_LINE - FONT}" height="{FONT + 6}" width="0">'
            f'<animate attributeName="width" calcMode="discrete" dur="{total}s" repeatCount="indefinite" '
            f'keyTimes="{kt}" values="{vals}"/></rect></clipPath>'
        )
        body.append(
            f'<text x="{X0}" y="{Y_LINE}" fill="{C_TXT}" clip-path="url(#p{i})" xml:space="preserve">{escape(p)}</text>'
        )
        # cursor follows the active phrase's edge
        xs = ";".join(f"{X0 + float(v):.1f}" for v in vals.split(";"))
        # visible from its first typed char until the sentinel (last point)
        npts = len(kt.split(";"))
        on = ";".join("0" if (j == 0 and i > 0) or j == npts - 1 else "1" for j in range(npts))
        body.append(
            f'<rect y="{Y_LINE - FONT + 2}" width="{CHAR_W:.1f}" height="{FONT + 2}" fill="{C_ACC}" opacity="0">'
            f'<animate attributeName="x" calcMode="discrete" dur="{total}s" repeatCount="indefinite" keyTimes="{kt}" values="{xs}"/>'
            f'<animate attributeName="opacity" calcMode="discrete" dur="{total}s" repeatCount="indefinite" keyTimes="{kt}" values="{on}"/>'
            f"</rect>"
        )
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" role="img" '
        f'aria-label="{escape(NAME)} - {escape(" / ".join(PHRASES))}">',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{C_BG}" stroke="{C_BORDER}"/>',
        f'<text x="20" y="40" font-size="22" font-weight="700" fill="{C_TXT}">{escape(NAME)}'
        f'<tspan fill="{C_ACC}"> _</tspan></text>',
        f'<text x="20" y="{Y_LINE}" font-size="{FONT}" fill="{C_ACC}" font-weight="700">$</text>',
        f'<g font-size="{FONT}">',
        "<defs>", *defs, "</defs>",
        *body,
        "</g>",
        "</svg>",
    ]
    OUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"wrote {OUT.name} ({n} phrases, {total:.0f}s loop)")


if __name__ == "__main__":
    main()
