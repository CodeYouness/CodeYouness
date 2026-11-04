"""Render data/contributions.json as an animated heatmap SVG (contrib-heatmap.svg).

Boxes slide in along diagonals once on load, then freeze. Standard library only.
STATIC=1 emits a frozen frame.

Usage: python scripts/render_heatmap_svg.py
"""
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]  # none -> neon top
CELL, GAP = 11, 3
W = 860
LEFT, TOP = 58, 74
C_BG, C_BORDER, C_TXT, C_DIM, C_ACC = "#0d1117", "#30363d", "#c9d1d9", "#8b949e", "#39d353"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def level(count: int, q: list[int]) -> int:
    if count == 0:
        return 0
    for i, t in enumerate(q, start=1):
        if count <= t:
            return i
    return 5


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    days, st = data["days"], data["stats"]
    counts = sorted(d["count"] for d in days if d["count"])
    # quantile thresholds -> levels 1..4, level 5 = top ~3% (neon)
    q = [counts[int(len(counts) * f)] for f in (0.25, 0.5, 0.75, 0.97)] if counts else [1, 2, 3, 4]

    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    cells, month_labels, last_month = [], [], None
    max_diag = 0
    for i, d in enumerate(days):
        idx = i + offset
        wk, dow = divmod(idx, 7)
        x, y = LEFT + wk * (CELL + GAP), TOP + dow * (CELL + GAP)
        dt = date.fromisoformat(d["date"])
        # label a month on the first column whose top cell falls in it
        if (dow == 0 or i == 0) and dt.month != last_month:
            month_labels.append((x, MONTHS[dt.month - 1]))
            last_month = dt.month
        diag = wk + dow
        max_diag = max(max_diag, diag)
        cls = "" if STATIC else f' class="c" style="animation-delay:{0.3 + diag * 0.028:.3f}s"'
        cells.append(
            f'<rect{cls} x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" '
            f'fill="{PALETTE[level(d["count"], q)]}"><title>{d["count"]} on {d["date"]}</title></rect>'
        )
    # drop a month label that would collide with the next one
    labels = []
    for n, (x, m) in enumerate(month_labels):
        nxt = month_labels[n + 1][0] if n + 1 < len(month_labels) else 10**6
        if nxt - x >= 30:
            labels.append(f'<text x="{x}" y="{TOP - 8}" fill="{C_DIM}">{m}</text>')
    weekdays = "".join(
        f'<text x="{LEFT - 8}" y="{TOP + r * (CELL + GAP) + 10}" text-anchor="end" fill="{C_DIM}">{t}</text>'
        for r, t in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    grid_bottom = TOP + 7 * (CELL + GAP)
    fy = grid_bottom + 26
    legend_x = W - 20 - len(PALETTE) * (CELL + 3) - 34
    legend = (
        f'<text x="{legend_x - 8}" y="{fy}" text-anchor="end" fill="{C_DIM}">Less</text>'
        + "".join(
            f'<rect x="{legend_x + n * (CELL + 3)}" y="{fy - 10}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>'
            for n, c in enumerate(PALETTE)
        )
        + f'<text x="{legend_x + len(PALETTE) * (CELL + 3) + 4}" y="{fy}" fill="{C_DIM}">More</text>'
    )
    best = st["best_day"]
    best_d = date.fromisoformat(best["date"]).strftime("%b %d")
    footer = (
        f'<text x="{LEFT - 26}" y="{fy}" fill="{C_TXT}">'
        f'<tspan fill="{C_ACC}" font-weight="700">{st["total"]:,}</tspan> contributions in the last year'
        f'<tspan fill="{C_DIM}">  ·  </tspan>current streak <tspan fill="{C_ACC}">{st["current_streak"]}d</tspan>'
        f'<tspan fill="{C_DIM}">  ·  </tspan>longest <tspan fill="{C_ACC}">{st["longest_streak"]}d</tspan>'
        f'<tspan fill="{C_DIM}">  ·  </tspan>best day <tspan fill="{C_ACC}">{best["count"]}</tspan>'
        f'<tspan fill="{C_DIM}"> ({best_d})</tspan></text>'
    )
    H = fy + 22
    style = "" if STATIC else (
        "<style>"
        ".c{opacity:0;transform-box:fill-box;transform-origin:center;animation:drop .35s cubic-bezier(.2,.8,.3,1.2) forwards}"
        "@keyframes drop{from{opacity:0;transform:translateY(-9px) scale(.6)}to{opacity:1;transform:none}}"
        ".hd{opacity:0;animation:f .5s ease-out .1s forwards}@keyframes f{to{opacity:1}}"
        "</style>"
    )
    hd = "" if STATIC else ' class="hd"'
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="11" '
        f'role="img" aria-label="{st["total"]} GitHub contributions in the last year">',
        style,
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{C_BG}" stroke="{C_BORDER}"/>',
        f'<g{hd}><text x="{LEFT - 26}" y="30" font-size="13" fill="{C_TXT}" font-weight="700">'
        f'<tspan fill="{C_ACC}">$</tspan> git log --since="1 year ago" --author={data["user"]}</text>'
        f'<text x="{W - 20}" y="30" text-anchor="end" fill="{C_DIM}">updated {data["generated"]}</text></g>',
        *labels,
        weekdays,
        *cells,
        f"<g{hd}>{legend}{footer}</g>",
        "</svg>",
    ]
    OUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"wrote {OUT.name} ({W}x{H}, {len(days)} days)")


if __name__ == "__main__":
    main()
