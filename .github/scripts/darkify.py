#!/usr/bin/env python3
"""Convert a light-themed metrics SVG into a dark-themed variant.

The lowlighter/metrics action bakes GitHub light-theme colors into its SVG
output, and it has no working option to emit a genuinely dark variant
(``config_colors`` is not a real input).  This script remaps the known light
palette to the GitHub dark palette so the profile README can serve a proper
dark-mode card.
"""

import sys

PALETTE = {
    # Contribution calendar (GitHub light -> dark)
    "#ebedf0": "#161b22",  # empty cell background
    "#9be9a8": "#0e4429",  # L1
    "#40c463": "#006d32",  # L2
    "#30a14e": "#26a641",  # L3
    "#216e39": "#39d353",  # L4
    # Text / headers
    "#0366d6": "#58a6ff",
    "#777777": "#8b949e",
    "#777": "#8b949e",
    # Icons / muted elements
    "#959da5": "#8b949e",
    "#cb2431": "#f85149",
    "#D79533": "#d29922",
    "#EB355E": "#f85149",
    # Calendar cell outlines
    "rgba(27,31,35,0.06)": "rgba(240,246,252,0.06)",
    "rgba(27,31,35,.06)": "rgba(240,246,252,0.06)",
    "rgba(27,31,35,.04)": "rgba(240,246,252,0.04)",
    "rgba(27,31,35,0.04)": "rgba(240,246,252,0.04)",
}


def main() -> None:
    src = open(sys.argv[1], encoding="utf-8").read()
    out = src
    for light, dark in PALETTE.items():
        out = out.replace(light, dark)
    with open(sys.argv[2], "w", encoding="utf-8") as handle:
        handle.write(out)


if __name__ == "__main__":
    main()
