"""
Battery of test positions for every version (experiments of session 5).
Run from the engine folder with:

    python experiments.py              (versions v1 to v5, level 6)
    python experiments.py v3 v5        (only some versions)
    python experiments.py --level 4    (time of version 5: level 4 = 4 s)

Runs test_tactics.py with each version and collects, for every position
(forced wins and defences in 1, 2 and 3 turns), whether the version passed,
and the decision time, expanded nodes, pruned nodes and depth of its (first)
move. Prints a table and saves it to experiments.csv.

Versions 1 to 4 search at their fixed depth; version 5 gets the time limit
that the GUI sends with each AI level (Low = 4, Medium = 5, High = 6 seconds)
and searches as deep as that time allows.
"""

import csv
import re
import subprocess
import sys

args = sys.argv[1:]
LEVEL = "6"
if "--level" in args:
    i = args.index("--level")
    LEVEL = args[i + 1]
    del args[i:i + 2]
VERSIONS = args or ["v1", "v2", "v3", "v4", "v5"]
DETAIL = re.compile(r"([\d.]+) s, (\d+) nodes, (\d+) pruned, depth (\d+)")

rows = []
for version in VERSIONS:
    print(f"Running the positions with {version}...", flush=True)
    out = subprocess.run([sys.executable, "test_tactics.py", version, LEVEL],
                         capture_output=True, text=True).stdout.splitlines()
    for result, detail in zip(out[0::2], out[1::2]):
        status, name = result.split(" ", 1)
        test = name.split(" (")[0]
        found = DETAIL.search(detail)
        seconds, nodes, pruned, depth = found.groups() if found else ("", "", "", "")
        rows.append([version, test, status, seconds, nodes, pruned, depth])

with open("experiments.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["version", "position", "result", "seconds", "nodes",
                     "pruned", "depth"])
    writer.writerows(rows)

print()
print(f"{'version':8}{'position':42}{'result':8}{'time':>8}{'nodes':>9}"
      f"{'pruned':>9}{'depth':>7}")
for version, test, status, seconds, nodes, pruned, depth in rows:
    print(f"{version:8}{test:42}{status:8}{seconds:>8}{nodes:>9}"
          f"{pruned:>9}{depth:>7}")
print("\nSaved to experiments.csv")
