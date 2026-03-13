#!/usr/bin/env python3
"""Print a coverage summary from coverage.json for use in git commit messages."""
import json
import sys
from pathlib import Path

data = json.loads((Path(__file__).parent / "coverage.json").read_text())
totals = data["totals"]
files = data["files"]

print(f"test coverage: {totals['percent_covered_display']}% ({totals['covered_lines']}/{totals['num_statements']} lines)")
print()
for path, info in sorted(files.items()):
    if path.startswith("tests/"):
        continue
    pct = info["summary"]["percent_covered_display"]
    print(f"  {path:<30} {pct}%")
