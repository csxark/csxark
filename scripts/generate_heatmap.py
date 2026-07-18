#!/usr/bin/env python3
"""
Fetches the last 12 months of contribution counts via the GitHub GraphQL
API and renders a heatmap SVG themed to the profile's cyan/dark palette
(rather than GitHub's default green squares).

Requires a token with read access to public data — pass via GITHUB_TOKEN.
GraphQL has no unauthenticated tier, so this cannot be dry-run without one.

Usage:
    GITHUB_TOKEN=... python3 generate_heatmap.py <username> <output_svg>
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_calendar(username: str, token: str):
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": QUERY, "variables": {"login": username}}).encode(),
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


# Cyan intensity ramp, darkest (no contributions) to brightest (heavy day).
LEVEL_COLORS = ["#0d1117", "#0e4b52", "#0f7a87", "#14b8c4", "#22D3EE"]


def level_for(count: int, max_count: int) -> int:
    if count == 0 or max_count == 0:
        return 0
    ratio = count / max_count
    if ratio > 0.75:
        return 4
    if ratio > 0.5:
        return 3
    if ratio > 0.25:
        return 2
    return 1


def render_svg(weeks: list, bg: str) -> str:
    cell = 11
    gap = 3
    cols = len(weeks)
    rows = 7
    width = cols * (cell + gap) + 40
    height = rows * (cell + gap) + 40

    all_counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    max_count = max(all_counts) if all_counts else 0

    squares = []
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            date = datetime.strptime(day["date"], "%Y-%m-%d")
            di = date.weekday()  # Mon=0 .. Sun=6
            count = day["contributionCount"]
            level = level_for(count, max_count)
            x = 20 + wi * (cell + gap)
            y = 20 + di * (cell + gap)
            squares.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{LEVEL_COLORS[level]}"><title>{day["date"]}: {count} contributions</title></rect>'
            )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="{bg}" rx="10"/>
  {"".join(squares)}
</svg>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("username")
    ap.add_argument("output")
    ap.add_argument("--bg", default="#0D1117")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("error: GITHUB_TOKEN is required (GraphQL has no unauthenticated tier)", file=sys.stderr)
        sys.exit(1)

    weeks = fetch_calendar(args.username, token)
    svg = render_svg(weeks, args.bg)
    with open(args.output, "w") as f:
        f.write(svg)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
