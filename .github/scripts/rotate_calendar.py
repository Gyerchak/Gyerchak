#!/usr/bin/env python3
"""Rotate the isometric contribution calendar 45 degrees to the left.

Runs after lowlighter/metrics generates the SVG (and before the dark variant
is derived from it), so both light and dark cards get the rotated graph.
The calendar group is rotated counter-clockwise around its center and
re-centered so the whole diamond fits inside the 480x270 viewBox at full size.
"""

import sys

ORIGINAL = '<g transform="scale(4) translate(12, 0)">'
ROTATED = '<g transform="scale(4) translate(12, 0) translate(9, 1.25) rotate(45 39 29)">'


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
