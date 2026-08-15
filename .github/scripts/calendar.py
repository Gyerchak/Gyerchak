#!/usr/bin/env python3
"""Generate stacked per-year contribution calendars (GitHub-style) for the
profile README. Years start at 2026 and a new year block is added
automatically once it has contributions. Writes contributions.svg (light
palette); the workflow converts it to contributions-dark.svg via darkify.py."""

import datetime
import json
import os
import urllib.request

OWNER = "Gyerchak"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
START_YEAR = 2026

LEVELS = [(1, "#9be9a8"), (3, "#40c463"), (5, "#30a14e"), (9, "#216e39")]
EMPTY = "#ebedf0"
TEXT = "#777777"
HEAD = "#0366d6"
MUTED = "#959da5"
OUTLINE = "rgba(27,31,35,0.06)"
GREEN = "#216e39"
WHITE = "#ffffff"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

CELL = 11
GAP = 3
STEP = CELL + GAP
COLS = 53
ROWS = 7
TOP = 26
CHIP_H = 34
LEGEND_H = 26
WEEK_W = 28
PAD_X = 10
WIDTH = WEEK_W + COLS * STEP + PAD_X * 2 + 20
BLOCK_H = TOP + ROWS * STEP + LEGEND_H

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def graphql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json",
            "User-Agent": "Gyerchak-profile-calendar",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"]))
    return data


def fetch_counts(year):
    data = graphql(QUERY, {
        "login": OWNER,
        "from": "%d-01-01T00:00:00Z" % year,
        "to": "%d-12-31T23:59:59Z" % year,
    })
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    counts = {}
    for week in cal["weeks"]:
        for day in week["contributionDays"]:
            counts[day["date"]] = day["contributionCount"]
    return cal["totalContributions"], counts


def level_color(n):
    if n <= 0:
        return EMPTY
    color = LEVELS[0][1]
    for threshold, col in LEVELS:
        if n >= threshold:
            color = col
    return color


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_year_block(year, total, counts):
    first = datetime.date(year, 1, 1)
    last = datetime.date(year, 12, 31)
    offset = first.weekday()  # Monday == 0
    days = (last - first).days + 1

    parts = []
    parts.append(
        '<rect x="%d" y="0" width="52" height="22" rx="11" fill="%s"/>'
        % (PAD_X, GREEN)
    )
    parts.append(
        '<text x="%d" y="15" text-anchor="middle" font-size="12" fill="%s" font-family="%s">%d</text>'
        % (PAD_X + 26, WHITE, FONT, year)
    )
    parts.append(
        '<text x="%d" y="15" font-size="13" fill="%s" font-family="%s">%d commits</text>'
        % (PAD_X + 62, TEXT, FONT, total)
    )

    for m in range(1, 13):
        d = datetime.date(year, m, 1)
        col = (d.toordinal() - first.toordinal() + offset) // 7
        if col >= COLS:
            continue
        x = PAD_X + WEEK_W + col * STEP
        abbr = d.strftime("%b")
        parts.append(
            '<text x="%d" y="%d" font-size="11" fill="%s" font-family="%s">%s</text>'
            % (x, CHIP_H + 12, TEXT, FONT, esc(abbr))
        )

    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            '<text x="%d" y="%d" font-size="11" fill="%s" font-family="%s">%s</text>'
            % (PAD_X, CHIP_H + TOP + row * STEP + 8, MUTED, FONT, label)
        )

    for i in range(days):
        d = first + datetime.timedelta(days=i)
        count = counts.get(d.isoformat(), 0)
        col = (i + offset) // 7
        row = (i + offset) % 7
        if col >= COLS:
            continue
        x = PAD_X + WEEK_W + col * STEP
        y = CHIP_H + TOP + row * STEP
        parts.append(
            '<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s" stroke="%s"/>'
            % (x, y, CELL, CELL, level_color(count), OUTLINE)
        )

    ly = CHIP_H + TOP + ROWS * STEP + 14
    parts.append(
        '<text x="%d" y="%d" font-size="11" fill="%s" font-family="%s">Less</text>'
        % (PAD_X, ly, TEXT, FONT)
    )
    legend = [EMPTY] + [c for _, c in LEVELS]
    for k in range(5):
        x = PAD_X + 40 + k * STEP
        parts.append(
            '<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s" stroke="%s"/>'
            % (x, ly - 9, CELL, CELL, legend[k], OUTLINE)
        )
    parts.append(
        '<text x="%d" y="%d" font-size="11" fill="%s" font-family="%s">More</text>'
        % (PAD_X + 40 + 5 * STEP + 6, ly, TEXT, FONT)
    )
    return "\n".join(parts)


def main():
    now = datetime.date.today()
    blocks = []
    for year in range(START_YEAR, now.year + 1):
        try:
            total, counts = fetch_counts(year)
        except Exception as err:  # noqa: BLE001
            print("calendar %d: %s" % (year, err), flush=True)
            if year == now.year:
                total, counts = 0, {}
            else:
                continue
        if total <= 0 and year != now.year:
            continue
        blocks.append((year, total, counts))

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="__HEIGHT__">' % WIDTH,
        '<style>text{font-size:12px}</style>',
    ]
    y = 0
    for year, total, counts in blocks:
        parts.append('<g transform="translate(0, %d)">' % y)
        parts.append(render_year_block(year, total, counts))
        parts.append("</g>")
        y += CHIP_H + BLOCK_H
    svg = "\n".join(parts).replace("__HEIGHT__", str(y))
    svg += "\n</svg>\n"
    with open("contributions.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("contribution calendars: %d year(s)" % len(blocks))


if __name__ == "__main__":
    main()
