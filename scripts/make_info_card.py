"""Neofetch-style info card as an animated SVG.

Edit CARD below, then run: python scripts/make_info_card.py
STATIC=1 emits a frozen frame (handy for local previews).
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

USER = "youness@github"

# (key, value). key=None -> section header; ("", value) -> continuation line.
CARD = [
    ("Role", "Full-Stack Developer -> AI Engineer"),
    ("Based", "Venice, Italy"),
    ("Focus", "LLM apps · RAG · AI agents"),
    (None, "stack"),
    ("Web", "PHP · Laravel · JS/TS · React · Vue"),
    ("AI", "Python · FastAPI · LangChain · LangGraph"),
    ("Data", "MySQL · ChromaDB · Pydantic"),
    ("Ops", "Docker · Git · GitHub Actions"),
    (None, "highlights"),
    ("Shipped", "customer voting portal, end-to-end"),
    ("Runs", "3 production web portals"),
    ("Trained", "700h Full-Stack bootcamp"),
    (None, "contact"),
    ("LinkedIn", "in/younesslijassi"),
    ("Mail", "ylijassi@gmail.com"),
]

W = 490
PAD_X = 20
LINE_H = 18.5
TOP = 52
KEY_W = 82

C_BG = "#0d1117"
C_BAR = "#161b22"
C_BORDER = "#30363d"
C_USER = "#39d353"
C_KEY = "#58a6ff"
C_VAL = "#c9d1d9"
C_DIM = "#8b949e"
PALETTE = ["#f85149", "#d29922", "#39d353", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]

STEP = 0.11  # seconds between lines


def anim(i: int) -> str:
    if STATIC:
        return ""
    return f' class="ln" style="animation-delay:{0.25 + i * STEP:.2f}s"'


def main() -> None:
    rows = []
    y = TOP
    # user@host + underline, like neofetch
    rows.append(
        f'<g{anim(0)}><text x="{PAD_X}" y="{y}" font-weight="700">'
        f'<tspan fill="{C_USER}">youness</tspan><tspan fill="{C_VAL}">@</tspan>'
        f'<tspan fill="{C_USER}">github</tspan></text></g>'
    )
    y += LINE_H
    rows.append(f'<g{anim(1)}><text x="{PAD_X}" y="{y}" fill="{C_DIM}">{"-" * len(USER)}</text></g>')
    i = 2
    for key, val in CARD:
        if key is None:
            y += 6
            y += LINE_H
            rows.append(
                f'<g{anim(i)}><text x="{PAD_X}" y="{y}" fill="{C_DIM}">'
                f'<tspan fill="{C_USER}">~</tspan> {escape(val)}</text>'
                f'<line x1="{PAD_X + 14 + len(val) * 7.6:.0f}" y1="{y - 4}" x2="{W - PAD_X}" y2="{y - 4}" '
                f'stroke="{C_BORDER}" stroke-dasharray="2 3"/></g>'
            )
        else:
            y += LINE_H
            k = f'<tspan fill="{C_KEY}" font-weight="700">{escape(key)}</tspan>' if key else ""
            colon = f'<tspan fill="{C_DIM}">:</tspan>' if key else ""
            rows.append(
                f'<g{anim(i)}><text x="{PAD_X}" y="{y}">{k}{colon}</text>'
                f'<text x="{PAD_X + KEY_W}" y="{y}" fill="{C_VAL}">{escape(val)}</text></g>'
            )
        i += 1
    # neofetch colour blocks
    y += LINE_H
    blocks = "".join(
        f'<rect x="{PAD_X + n * 26}" y="{y - 4}" width="22" height="12" rx="2" fill="{c}"/>'
        for n, c in enumerate(PALETTE)
    )
    rows.append(f"<g{anim(i)}>{blocks}</g>")
    # blinking prompt cursor at the end
    y += LINE_H + 8
    blink = "" if STATIC else ' class="blink"'
    rows.append(
        f'<g{anim(i + 1)}><text x="{PAD_X}" y="{y}" fill="{C_USER}">$</text>'
        f'<rect{blink} x="{PAD_X + 14}" y="{y - 11}" width="8" height="14" fill="{C_VAL}"/></g>'
    )
    H = int(y + 22)

    style = "" if STATIC else (
        "<style>"
        ".ln{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        ".blink{animation:b 1.1s steps(1) infinite}"
        "@keyframes b{50%{opacity:0}}"
        "</style>"
    )
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="12.5" '
        f'role="img" aria-label="Youness - info card">',
        style,
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{C_BG}" stroke="{C_BORDER}"/>',
        f'<path d="M.5 10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V26H.5z" fill="{C_BAR}" stroke="{C_BORDER}"/>',
        '<circle cx="18" cy="14" r="5" fill="#f85149"/><circle cx="34" cy="14" r="5" fill="#d29922"/>'
        '<circle cx="50" cy="14" r="5" fill="#39d353"/>',
        f'<text x="{W / 2}" y="18" text-anchor="middle" fill="{C_DIM}" font-size="11">~ neofetch</text>',
        *rows,
        "</svg>",
    ]
    OUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"wrote {OUT.name} ({W}x{H})")


if __name__ == "__main__":
    main()
