#!/usr/bin/env python3
"""Regenerate the profile README repo status list (all public non-fork repos
of Gyerchak). The section is replaced between HTML comment markers in README.md."""

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
        "| Repo | Status | Description | Language | License | Stars |",
        "|------|--------|-------------|----------|---------|-------|",
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
        lic = (r.get("license") or {}).get("spdx_id") or "—"
        stars = r.get("stargazers_count", 0)
        lines.append(
            "| [%s](https://github.com/%s/%s) | %s | %s | %s | %s | ⭐ %s |"
            % (name, OWNER, name, status_cell, desc, lang, lic, stars)
        )

    with open("README.md") as f:
        readme = f.read()

    readme = replace_section(readme, START_STATUS, END_STATUS, status)
    readme = replace_section(readme, START_REPOS, END_REPOS, "\n".join(lines))

    with open("README.md", "w") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
