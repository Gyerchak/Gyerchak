#!/usr/bin/env python3
"""Rotate the isometric contribution calendar 90 degrees clockwise.

Runs after lowlighter/metrics generates the SVG (and before the dark variant
is derived from it), so both light and dark cards get the rotated graph.
The calendar group is rotated around its center and scaled down so the
whole calendar fits inside the 480x270 viewBox.
"""

import sys

ORIGINAL = '<g transform="scale(4) translate(12, 0)">'
ROTATED = '<g transform="scale(4) translate(12, 0) translate(23.82, 15.77) scale(0.62) rotate(90 39 29)">'


def main() -> None:
    path = sys.argv[1]
    src = open(path, encoding="utf-8").read()
    if ORIGINAL not in src:
        raise SystemExit(f"isocalendar group not found in {path}")
    out = src.replace(ORIGINAL, ROTATED)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(out)


if __name__ == "__main__":
    main()
