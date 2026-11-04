"""Fetch the public contribution calendar (no token needed) -> data/contributions.json

GitHub serves the profile calendar as an HTML fragment at
https://github.com/users/<user>/contributions. Standard library only.

Usage: python scripts/fetch_contributions.py [username]
"""
import json
import os
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
USER = os.environ.get("GH_USER", "CodeYouness")


def fetch(user: str) -> str:
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-readme-heatmap"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse(html: str) -> list[dict]:
    cells = {}
    for m in re.finditer(r"<td[^>]*?data-date=\"([\d-]+)\"[^>]*?id=\"([^\"]+)\"[^>]*?data-level=\"(\d)\"", html):
        cells[m.group(2)] = {"date": m.group(1), "level": int(m.group(3)), "count": 0}
    for m in re.finditer(r"<tool-tip[^>]*?for=\"([^\"]+)\"[^>]*>([^<]*)", html):
        if m.group(1) in cells:
            n = re.match(r"\s*([\d,]+) contributions?", m.group(2))
            cells[m.group(1)]["count"] = int(n.group(1).replace(",", "")) if n else 0
    days = sorted(cells.values(), key=lambda d: d["date"])
    if not days:
        raise SystemExit("no contribution cells found - GitHub markup may have changed")
    return days


def stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)
    longest = cur = 0
    for d in days:
        cur = cur + 1 if d["count"] else 0
        longest = max(longest, cur)
    # current streak: today may still be empty, so allow starting from yesterday
    current = 0
    rev = list(reversed(days))
    if rev and rev[0]["count"] == 0:
        rev = rev[1:]
    for d in rev:
        if not d["count"]:
            break
        current += 1
    best = max(days, key=lambda d: d["count"])
    months = defaultdict(int)
    for d in days:
        months[d["date"][:7]] += d["count"]
    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": sum(1 for d in days if d["count"]),
        "monthly": dict(months),
    }


def main() -> None:
    user = sys.argv[1] if len(sys.argv) > 1 else USER
    days = parse(fetch(user))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps({"user": user, "generated": date.today().isoformat(), "stats": stats(days), "days": days}, indent=1),
        encoding="utf-8",
    )
    print(f"wrote {OUT.relative_to(ROOT)}: {len(days)} days, {stats(days)['total']} contributions")


if __name__ == "__main__":
    main()
