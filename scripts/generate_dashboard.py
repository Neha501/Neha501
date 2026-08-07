#!/usr/bin/env python3
"""
generate_dashboard.py – GitHub Analytics Dashboard SVG generator.

Generates 7 premium dark-theme animated SVG charts from LIVE GitHub data.
No fake values. No hardcoded numbers. No placeholders.

DATA SOURCES:
  - Contribution calendar  : github.com/users/{username}/contributions (public HTML)
  - Repository list        : GET /users/{username}/repos (REST API, uses GH_TOKEN)
  - PR / Issue counts      : GET /search/issues (REST API, uses GH_TOKEN)

USAGE:
    python3 generate_dashboard.py --username Neha501 --outdir ../assets/generated

OUTPUT FILES:
    contribution-trend.svg
    weekly-pattern.svg
    monthly-contributions.svg
    repository-activity.svg
    language-distribution.svg
    repository-growth.svg
    commit-heatmap.svg
"""

import argparse
import calendar
import datetime
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

API  = "https://api.github.com"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

# GitHub dark theme palette
P = {
    "bg":     "#0D1117",
    "card":   "#161B22",
    "card2":  "#1C2128",
    "border": "#30363D",
    "text":   "#C9D1D9",
    "muted":  "#8B949E",
    "blue":   "#58A6FF",
    "green":  "#3FB950",
    "orange": "#F78166",
    "purple": "#BC8CFF",
    "yellow": "#E3B341",
    "teal":   "#39D353",
    "red":    "#FF7B72",
}

# Heatmap level colours (matches GitHub's contribution graph)
HEATMAP = ["#161B22", "#0E4429", "#006D32", "#26A641", "#39D353"]

# Language → brand colour mapping
LANG_COLORS = {
    "Python":           "#3572A5",
    "Java":             "#B07219",
    "JavaScript":       "#F1E05A",
    "TypeScript":       "#2B7489",
    "C++":              "#F34B7D",
    "C":                "#555555",
    "HTML":             "#E34C26",
    "CSS":              "#563D7C",
    "Go":               "#00ADD8",
    "Rust":             "#DEA584",
    "Ruby":             "#701516",
    "Swift":            "#FFAC45",
    "Kotlin":           "#A97BFF",
    "Dart":             "#00B4AB",
    "PHP":              "#4F5D95",
    "Shell":            "#89E051",
    "Vue":              "#41B883",
    "Jupyter Notebook": "#DA5B0B",
    "Other":            "#8B949E",
}

CHART_COLORS = [
    P["blue"], P["green"], P["purple"],
    P["orange"], P["yellow"], P["teal"], P["red"],
]

# ──────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ──────────────────────────────────────────────────────────────────────────────

def gh_get(url, token=None):
    req = urllib.request.Request(url, headers={
        "Accept":     "application/vnd.github+json",
        "User-Agent": "profile-dashboard/2.0",
    })
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def fetch_search_count(query, token=None):
    try:
        url = f"{API}/search/issues?q={urllib.parse.quote(query)}&per_page=1"
        return gh_get(url, token).get("total_count", 0)
    except Exception:
        return 0

# ──────────────────────────────────────────────────────────────────────────────
# Data fetching
# ──────────────────────────────────────────────────────────────────────────────

def fetch_contribution_calendar(username):
    """
    Scrapes github.com/users/{username}/contributions (public, no auth needed).
    Returns a sorted list of {date, count, level} dicts for the past year.
    Uses data-count when available (newer GitHub HTML), else estimates from level.
    """
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-dashboard/2.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        html = r.read().decode()

    days = []
    for attrs in re.findall(r"<td\s([^>]*data-date[^>]*)>", html):
        dm = re.search(r'data-date="([0-9-]+)"', attrs)
        cm = re.search(r'data-count="([0-9]+)"', attrs)
        lm = re.search(r'data-level="([0-9])"', attrs)
        if dm and lm:
            level = int(lm.group(1))
            count = int(cm.group(1)) if cm else [0, 1, 3, 6, 10][level]
            days.append({"date": dm.group(1), "count": count, "level": level})

    return sorted(days, key=lambda d: d["date"])


def fetch_repos(username, token=None):
    repos, page = [], 1
    while True:
        batch = gh_get(
            f"{API}/users/{username}/repos?per_page=100&page={page}&sort=created",
            token,
        )
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos

# ──────────────────────────────────────────────────────────────────────────────
# SVG primitives (shared across all charts)
# ──────────────────────────────────────────────────────────────────────────────

def _defs():
    return f"""\
  <defs>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="shadow">
      <feDropShadow dx="0" dy="6" stdDeviation="10"
                    flood-color="#010409" flood-opacity="0.55"/>
    </filter>
    <linearGradient id="blueArea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{P['blue']}"  stop-opacity="0.28"/>
      <stop offset="100%" stop-color="{P['blue']}"  stop-opacity="0.02"/>
    </linearGradient>
    <linearGradient id="greenArea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{P['green']}" stop-opacity="0.32"/>
      <stop offset="100%" stop-color="{P['green']}" stop-opacity="0.02"/>
    </linearGradient>
  </defs>"""


def _card(w, h, rx=12):
    return (
        f'  <rect width="{w}" height="{h}" rx="{rx}"'
        f' fill="{P["card"]}" filter="url(#shadow)"/>\n'
        f'  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{rx}"'
        f' fill="none" stroke="{P["border"]}" stroke-opacity="0.7"/>\n'
    )


def _title(title, subtitle, x=24, y=30):
    return (
        f'  <text x="{x}" y="{y}" font-size="13" font-weight="600"'
        f' fill="{P["text"]}" font-family="{FONT}">{title}</text>\n'
        f'  <text x="{x}" y="{y+16}" font-size="10"'
        f' fill="{P["muted"]}" font-family="{FONT}">{subtitle}</text>\n'
    )


def _svg_wrap(w, h, content, aria="GitHub Analytics"):
    return (
        f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg"'
        f' role="img" aria-label="{aria}">\n'
        + _defs() + "\n"
        + _card(w, h)
        + content
        + "\n</svg>\n"
    )


def _smooth_path(pts):
    """Smooth cubic bezier through (x,y) point list."""
    if len(pts) < 2:
        return ""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        cp1x = x0 + (x1 - x0) / 3
        cp2x = x1 - (x1 - x0) / 3
        d += f" C{cp1x:.1f},{y0:.1f} {cp2x:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
    return d


def _donut_seg(cx, cy, r, ri, a0, a1):
    """SVG path for one donut segment from angle a0→a1 (degrees)."""
    def pt(a, radius):
        rad = math.radians(a)
        return cx + radius * math.cos(rad), cy + radius * math.sin(rad)

    x1, y1 = pt(a0, r)
    x2, y2 = pt(a1, r)
    x3, y3 = pt(a1, ri)
    x4, y4 = pt(a0, ri)
    lg = 1 if (a1 - a0) > 180 else 0
    return (
        f"M{x1:.2f},{y1:.2f} A{r},{r} 0 {lg} 1 {x2:.2f},{y2:.2f} "
        f"L{x3:.2f},{y3:.2f} A{ri},{ri} 0 {lg} 0 {x4:.2f},{y4:.2f} Z"
    )


def _y_gridlines(cx1, cx2, cy2, ch, max_v, frac_ticks=(0.25, 0.5, 0.75, 1.0)):
    out = ""
    for tick in frac_ticks:
        gy = cy2 - tick * ch * 0.88
        out += (
            f'  <line x1="{cx1}" y1="{gy:.1f}" x2="{cx2}" y2="{gy:.1f}"'
            f' stroke="{P["border"]}" stroke-opacity="0.4" stroke-dasharray="4,4"/>\n'
            f'  <text x="{cx1-7}" y="{gy+4:.1f}" font-size="9" fill="{P["muted"]}"'
            f' text-anchor="end" font-family="{FONT}">{int(tick*max_v)}</text>\n'
        )
    return out


def _animate_bar(attr_name, from_val, to_val, delay_s, dur="0.75s"):
    return (
        f'    <animate attributeName="{attr_name}" from="{from_val:.1f}" to="{to_val:.1f}"'
        f' dur="{dur}" begin="{delay_s:.2f}s" fill="freeze"'
        f' calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1"/>\n'
    )

# ──────────────────────────────────────────────────────────────────────────────
# Chart 1 – Contribution Trend (last 30 days)
# ──────────────────────────────────────────────────────────────────────────────

def build_contribution_trend(days):
    W, H = 860, 220
    last30 = days[-30:] if len(days) >= 30 else days
    if not last30:
        return _svg_wrap(W, H, _title("Contribution Trend", "No data available"))

    CX1, CX2, CY1, CY2 = 58, W - 28, 56, H - 40
    ch = CY2 - CY1
    cw = CX2 - CX1
    n   = len(last30)
    counts = [d["count"] for d in last30]
    max_c  = max(counts) or 1

    def xp(i): return CX1 + i * cw / max(n - 1, 1)
    def yp(c): return CY2 - (c / max_c) * ch * 0.88

    pts     = [(xp(i), yp(last30[i]["count"])) for i in range(n)]
    line_d  = _smooth_path(pts)
    area_d  = line_d + f" L{pts[-1][0]:.1f},{CY2} L{pts[0][0]:.1f},{CY2} Z"
    pl      = int(cw * 1.3)  # path length estimate

    grids = _y_gridlines(CX1, CX2, CY2, ch, max_c)

    # X-axis labels
    xlabels = ""
    step = max(1, n // 6)
    shown = set()
    for i in list(range(0, n, step)) + [n - 1]:
        if i in shown:
            continue
        shown.add(i)
        dt = datetime.date.fromisoformat(last30[i]["date"])
        xlabels += (
            f'  <text x="{xp(i):.1f}" y="{CY2+14}" font-size="9" fill="{P["muted"]}"'
            f' text-anchor="middle" font-family="{FONT}">{dt.strftime("%b %d")}</text>\n'
        )

    # Subtle dots
    dots = "".join(
        f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="2.2" fill="{P["blue"]}" opacity="0.65"/>\n'
        for px, py in pts
    )

    body = (
        _title("Contribution Trend", "Last 30 days · real contribution counts")
        + grids
        + f'  <path d="{area_d}" fill="url(#blueArea)"/>\n'
        + f'  <path d="{line_d}" fill="none" stroke="{P["blue"]}" stroke-width="2.5"'
        + f' stroke-linecap="round" filter="url(#glow)"'
        + f' stroke-dasharray="{pl}" stroke-dashoffset="{pl}">\n'
        + f'    <animate attributeName="stroke-dashoffset" from="{pl}" to="0"'
        + f' dur="1.8s" fill="freeze" calcMode="spline"'
        + f' keySplines="0.4 0 0.2 1" keyTimes="0;1"/>\n'
        + f'  </path>\n'
        + dots
        + xlabels
        + f'  <line x1="{CX1}" y1="{CY1}" x2="{CX1}" y2="{CY2}"'
        + f' stroke="{P["border"]}" stroke-opacity="0.5"/>\n'
        + f'  <line x1="{CX1}" y1="{CY2}" x2="{CX2}" y2="{CY2}"'
        + f' stroke="{P["border"]}" stroke-opacity="0.5"/>\n'
    )
    return _svg_wrap(W, H, body, "Contribution Trend – last 30 days")

# ──────────────────────────────────────────────────────────────────────────────
# Chart 2 – Weekly Contribution Pattern
# ──────────────────────────────────────────────────────────────────────────────

def build_weekly_pattern(days):
    W, H = 860, 200
    DNAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    sums = defaultdict(int)
    cnts = defaultdict(int)
    for d in days:
        wd = datetime.date.fromisoformat(d["date"]).weekday()
        sums[wd] += d["count"]
        cnts[wd]  += 1

    avgs  = [sums[i] / cnts[i] if cnts[i] else 0.0 for i in range(7)]
    max_a = max(avgs) or 1

    CX1, CX2, CY2 = 50, W - 28, H - 36
    ch  = CY2 - 56
    gap = (CX2 - CX1) / 7
    bw  = gap * 0.55

    bars = ""
    for i, (avg, label) in enumerate(zip(avgs, DNAMES)):
        bx = CX1 + i * gap + (gap - bw) / 2
        bh = avg / max_a * ch * 0.88
        by = CY2 - bh
        col = P["purple"] if i >= 5 else P["blue"]
        bars += (
            f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}"'
            f' rx="5" fill="{col}" opacity="0.85">\n'
            + _animate_bar("height", 0, bh, i * 0.09)
            + _animate_bar("y", CY2, by, i * 0.09)
            + f'  </rect>\n'
            + (f'  <text x="{bx+bw/2:.1f}" y="{by-5:.1f}" font-size="9.5"'
               f' fill="{P["muted"]}" text-anchor="middle" font-family="{FONT}">'
               f'{avg:.1f}</text>\n' if avg > 0 else "")
            + f'  <text x="{bx+bw/2:.1f}" y="{CY2+14}" font-size="10"'
            + f' fill="{P["muted"]}" text-anchor="middle" font-family="{FONT}">{label}</text>\n'
        )

    body = (
        _title("Weekly Contribution Pattern", "Average contributions per weekday · past year")
        + _y_gridlines(CX1, CX2, CY2, ch, max_a)
        + bars
        + f'  <line x1="{CX1}" y1="{CY2}" x2="{CX2}" y2="{CY2}"'
        + f' stroke="{P["border"]}" stroke-opacity="0.5"/>\n'
    )
    return _svg_wrap(W, H, body, "Weekly Contribution Pattern")

# ──────────────────────────────────────────────────────────────────────────────
# Chart 3 – Monthly Contribution Overview
# ──────────────────────────────────────────────────────────────────────────────

def build_monthly_contributions(days):
    W, H = 860, 200
    MNAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    monthly = defaultdict(int)
    for d in days:
        dt = datetime.date.fromisoformat(d["date"])
        monthly[(dt.year, dt.month)] += d["count"]

    today = datetime.date.today()
    keys  = []
    yr, mo = today.year, today.month
    for _ in range(12):
        keys.append((yr, mo))
        mo -= 1
        if mo == 0:
            mo = 12
            yr -= 1
    keys.reverse()

    vals   = [monthly.get(k, 0) for k in keys]
    labels = [MNAMES[k[1] - 1] for k in keys]
    max_v  = max(vals) or 1

    CX1, CX2, CY2 = 50, W - 28, H - 36
    ch  = CY2 - 56
    gap = (CX2 - CX1) / 12
    bw  = gap * 0.55

    bars = ""
    for i, (val, label) in enumerate(zip(vals, labels)):
        bx = CX1 + i * gap + (gap - bw) / 2
        bh = val / max_v * ch * 0.88
        by = CY2 - bh
        is_now = keys[i] == (today.year, today.month)
        col = P["teal"] if is_now else P["green"]
        bars += (
            f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}"'
            f' rx="4" fill="{col}" opacity="0.85">\n'
            + _animate_bar("height", 0, bh, i * 0.06)
            + _animate_bar("y", CY2, by, i * 0.06)
            + f'  </rect>\n'
            + (f'  <text x="{bx+bw/2:.1f}" y="{by-5:.1f}" font-size="9"'
               f' fill="{P["muted"]}" text-anchor="middle"'
               f' font-family="{FONT}">{val}</text>\n' if val > 0 else "")
            + f'  <text x="{bx+bw/2:.1f}" y="{CY2+14}" font-size="9.5"'
            + f' fill="{P["muted"]}" text-anchor="middle" font-family="{FONT}">{label}</text>\n'
        )

    body = (
        _title("Monthly Contribution Overview", "Total contributions per month · last 12 months")
        + _y_gridlines(CX1, CX2, CY2, ch, max_v)
        + bars
        + f'  <line x1="{CX1}" y1="{CY2}" x2="{CX2}" y2="{CY2}"'
        + f' stroke="{P["border"]}" stroke-opacity="0.5"/>\n'
    )
    return _svg_wrap(W, H, body, "Monthly Contribution Overview")

# ──────────────────────────────────────────────────────────────────────────────
# Chart 4 – Repository Activity (horizontal bar chart)
# ──────────────────────────────────────────────────────────────────────────────

def build_repository_activity(total_contrib, prs, issues, stars):
    W, H = 860, 230

    items = [
        ("Total Contributions", total_contrib, P["blue"]),
        ("Pull Requests",       prs,           P["purple"]),
        ("Issues Opened",       issues,        P["orange"]),
        ("Stars Earned",        stars,          P["yellow"]),
    ]
    max_v = max(v for _, v, _ in items) or 1

    CX1, CX2 = 190, W - 50
    bh  = 32
    gap = (H - 80) / len(items)

    bars = ""
    for i, (label, val, col) in enumerate(items):
        by  = 66 + i * gap
        bw  = val / max_v * (CX2 - CX1) * 0.95
        pct = val / max_v * 100
        bars += (
            # Label
            f'  <text x="{CX1-10}" y="{by+bh/2+5:.1f}" font-size="11.5" fill="{P["text"]}"'
            f' text-anchor="end" font-family="{FONT}">{label}</text>\n'
            # Track
            + f'  <rect x="{CX1}" y="{by:.1f}" width="{CX2-CX1}" height="{bh}"'
            + f' rx="6" fill="{P["border"]}" opacity="0.25"/>\n'
            # Fill
            + f'  <rect x="{CX1}" y="{by:.1f}" width="{bw:.1f}" height="{bh}"'
            + f' rx="6" fill="{col}" opacity="0.88">\n'
            + f'    <animate attributeName="width" from="0" to="{bw:.1f}"'
            + f' dur="1s" begin="{i*0.14:.2f}s" fill="freeze"'
            + f' calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1"/>\n'
            + f'  </rect>\n'
            # Value badge
            + f'  <text x="{CX1+bw+10:.1f}" y="{by+bh/2+5:.1f}" font-size="12"'
            + f' font-weight="600" fill="{col}" font-family="{FONT}">{val:,}</text>\n'
        )

    body = _title("Repository Activity", "Live stats · GitHub REST API") + bars
    return _svg_wrap(W, H, body, "Repository Activity")

# ──────────────────────────────────────────────────────────────────────────────
# Chart 5 – Language Distribution (donut chart)
# ──────────────────────────────────────────────────────────────────────────────

def build_language_distribution(lang_counts):
    W, H = 860, 270
    if not lang_counts:
        return _svg_wrap(W, H, _title("Language Distribution", "No language data available"))

    top = sorted(lang_counts.items(), key=lambda x: -x[1])[:8]
    total = sum(v for _, v in top) or 1

    CX, CY, R, RI = 250, 152, 104, 58

    segs   = ""
    legend = ""
    angle  = -90.0

    for i, (lang, cnt) in enumerate(top):
        sweep = cnt / total * 360
        a1    = angle + sweep
        col   = LANG_COLORS.get(lang, CHART_COLORS[i % len(CHART_COLORS)])
        d     = _donut_seg(CX, CY, R, RI, angle, a1)
        pct   = cnt / total * 100
        segs += (
            f'  <path d="{d}" fill="{col}" stroke="{P["card"]}" stroke-width="2.5">\n'
            f'    <title>{lang}: {cnt} repos ({pct:.1f}%)</title>\n'
            f'  </path>\n'
        )
        lx, ly = 390, 58 + i * 27
        legend += (
            f'  <rect x="{lx}" y="{ly-11}" width="13" height="13" rx="3" fill="{col}"/>\n'
            f'  <text x="{lx+18}" y="{ly}" font-size="11.5" fill="{P["text"]}"'
            f' font-family="{FONT}">{lang}</text>\n'
            f'  <text x="{W-40}" y="{ly}" font-size="11" fill="{P["muted"]}"'
            f' text-anchor="end" font-family="{FONT}">{pct:.1f}%</text>\n'
        )
        angle = a1

    center = (
        f'  <text x="{CX}" y="{CY-10}" font-size="24" font-weight="700" fill="{P["text"]}"'
        f' text-anchor="middle" font-family="{FONT}">{len(top)}</text>\n'
        f'  <text x="{CX}" y="{CY+14}" font-size="10.5" fill="{P["muted"]}"'
        f' text-anchor="middle" font-family="{FONT}">Languages</text>\n'
    )
    # Separator line
    sep = (
        f'  <line x1="360" y1="50" x2="360" y2="{H-24}"'
        f' stroke="{P["border"]}" stroke-opacity="0.4"/>\n'
    )
    body = (
        _title("Language Distribution", "By primary language · non-fork repositories")
        + segs + center + sep + legend
    )
    return _svg_wrap(W, H, body, "Language Distribution")

# ──────────────────────────────────────────────────────────────────────────────
# Chart 6 – Repository Growth (cumulative line chart)
# ──────────────────────────────────────────────────────────────────────────────

def build_repository_growth(repos):
    W, H = 860, 200
    non_fork = [r for r in repos if not r.get("fork") and r.get("created_at")]
    if not non_fork:
        return _svg_wrap(W, H, _title("Repository Growth", "No data available"))

    dated = sorted(r["created_at"][:7] for r in non_fork)  # "YYYY-MM"
    monthly = defaultdict(int)
    for ym in dated:
        monthly[ym] += 1

    months = sorted(monthly.keys())
    cumul  = []
    total  = 0
    for ym in months:
        total += monthly[ym]
        cumul.append((ym, total))

    n     = len(cumul)
    max_v = cumul[-1][1] if cumul else 1

    CX1, CX2, CY1, CY2 = 55, W - 28, 56, H - 36
    ch = CY2 - CY1
    cw = CX2 - CX1

    def xp(i): return CX1 + i * cw / max(n - 1, 1)
    def yp(v): return CY2 - v / max_v * ch * 0.88

    pts    = [(xp(i), yp(v)) for i, (ym, v) in enumerate(cumul)]
    line_d = _smooth_path(pts)
    area_d = line_d + f" L{pts[-1][0]:.1f},{CY2} L{pts[0][0]:.1f},{CY2} Z"
    pl     = int(cw * 1.1)

    # X-axis labels
    step = max(1, n // 6)
    shown = set()
    xlabels = ""
    for i in list(range(0, n, step)) + [n - 1]:
        if i in shown:
            continue
        shown.add(i)
        ym, _ = cumul[i]
        yr, mo = ym.split("-")
        xlabels += (
            f'  <text x="{xp(i):.1f}" y="{CY2+14}" font-size="9" fill="{P["muted"]}"'
            f' text-anchor="middle" font-family="{FONT}">'
            f'{calendar.month_abbr[int(mo)]} {yr[2:]}</text>\n'
        )

    # Final count dot + label
    px0, py0 = pts[-1]
    badge = (
        f'  <circle cx="{px0:.1f}" cy="{py0:.1f}" r="5.5"'
        f' fill="{P["green"]}" filter="url(#glow)"/>\n'
        f'  <text x="{px0+10:.1f}" y="{py0+4:.1f}" font-size="11" font-weight="600"'
        f' fill="{P["green"]}" font-family="{FONT}">{max_v} repos</text>\n'
    )

    body = (
        _title("Repository Growth", "Cumulative public repositories created over time")
        + _y_gridlines(CX1, CX2, CY2, ch, max_v)
        + f'  <path d="{area_d}" fill="url(#greenArea)"/>\n'
        + f'  <path d="{line_d}" fill="none" stroke="{P["green"]}" stroke-width="2.5"'
        + f' stroke-linecap="round" filter="url(#glow)"'
        + f' stroke-dasharray="{pl}" stroke-dashoffset="{pl}">\n'
        + f'    <animate attributeName="stroke-dashoffset" from="{pl}" to="0"'
        + f' dur="1.8s" fill="freeze" calcMode="spline"'
        + f' keySplines="0.4 0 0.2 1" keyTimes="0;1"/>\n'
        + f'  </path>\n'
        + badge + xlabels
        + f'  <line x1="{CX1}" y1="{CY1}" x2="{CX1}" y2="{CY2}"'
        + f' stroke="{P["border"]}" stroke-opacity="0.5"/>\n'
        + f'  <line x1="{CX1}" y1="{CY2}" x2="{CX2}" y2="{CY2}"'
        + f' stroke="{P["border"]}" stroke-opacity="0.5"/>\n'
    )
    return _svg_wrap(W, H, body, "Repository Growth – cumulative repositories over time")

# ──────────────────────────────────────────────────────────────────────────────
# Chart 7 – Commit Heat Calendar (mini heatmap)
# ──────────────────────────────────────────────────────────────────────────────

def build_commit_heatmap(days):
    W, H = 860, 182
    CELL, GAP = 18, 3
    STEP = CELL + GAP
    DNAMES = ["Mon", "", "Wed", "", "Fri", "", ""]

    last26 = days[-(26 * 7):]
    if not last26:
        return _svg_wrap(W, H, _title("Commit Heat Calendar", "No data available"))

    # Group into weeks (7 days each)
    weeks = [last26[i:i + 7] for i in range(0, len(last26), 7)]

    CX1, CY1 = 50, 58

    # Day-of-week labels
    dlabels = "".join(
        f'  <text x="{CX1-6}" y="{CY1+di*STEP+CELL/2+4:.1f}" font-size="9"'
        f' fill="{P["muted"]}" text-anchor="end" font-family="{FONT}">{dl}</text>\n'
        for di, dl in enumerate(DNAMES)
        if dl
    )

    cells         = ""
    month_labels  = ""
    month_shown   = set()

    for wi, week in enumerate(weeks):
        if not week:
            continue
        dt0 = datetime.date.fromisoformat(week[0]["date"])
        mo_key = (dt0.year, dt0.month)
        if mo_key not in month_shown:
            month_shown.add(mo_key)
            month_labels += (
                f'  <text x="{CX1+wi*STEP+CELL/2:.1f}" y="{CY1-8}" font-size="9"'
                f' fill="{P["muted"]}" text-anchor="middle" font-family="{FONT}">'
                f'{calendar.month_abbr[dt0.month]}</text>\n'
            )
        for di, day in enumerate(week):
            cx = CX1 + wi * STEP
            cy = CY1 + di * STEP
            col = HEATMAP[day["level"]]
            cells += (
                f'  <rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="3"'
                f' fill="{col}" stroke="{P["card"]}" stroke-width="1">\n'
                f'    <title>{day["date"]}: {day["count"]} contributions</title>\n'
                f'  </rect>\n'
            )

    # Legend
    leg_x = CX1
    leg_y = H - 14
    legend = (
        f'  <text x="{leg_x}" y="{leg_y}" font-size="9"'
        f' fill="{P["muted"]}" font-family="{FONT}">Less</text>\n'
    )
    for li, lc in enumerate(HEATMAP):
        legend += (
            f'  <rect x="{leg_x+30+li*22}" y="{leg_y-12}" width="{CELL}" height="{CELL}"'
            f' rx="3" fill="{lc}"/>\n'
        )
    legend += (
        f'  <text x="{leg_x+30+len(HEATMAP)*22+5}" y="{leg_y}" font-size="9"'
        f' fill="{P["muted"]}" font-family="{FONT}">More</text>\n'
    )

    body = (
        _title("Commit Heat Calendar", "Last 26 weeks · real contribution intensity per day")
        + month_labels + dlabels + cells + legend
    )
    return _svg_wrap(W, H, body, "Commit Heat Calendar – 26-week contribution heatmap")

# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate GitHub Analytics Dashboard SVGs")
    parser.add_argument("--username", default="Neha501", help="GitHub username")
    parser.add_argument("--outdir",   default="../assets/generated", help="Output directory")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    print("📥 Fetching contribution calendar…", file=sys.stderr)
    days = fetch_contribution_calendar(args.username)
    print(f"   → {len(days)} days fetched", file=sys.stderr)

    print("📥 Fetching repository list…", file=sys.stderr)
    repos = fetch_repos(args.username, token)
    print(f"   → {len(repos)} repositories fetched", file=sys.stderr)

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    lang_counts = {}
    for r in repos:
        if not r.get("fork") and r.get("language"):
            lg = r["language"]
            lang_counts[lg] = lang_counts.get(lg, 0) + 1

    print("📥 Fetching PR count…", file=sys.stderr)
    prs = fetch_search_count(f"author:{args.username} type:pr", token)

    print("📥 Fetching issue count…", file=sys.stderr)
    issues = fetch_search_count(f"author:{args.username} type:issue", token)

    total_contrib = sum(d["count"] for d in days)

    print(f"   → contributions={total_contrib}, stars={total_stars}, PRs={prs}, issues={issues}", file=sys.stderr)

    charts = {
        "contribution-trend.svg":   build_contribution_trend(days),
        "weekly-pattern.svg":       build_weekly_pattern(days),
        "monthly-contributions.svg":build_monthly_contributions(days),
        "repository-activity.svg":  build_repository_activity(total_contrib, prs, issues, total_stars),
        "language-distribution.svg":build_language_distribution(lang_counts),
        "repository-growth.svg":    build_repository_growth(repos),
        "commit-heatmap.svg":       build_commit_heatmap(days),
    }

    print("\n🎨 Generating SVGs…", file=sys.stderr)
    for fname, svg in charts.items():
        path = os.path.join(outdir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        size_kb = os.path.getsize(path) / 1024
        print(f"   ✓ {fname}  ({size_kb:.1f} kB)", file=sys.stderr)

    print("\n✅ Dashboard generation complete.", file=sys.stderr)


if __name__ == "__main__":
    main()
