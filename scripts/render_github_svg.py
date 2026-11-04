"""Render data/github.json as two terminal panels:
  languages.svg  ->  $ cat languages.txt   (animated bars)
  activity.svg   ->  $ tail activity.log   (recently pushed repos + last commit)

Standard library only. STATIC=1 emits frozen frames.
Usage: python scripts/render_github_svg.py
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "github.json"
STATIC = os.environ.get("STATIC") == "1"

LANG_W, ACT_W = 340, 520           # side by side: 340 + 520 = 860
ROWS = 6
ROW_H = 27
TOP = 64
H = TOP + ROWS * ROW_H + 18
FONT = 12
CH = FONT * 0.6

C_BG, C_BAR, C_BORDER = "#0d1117", "#161b22", "#30363d"
C_TXT, C_DIM, C_ACC, C_KEY = "#c9d1d9", "#8b949e", "#39d353", "#58a6ff"
LANG_COLORS = {
    "PHP": "#4F5D95", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Python": "#3572A5",
    "HTML": "#e34c26", "CSS": "#663399", "SCSS": "#c6538c", "Vue": "#41b883", "Blade": "#f7523f",
    "Shell": "#89e051", "Jupyter Notebook": "#DA5B0B", "Dockerfile": "#384d54", "Java": "#b07219",
    "C#": "#178600", "Go": "#00ADD8", "Rust": "#dea584", "Svelte": "#ff3e00", "Astro": "#ff5a03",
}


def frame(w: int, title: str, cmd: str, body: list[str], style: str, label: str) -> str:
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="0 0 {w} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{FONT}" '
        f'role="img" aria-label="{escape(label)}">',
        style,
        f'<rect x=".5" y=".5" width="{w - 1}" height="{H - 1}" rx="10" fill="{C_BG}" stroke="{C_BORDER}"/>',
        f'<path d="M.5 10.5a10 10 0 0 1 10-10h{w - 21}a10 10 0 0 1 10 10V26H.5z" fill="{C_BAR}" stroke="{C_BORDER}"/>',
        '<circle cx="18" cy="14" r="5" fill="#f85149"/><circle cx="34" cy="14" r="5" fill="#d29922"/>'
        '<circle cx="50" cy="14" r="5" fill="#39d353"/>',
        f'<text x="{w / 2}" y="18" text-anchor="middle" fill="{C_DIM}" font-size="11">{escape(title)}</text>',
        f'<text x="18" y="48" font-weight="700"><tspan fill="{C_ACC}">$</tspan>'
        f'<tspan fill="{C_TXT}"> {escape(cmd)}</tspan></text>',
        *body,
        "</svg>",
    ])


STYLE = "" if STATIC else (
    "<style>"
    ".ln{opacity:0;animation:in .4s ease-out forwards}"
    "@keyframes in{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}"
    ".bar{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:grow 1s cubic-bezier(.2,.8,.2,1) forwards}"
    "@keyframes grow{to{transform:scaleX(1)}}"
    "</style>"
)


def a(i: int, cls: str = "ln", base: float = 0.3, step: float = 0.12) -> str:
    return "" if STATIC else f' class="{cls}" style="animation-delay:{base + i * step:.2f}s"'


def languages(data: dict) -> None:
    langs = data["languages"][:ROWS]
    rest = sum(l["pct"] for l in data["languages"][ROWS:])
    if rest and len(langs) == ROWS:
        langs[-1] = {"name": "Other", "pct": round(langs[-1]["pct"] + rest, 1)}
    bar_x = 33 + 11 * CH + 10
    bar_w = LANG_W - bar_x - 62
    body = []
    for i, l in enumerate(langs):
        y = TOP + i * ROW_H + 12
        col = LANG_COLORS.get(l["name"], "#8b949e")
        w = max(bar_w * l["pct"] / 100, 2)
        body.append(
            f'<g{a(i)}>'
            f'<circle cx="23" cy="{y - 4}" r="4" fill="{col}"/>'
            f'<text x="33" y="{y}" fill="{C_TXT}">{escape(l["name"][:11])}</text>'
            f'<rect x="{bar_x:.0f}" y="{y - 9}" width="{bar_w:.0f}" height="10" rx="3" fill="{C_BAR}"/>'
            f'<rect{a(i, "bar", 0.45)} x="{bar_x:.0f}" y="{y - 9}" width="{w:.1f}" height="10" rx="3" fill="{col}"/>'
            f'<text x="{LANG_W - 18}" y="{y}" text-anchor="end" fill="{C_DIM}">{l["pct"]:.1f}%</text>'
            f"</g>"
        )
    label = "Languages: " + ", ".join(f'{l["name"]} {l["pct"]}%' for l in langs)
    (ROOT / "languages.svg").write_text(
        frame(LANG_W, "~ languages", "cat languages.txt", body, STYLE, label), encoding="utf-8")


def ago(iso: str) -> str:
    d = datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))
    s = d.total_seconds()
    if s < 3600:
        return f"{max(int(s // 60), 1)}m ago"
    if s < 86400:
        return f"{int(s // 3600)}h ago"
    if s < 86400 * 60:
        return f"{int(s // 86400)}d ago"
    if s < 86400 * 365:
        return f"{int(s // (86400 * 30))}mo ago"
    return f"{int(s // (86400 * 365))}y ago"


def activity(data: dict) -> None:
    rows = data["activity"][:ROWS]
    repo_x = 18 + 9 * CH
    names = [r["repo"] or "private repo" for r in rows]
    repo_len = min(max((len(n) for n in names), default=8), 20) + 2
    msg_x = repo_x + 12 + (repo_len + 1) * CH
    max_msg = int((ACT_W - 18 - msg_x) / CH)
    body = []
    for i, r in enumerate(rows):
        y = TOP + i * ROW_H + 12
        col = LANG_COLORS.get(r.get("language") or "", C_DIM)
        when = f'<text x="18" y="{y}" fill="{C_DIM}">{ago(r["pushed_at"])}</text>'
        if r.get("private"):
            # anonymised: lock icon, no repo name, no commit message
            lock = (
                f'<rect x="{repo_x - 1}" y="{y - 7}" width="9" height="7" rx="1.5" fill="{C_DIM}"/>'
                f'<path d="M{repo_x + 1} {y - 7}v-2a2.5 2.5 0 0 1 5 0v2" fill="none" stroke="{C_DIM}" stroke-width="1.4"/>'
            )
            lang = r.get("language") or "code"
            body.append(
                f'<g{a(i)}>{when}{lock}'
                f'<text x="{repo_x + 12}" y="{y}" fill="{C_DIM}" font-style="italic">private repo</text>'
                f'<circle cx="{msg_x + 3}" cy="{y - 4}" r="3.5" fill="{col}"/>'
                f'<text x="{msg_x + 12}" y="{y}" fill="{C_DIM}">{escape(lang)} · commits hidden</text>'
                f"</g>"
            )
            continue
        msg = r["message"] or "(no commits yet)"
        if len(msg) > max_msg:
            msg = msg[: max_msg - 1] + "…"
        repo = r["repo"] if len(r["repo"]) <= 20 else r["repo"][:19] + "…"
        body.append(
            f'<g{a(i)}>{when}'
            f'<circle cx="{repo_x + 3}" cy="{y - 4}" r="3.5" fill="{col}"/>'
            f'<text x="{repo_x + 12}" y="{y}" fill="{C_KEY}" font-weight="700">{escape(repo)}</text>'
            f'<text x="{msg_x}" y="{y}" fill="{C_TXT}">{escape(msg)}</text>'
            f"</g>"
        )
    if not rows:
        body.append(f'<text x="18" y="{TOP + 12}" fill="{C_DIM}">no activity yet</text>')
    label = "Recent activity: " + ", ".join(names)
    (ROOT / "activity.svg").write_text(
        frame(ACT_W, "~ activity.log", f"tail -n {ROWS} activity.log", body, STYLE, label), encoding="utf-8")


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    languages(data)
    activity(data)
    print(f"wrote languages.svg + activity.svg ({len(data['languages'])} langs, {len(data['activity'])} repos)")


if __name__ == "__main__":
    main()
