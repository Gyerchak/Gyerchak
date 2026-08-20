#!/usr/bin/env python3
"""Regenerate the profile README repo status list (all public non-fork repos
of Gyerchak), grouped by category. The section is replaced between HTML
comment markers in README.md."""

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

# Each repo -> (emoji label-ish node, category title). Repos not listed here
# fall into a final "Everything else" group. Order matters: CATEGORY_ORDER
# sets the display order; unknown repos go last.
CATEGORIZED = {
    # ── Games
    "Minkraft": "🎮 Games",
    "Moba": "🎮 Games",
    "Globe-Game": "🎮 Games",
    "GameTemplate": "🎮 Games",
    "OpenCode-OpenGLMiniGames": "🎮 Games",
    # ── Devices & hardware
    "XiaomiWatchApp": "⌚ Devices & hardware",
    "XiaomiWatchLinuxConnect": "⌚ Devices & hardware",
    "LinuxXiaomiWatchApp": "⌚ Devices & hardware",
    "HeadControll": "⌚ Devices & hardware",
    # ── Markets & finance
    "StockAnalyzer": "📈 Markets & finance",
    "DemandPolandEu": "📈 Markets & finance",
    "DenSupply": "📈 Markets & finance",
    "MAAW-Supply": "📈 Markets & finance",
    # ── AI, bots & agents
    "OpenCode-DiscordBot": "🤖 AI, bots & agents",
    "Remote-OpenCode-DiscordBot": "🤖 AI, bots & agents",
    "OpenCodeAndroidChat": "🤖 AI, bots & agents",
    "OpenCodeLiveTranslator": "🤖 AI, bots & agents",
    "AiBotniak": "🤖 AI, bots & agents",
    "HistorAI": "🤖 AI, bots & agents",
    "ShrimpFarmer-Agent": "🤖 AI, bots & agents",
    "MAAW-Bot": "🤖 AI, bots & agents",
    # ── EU & transparency
    "EuTransparencyChecker": "🌍 EU & transparency",
    "NiceEuTransparency": "🌍 EU & transparency",
    "CopyRightsChecker": "🌍 EU & transparency",
    "EuDemand": "🌍 EU & transparency",
}

OTHER = "🗂️ Everything else"


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


def repo_row(r, released_names):
    name = r["name"]
    if name in released_names:
        tag = api("/repos/%s/%s/releases/latest" % (OWNER, name)).get("tag_name", "released")
        status_cell = "✅ `%s`" % tag
    else:
        status_cell = "🚧 in development"
    desc = (r.get("description") or "").replace("|", "/")
    lang = r.get("language") or "—"
    lic = (r.get("license") or {}).get("spdx_id") or "—"
    stars = r.get("stargazers_count", 0)
    return (
        "| [%s](https://github.com/%s/%s) | %s | %s | %s | %s | ⭐ %s |"
        % (name, OWNER, name, status_cell, desc, lang, lic, stars)
    )


def main():
    repos = [r for r in api("/users/%s/repos?per_page=100&visibility=public" % OWNER) if not r["fork"]]
    repos = [r for r in repos if r["name"] != OWNER]

    released_names = set()
    for r in repos:
        if has_release(r["name"]):
            released_names.add(r["name"])

    # order categories logically; unknown → Other
    seen = {c for c in CATEGORIZED.values()}
    cat_order = [c for c in dict.fromkeys(CATEGORIZED.values())]
    for c in seen:
        if c not in cat_order:
            cat_order.append(c)
    if OTHER not in cat_order:
        cat_order.append(OTHER)

    # stable order within each cat: released first, then by name
    groups = {c: [] for c in cat_order}
    for r in repos:
        cat = CATEGORIZED.get(r["name"], OTHER)
        groups[cat].append(r)
    for c in groups:
        groups[c].sort(key=lambda r: (not r["name"] in released_names, r["name"].lower()))

    status = (
        "**%d public repos** · "
        "**%d released** · "
        "**%d in development**"
    ) % (len(repos), len(released_names), len(repos) - len(released_names))

    lines = []
    for cat in cat_order:
        g = groups[cat]
        if not g:
            continue
        lines.append("### %s" % cat)
        lines.append("")
        lines.append("| Repo | Status | Description | Language | License | Stars |")
        lines.append("|------|--------|-------------|----------|---------|-------|")
        for r in g:
            lines.append(repo_row(r, released_names))
        lines.append("")

    with open("README.md") as f:
        readme = f.read()

    readme = replace_section(readme, START_STATUS, END_STATUS, status)
    readme = replace_section(readme, START_REPOS, END_REPOS, "\n".join(lines).rstrip())

    with open("README.md", "w") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
