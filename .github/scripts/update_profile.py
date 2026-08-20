#!/usr/bin/env python3
"""Regenerate the profile README repo status list (all public non-fork repos
of Gyerchak), grouped by category. The section is replaced between HTML
comment markers in README.md. Tables are padded so every category table has
equal column widths (max across all repos)."""

import json
import os
import re
import urllib.request
import urllib.error

OWNER = "Gyerchak"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"

START_STATUS = "<!-- STATUS:START -->"
END_STATUS = "<!-- STATUS:END -->"
START_REPOS = "<!-- REPOS:START -->"
END_REPOS = "<!-- REPOS:END -->"

CATEGORIZED = {
    "Minkraft": "🎮 Games",
    "Moba": "🎮 Games",
    "Globe-Game": "🎮 Games",
    "GameTemplate": "🎮 Games",
    "OpenCode-OpenGLMiniGames": "🎮 Games",
    "XiaomiWatchApp": "⌚ Devices & hardware",
    "XiaomiWatchLinuxConnect": "⌚ Devices & hardware",
    "LinuxXiaomiWatchApp": "⌚ Devices & hardware",
    "HeadControll": "⌚ Devices & hardware",
    "StockAnalyzer": "📈 Markets & finance",
    "DemandPolandEu": "📈 Markets & finance",
    "DenSupply": "📈 Markets & finance",
    "MAAW-Supply": "📈 Markets & finance",
    "OpenCode-Box-AgentMixer": "🤖 AI, bots & agents",
    "OpenCode-DiscordBot": "🤖 AI, bots & agents",
    "Remote-OpenCode-DiscordBot": "🤖 AI, bots & agents",
    "OpenCodeAndroidChat": "🤖 AI, bots & agents",
    "OpenCodeLiveTranslator": "🤖 AI, bots & agents",
    "AiBotniak": "🤖 AI, bots & agents",
    "HistorAI": "🤖 AI, bots & agents",
    "ShrimpFarmer-Agent": "🤖 AI, bots & agents",
    "MAAW-Bot": "🤖 AI, bots & agents",
    "EuTransparencyChecker": "🌍 EU & transparency",
    "NiceEuTransparency": "🌍 EU & transparency",
    "CopyRightsChecker": "🌍 EU & transparency",
    "EuDemand": "🌍 EU & transparency",
}

OTHER = "🗂️ Everything else"
HEADERS = ["Repo", "Status", "Description", "Language", "License", "Stars"]


def api(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + TOKEN,
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def has_release(name):
    try:
        api("/repos/%s/%s/releases/latest" % (OWNER, name))
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise


def replace_section(text, start, end, replacement):
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    return pattern.sub(start + "\n" + replacement + "\n" + end, text)


STATUS_OVERRIDES = {
    "OpenCode-Box-AgentMixer": "🧪 alpha",
    "Minkraft": "🌱 pre-alpha",
}

def build_rows(repos, released_names):
    """Return list of rows; each row is a list of 6 cell strings."""
    rows = []
    for r in repos:
        name = r["name"]
        if name in STATUS_OVERRIDES:
            status = STATUS_OVERRIDES[name]
        elif name in released_names:
            tag = api("/repos/%s/%s/releases/latest" % (OWNER, name)).get("tag_name", "released")
            status = "✅ `%s`" % tag
        else:
            status = "🚧 in development"
        desc = (r.get("description") or "").replace("|", "/")
        lang = r.get("language") or "—"
        lic = (r.get("license") or {}).get("spdx_id") or "—"
        stars = "⭐ %s" % r.get("stargazers_count", 0)
        rows.append(["[%s](https://github.com/%s/%s)" % (name, OWNER, name), status, desc, lang, lic, stars])
    return rows


def md_row(cells, widths):
    return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"


def render_tables(groups, cat_order, released_names):
    """Render one padded table per non-empty category. All tables share the
    same column widths (max across every repo row)."""
    all_rows = []
    for cat in cat_order:
        for r in groups[cat]:
            all_rows.append(r)
    rows = build_rows(all_rows, released_names)

    # column widths: header text vs content, description gets a sane cap
    maxw = None
    table_rows_by_cat = {}
    idx = 0
    for cat in cat_order:
        g = groups[cat]
        if not g:
            continue
        table_rows_by_cat[cat] = rows[idx:idx + len(g)]
        idx += len(g)

    # compute widths across ALL tables at once
    desc_cap = 60
    cellw = []
    for i in range(6):
        hw = len(HEADERS[i])
        w = hw
        for cat, trows in table_rows_by_cat.items():
            for row in trows:
                v = row[i]
                if i == 2 and len(v) > desc_cap:
                    v = v[:desc_cap - 1] + "…"
                    row[i] = v
                w = max(w, len(v))
        cellw.append(w)

    sep = "| " + " | ".join("-" * w for w in cellw) + " |"

    chunks = []
    for cat in cat_order:
        trows = table_rows_by_cat.get(cat)
        if not trows:
            continue
        chunks.append("### %s" % cat)
        chunks.append("")
        chunks.append(md_row(HEADERS, cellw))
        chunks.append(sep)
        for row in trows:
            chunks.append(md_row(row, cellw))
        chunks.append("")

    return "\n".join(chunks).rstrip()


def main():
    repos = [r for r in api("/users/%s/repos?per_page=100&visibility=public" % OWNER) if not r["fork"]]
    repos = [r for r in repos if r["name"] != OWNER]

    released_names = set()
    for r in repos:
        if has_release(r["name"]):
            released_names.add(r["name"])

    preferred = ["🤖 AI, bots & agents", "🎮 Games", "⌚ Devices & hardware", "📈 Markets & finance", "🌍 EU & transparency"]
    cat_order = [c for c in preferred if c in set(CATEGORIZED.values())]
    for c in dict.fromkeys(CATEGORIZED.values()):
        if c not in cat_order:
            cat_order.append(c)
    for c in set(CATEGORIZED.values()):
        if c not in cat_order:
            cat_order.append(c)
    if OTHER not in cat_order:
        cat_order.append(OTHER)

    groups = {c: [] for c in cat_order}
    for r in repos:
        groups[CATEGORIZED.get(r["name"], OTHER)].append(r)
    for c in groups:
        groups[c].sort(key=lambda r: (not r["name"] in released_names, r["name"].lower()))

    n_released = n_alpha = n_prealpha = n_dev = 0
    for r in repos:
        ov = STATUS_OVERRIDES.get(r["name"])
        if ov:
            if "pre-alpha" in ov:
                n_prealpha += 1
            elif "alpha" in ov:
                n_alpha += 1
            else:
                n_dev += 1
        elif r["name"] in released_names:
            n_released += 1
        else:
            n_dev += 1
    parts = [f"**{len(repos)} public repos**", f"**{n_released} released**"]
    if n_alpha:
        parts.append(f"**{n_alpha} alpha**")
    if n_prealpha:
        parts.append(f"**{n_prealpha} pre-alpha**")
    parts.append(f"**{n_dev} in development**")
    status = " · ".join(parts)

    tables = render_tables(groups, cat_order, released_names)

    with open("README.md") as f:
        readme = f.read()

    readme = replace_section(readme, START_STATUS, END_STATUS, status)
    readme = replace_section(readme, START_REPOS, END_REPOS, tables)

    with open("README.md", "w") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
