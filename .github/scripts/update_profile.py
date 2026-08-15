#!/usr/bin/env python3
"""Regenerate the profile README sections:
  - pinned repository cards (top of README, GitHub-style)
  - repo status list (all public non-fork repos of Gyerchak)
Both sections are replaced between HTML comment markers in README.md."""

import json
import os
import re
import urllib.request
import urllib.error

OWNER = "Gyerchak"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"

START_PINS = "<!-- PINS:START -->"
END_PINS = "<!-- PINS:END -->"
START_STATUS = "<!-- STATUS:START -->"
END_STATUS = "<!-- STATUS:END -->"
START_REPOS = "<!-- REPOS:START -->"
END_REPOS = "<!-- REPOS:END -->"

PINS_QUERY = """
query($login: String!) {
  user(login: $login) {
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes {
        ... on Repository {
          name
          description
          visibility
          primaryLanguage { name color }
          stargazerCount
          forkCount
        }
      }
    }
  }
}
"""


def api(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + TOKEN,
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def graphql(query, variables):
    req = urllib.request.Request(
        API + "/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json",
            "User-Agent": "Gyerchak-profile",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"]))
    return data


def esc(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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


def build_pins():
    data = graphql(PINS_QUERY, {"login": OWNER})
    nodes = data["data"]["user"]["pinnedItems"]["nodes"]
    cells = []
    for repo in nodes:
        if repo is None:
            continue
        name = repo["name"]
        vis = repo.get("visibility", "public")
        lang = repo.get("primaryLanguage") or {}
        lang_name = lang.get("name") or ""
        lang_color = lang.get("color") or "#8b949e"
        desc = esc(repo.get("description") or "").strip() or "&nbsp;"
        meta = ""
        if lang_name:
            meta += '<span style="color:%s">&#11044;</span> %s' % (lang_color, esc(lang_name))
        meta += ' &nbsp; &#11088; %d &nbsp; &#127860; %d' % (
            repo.get("stargazerCount", 0),
            repo.get("forkCount", 0),
        )
        cell = (
            '<td width="330" align="left" valign="top" '
            'style="border:1px solid var(--color-border-default); border-radius:6px; padding:10px 14px;">'
            '<a href="https://github.com/%s/%s"><b>%s</b></a>'
            ' <sub style="color:var(--color-fg-muted)">%s</sub><br/>'
            '<span style="color:var(--color-fg-muted); font-size:13px;">%s</span><br/>'
            '<span style="color:var(--color-fg-muted); font-size:12px;">%s</span>'
            "</td>"
        ) % (OWNER, name, name, vis.title(), desc, meta)
        cells.append(cell)
    rows = []
    per_row = 3
    for i in range(0, len(cells), per_row):
        chunk = cells[i:i + per_row]
        while len(chunk) < per_row:
            chunk.append('<td width="330"></td>')
        rows.append("<tr>" + "".join(chunk) + "</tr>")
    if not rows:
        return "_(no pinned repositories)_"
    return '<div align="center">\n<table>\n' + "\n".join(rows) + "\n</table>\n</div>"


def main():
    repos = [r for r in api("/users/%s/repos?per_page=100&visibility=public" % OWNER) if not r["fork"]]
    repos = [r for r in repos if r["name"] != OWNER]
    repos.sort(key=lambda r: (not has_release(r["name"]), r["name"].lower()))

    released_names = set()
    for r in repos:
        if has_release(r["name"]):
            released_names.add(r["name"])

    status = (
        "**%d public repos** · "
        "**%d released** · "
        "**%d in development**"
    ) % (len(repos), len(released_names), len(repos) - len(released_names))

    lines = [
        "| Repo | Status | Description | Language | Stars |",
        "|------|--------|-------------|----------|-------|",
    ]
    for r in repos:
        name = r["name"]
        if name in released_names:
            rel = api("/repos/%s/%s/releases/latest" % (OWNER, name))
            tag = rel.get("tag_name", "released")
            status_cell = "✅ `%s`" % tag
        else:
            status_cell = "🚧 in development"
        desc = (r.get("description") or "").replace("|", "/")
        lang = r.get("language") or "—"
        stars = r.get("stargazers_count", 0)
        lines.append(
            "| [%s](https://github.com/%s/%s) | %s | %s | %s | ⭐ %s |"
            % (name, OWNER, name, status_cell, desc, lang, stars)
        )

    with open("README.md") as f:
        readme = f.read()

    readme = replace_section(readme, START_PINS, END_PINS, build_pins())
    readme = replace_section(readme, START_STATUS, END_STATUS, status)
    readme = replace_section(readme, START_REPOS, END_REPOS, "\n".join(lines))

    with open("README.md", "w") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
