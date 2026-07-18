#!/usr/bin/env python3
"""
generate_infocard.py

Renders a neofetch-style "info card" SVG, framed as a macOS terminal
window. Bio fields (Now/Building/Also/Edu) and Highlights are curated by
hand below since they're not the kind of thing an API can infer — but the
Stats block pulls live repo/star/follower/language counts from the GitHub
API on every run, so this file actually changes day to day.

Usage:
    GITHUB_TOKEN=... python3 generate_infocard.py <username> <output_svg>
"""

import argparse
import html
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _chrome

GREEN = "#3fb950"
ORANGE = "#e3b341"
CYAN = "#6ee7f9"
BODY = "#c9d1d9"
DIM = "#5b6472"

API = "https://api.github.com"

FIELDS = [
    ("Now", "Full-Stack Developer & AI/ML Engineer"),
    ("Building", "RAG pipelines, LangChain & LangGraph workflows, LLM-powered apps"),
    ("Also", "Project Admin @ ECWoC'26 · Contributor @ GSSOC'25"),
    ("Now", "Project Admin @ ECSoC'26"),
]

STACK = [
    ("Frontend", "React, Next.js, TypeScript, Tailwind"),
    ("Backend", "Node.js, FastAPI, Django"),
    ("AI / ML", "LangChain, LangGraph, RAG Pipelines, PyTorch"),
    ("Cloud", "Docker, PostgreSQL, Supabase, Git"),
]

HIGHLIGHTS = [
    "Top 6 Project Admin at Elite Coders Winter of Code (ECWoC'26)",
    "Mentored 50+ contributors and reviewed 200+ PRs across open source",
]

# Used only if the live API call fails (e.g. a local preview run with no
# token / no network) so the script still produces a representative card.
SAMPLE_STATS = {
    "public_repos": 24,
    "followers": 40,
    "total_stars": 18,
    "top_lang": "Python",
    "prs_merged": 12,
    "issues_raised": 9,
}



def api_get(path: str, token: str | None):
    req = urllib.request.Request(f"{API}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fetch_stats(username: str, token: str | None) -> dict:
    user = api_get(f"/users/{username}", token)
    repos, page = [], 1
    while True:
        batch = api_get(f"/users/{username}/repos?per_page=100&page={page}&type=owner", token)
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    langs: dict[str, int] = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            langs[lang] = langs.get(lang, 0) + 1
    top_lang = max(langs, key=langs.get) if langs else "-"

    prs_merged = api_get(f"/search/issues?q=author:{username}+type:pr+is:merged", token)["total_count"]
    issues_raised = api_get(f"/search/issues?q=author:{username}+type:issue", token)["total_count"]

    return {
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "total_stars": total_stars,
        "top_lang": top_lang,
        "prs_merged": prs_merged,
        "issues_raised": issues_raised,
    }


def render(username: str, stats: dict, width: int = 620, font_size: int = 13) -> str:
    pad = 20
    line_h = 24
    y = pad + 14
    lines = []

    def add(segments, size=font_size, dy=line_h, x=pad):
        nonlocal y
        spans = "".join(f'<tspan fill="{fill}">{html.escape(text)}</tspan>' for text, fill in segments)
        lines.append(f'<text x="{x}" y="{y}" font-size="{size}" xml:space="preserve">{spans}</text>')
        y += dy

    def row(label, value):
        nonlocal y
        lines.append(
            f'<text x="{pad}" y="{y}" font-size="{font_size}" font-weight="bold" fill="{ORANGE}">{html.escape(label)}</text>'
            f'<text x="{pad + label_col}" y="{y}" font-size="{font_size}" fill="{BODY}">{html.escape(value)}</text>'
        )
        y += line_h

    def divider():
        nonlocal y
        lines.append(f'<line x1="{pad}" y1="{y - line_h/2}" x2="{width - pad}" y2="{y - line_h/2}" '
                      f'stroke="#1f2733" stroke-width="1"/>')
        y += 10

    label_col = 150

    add([(username, GREEN), ("@github", BODY)], size=17, dy=34)

    for label, value in FIELDS:
        row(label, value)

    y += 6
    divider()

    add([("- Stack", CYAN)], dy=line_h + 4)
    for label, value in STACK:
        row(label, value)

    y += 6
    divider()

    # Live block — the only section that changes on its own between runs.
    row("Repos", str(stats["public_repos"]))
    row("Stars", str(stats["total_stars"]))
    row("Followers", str(stats["followers"]))
    row("Top lang", stats["top_lang"])
    row("Issues raised", str(stats["issues_raised"]))
    row("PRs merged", str(stats["prs_merged"]))

    y += 6
    divider()

    add([("- Highlights", CYAN)], dy=line_h + 4)
    for item in HIGHLIGHTS:
        lines.append(
            f'<circle cx="{pad + 4}" cy="{y - 5}" r="3.5" fill="{GREEN}"/>'
            f'<text x="{pad + 18}" y="{y}" font-size="{font_size}" fill="{BODY}">{html.escape(item)}</text>'
        )
        y += line_h

    body_height = y + pad - 6
    body = "".join(lines)
    title = f"{username}@github: ~$ neofetch"
    return _chrome.window(width, body_height, title, body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("username")
    ap.add_argument("output")
    ap.add_argument("--fetch-user", default=None,
                     help="Real GitHub username to pull live stats for, if different from the display handle")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    fetch_user = args.fetch_user or args.username
    try:
        stats = fetch_stats(fetch_user, token)
    except Exception as e:
        print(f"warning: live fetch failed ({e}), using sample data", file=sys.stderr)
        stats = SAMPLE_STATS

    svg = render(args.username, stats)
    with open(args.output, "w") as f:
        f.write(svg)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
