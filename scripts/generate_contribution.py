#!/usr/bin/env python3
"""
generate_contribution.py

Builds the ONE playful moment of the README: "Contribution Runner" — a tiny
minimal character that travels across a simplified strip of real
contribution data, hopping higher on weeks with more activity (taller
"platforms" for higher contribution intensity).

This is intentionally NOT the standard GitHub contribution-snake SVG
re-skinned, and NOT a copy of github.com/czl9707's space-shooter — it's a
much smaller, calmer, single-character platformer-style motion built
directly from real per-week contribution intensity.

Animation is done with SMIL (<animateMotion>), which GitHub renders fine
for <img>-embedded SVGs (this is the same underlying technique the
popular contribution-snake generators rely on).

DATA INTEGRITY: platform heights are derived from real weekly max
contribution level (0-4) pulled from the public contribution calendar.
Nothing here is randomly generated for visual effect.
"""

import argparse
import os
import re
import sys
import urllib.request

PALETTE = {
    "bg": "#FFFFFF",
    "pale": "#EDF5D8",
    "light": "#C8DD72",
    "primary": "#83B547",
    "strong": "#5F963B",
    "dark": "#315D34",
    "border": "#DDE8CE",
    "text2": "#657267",
}

LEVEL_COLORS = [PALETTE["pale"], PALETTE["light"], PALETTE["primary"],
                PALETTE["strong"], PALETTE["dark"]]

FONT_STACK = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def fetch_contribution_calendar(username):
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-contribution-script"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode()
    rows = re.findall(r'<td[^>]*data-date="([0-9-]+)"[^>]*data-level="([0-9])"', html)
    return [{"date": d, "level": int(l)} for d, l in rows]


def build_svg(username, days, cols=20):
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)][-cols:]
    week_levels = [max((d["level"] for d in w), default=0) for w in weeks]

    width, height = 620, 130
    baseline = 100
    platform_w = 26
    gap = 4
    step = platform_w + gap

    platforms = ""
    path_points = []
    for i, level in enumerate(week_levels):
        px = 20 + i * step
        p_h = 6 + level * 6
        py = baseline - p_h
        color = LEVEL_COLORS[level]
        platforms += (
            f'<rect x="{px}" y="{py}" width="{platform_w}" height="{p_h}" rx="3" '
            f'fill="{color}" stroke="{PALETTE["border"]}" stroke-width="0.6"/>'
        )
        path_points.append((px + platform_w / 2, py - 10))

    # Build a smooth motion path across platform tops for the runner to follow
    motion_path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in path_points)

    char_size = 12
    runner = f'''
  <g id="runner">
    <rect x="{-char_size/2}" y="{-char_size}" width="{char_size}" height="{char_size}" rx="2"
          fill="{PALETTE["dark"]}"/>
    <rect x="{-char_size/2+2}" y="{-char_size+2}" width="2.5" height="2.5" fill="{PALETTE["bg"]}"/>
    <animateMotion dur="14s" repeatCount="indefinite" rotate="0"
                   path="{motion_path}"/>
  </g>'''

    svg = f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Contribution Runner: a small character travels across {username}'s recent weekly contribution intensity, real data, tallest platforms are the most active weeks">
  <rect x="0" y="0" width="{width}" height="{height}" rx="16" fill="{PALETTE["bg"]}" stroke="{PALETTE["border"]}"/>
  <text x="20" y="20" font-size="9.5" font-weight="600" fill="{PALETTE["text2"]}"
        font-family="{FONT_STACK}">Contribution Runner — last {cols} weeks, real activity</text>
  <line x1="20" y1="{baseline}" x2="{width-20}" y2="{baseline}" stroke="{PALETTE["border"]}" stroke-width="1"/>
  {platforms}
  {runner}
</svg>'''
    return svg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="Neha501")
    parser.add_argument("--out", default="../assets/generated/contribution-animation.svg")
    args = parser.parse_args()

    print("Fetching contribution calendar (public, unauthenticated)...", file=sys.stderr)
    days = fetch_contribution_calendar(args.username)
    svg = build_svg(args.username, days)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        f.write(svg)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
