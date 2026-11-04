"""Fetch repos, languages and recent activity -> data/github.json

Standard library only.

Tokens (all optional):
  PROFILE_TOKEN  fine-grained PAT, read-only. Adds your PRIVATE repos, anonymised:
                 their code counts towards the language stats, and in the activity
                 log they appear as "private repo" - no name, no commit message.
  GITHUB_TOKEN   provided automatically in Actions (public repos only, 1000 req/h).
  none           public repos only, 60 req/h; languages use a cheaper estimate.

Usage: python scripts/fetch_github_data.py [username]
"""
import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "github.json"
USER = os.environ.get("GH_USER", "CodeYouness")
API = "https://api.github.com"
ACTIVITY_N = 6

PROFILE_TOKEN = os.environ.get("PROFILE_TOKEN", "").strip()
TOKEN = PROFILE_TOKEN or os.environ.get("GITHUB_TOKEN", "").strip()


def get(path: str):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(API + path, headers=headers), timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def list_repos(user: str) -> list[dict]:
    if PROFILE_TOKEN:
        repos, page = [], 1
        while True:
            batch = get(f"/user/repos?affiliation=owner&visibility=all&sort=pushed&per_page=100&page={page}")
            repos += batch
            if len(batch) < 100:
                break
            page += 1
    else:
        repos = get(f"/users/{user}/repos?per_page=100&type=owner&sort=pushed")
    return [
        r for r in repos
        if not r["fork"] and not r["archived"] and r["name"].lower() != user.lower()
    ]


def main() -> None:
    user = sys.argv[1] if len(sys.argv) > 1 else USER
    repos = list_repos(user)
    repos.sort(key=lambda r: r["pushed_at"] or "", reverse=True)

    langs: Counter = Counter()
    if TOKEN:
        # exact: bytes of every language in every repo (1 call per repo)
        for r in repos:
            for lang, n in get(f"/repos/{r['full_name']}/languages").items():
                langs[lang] += n
    else:
        # cheap fallback without a token: primary language weighted by repo size
        for r in repos:
            if r["language"]:
                langs[r["language"]] += max(r["size"], 1)
    total = sum(langs.values()) or 1
    languages = [{"name": k, "pct": round(v * 100 / total, 1)} for k, v in langs.most_common()]

    activity = []
    for r in repos[:ACTIVITY_N]:
        if r["private"]:
            # anonymised: never write a private repo's name or commits to the public repo
            activity.append({"repo": None, "private": True, "pushed_at": r["pushed_at"],
                             "language": r["language"], "message": ""})
            continue
        msg = ""
        try:
            commits = get(f"/repos/{r['full_name']}/commits?per_page=1")
            if commits:
                msg = commits[0]["commit"]["message"].splitlines()[0]
        except Exception:  # empty repo -> 409
            pass
        activity.append({"repo": r["name"], "private": False, "pushed_at": r["pushed_at"],
                         "language": r["language"], "message": msg})

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "user": user,
        "generated": date.today().isoformat(),
        "repos_counted": len(repos),
        "includes_private": bool(PROFILE_TOKEN),
        "languages": languages,
        "activity": activity,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(repos)} repos, {len(languages)} languages, "
          f"private={'yes' if PROFILE_TOKEN else 'no'}")


if __name__ == "__main__":
    main()
