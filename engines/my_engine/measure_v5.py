"""
Measurements of the optimisations of version 5 (for the report).
Run with:   python measure_v5.py [seconds]      (default: 20 seconds)

Uses four positions taken from games (an opening near the centre and three
more random turns) and measures:

  1. Equivalence: version 5 with forward pruning and quiescence switched off,
     at depth 3, must choose the same move and expand the same nodes as
     version 4 (the transposition table and the move ordering do not change
     the result of Alpha-Beta).
  2. Forward pruning (N-best): version 5 at depth 3 with and without it.
  3. Quiescence search: the depth that version 5 completes within the time
     limit, without quiescence and with one extra turn of forced moves.
"""

import random
import sys
import time

import search
from compare import opening
from match import use

SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0


def positions():
    result = []
    for s in range(4):
        b = opening(200 + s)
        rng = random.Random(s)
        for _ in range(3):
            cells = [c for c in b.empty_cells()
                     if 5 <= c[0] <= 13 and 5 <= c[1] <= 13]
            b.place(b.to_move, rng.sample(cells, 2))
        result.append(b)
    return result


def run(version, **settings):
    use(version)
    search.N_BEST = 20
    search.QUIESCENCE_DEPTH = 0
    for name, value in settings.items():
        setattr(search, name, value)
    rows = []
    for b in positions():
        t = time.perf_counter()
        move = search.best_move(b, b.to_move)
        rows.append((sorted(move), time.perf_counter() - t, search.nodes,
                     search.depth_reached))
    return rows


def show(title, rows):
    print(title)
    for i, (move, seconds, nodes, depth) in enumerate(rows, 1):
        print(f"  position {i}: move {move}, {seconds:5.2f} s, "
              f"{nodes:6} nodes, depth {depth}")


if __name__ == "__main__":
    print("1. Equivalence at depth 3")
    show(" version 4", run("v4", TIME_LIMIT=None))
    show(" version 5 without N-best and quiescence",
         run("v5", TIME_LIMIT=None, DEPTH=3, N_BEST=1000))
    print("\n2. Forward pruning at depth 3")
    show(" version 5, N-best = 20", run("v5", TIME_LIMIT=None, DEPTH=3))
    print(f"\n3. Quiescence search, time limit {SECONDS:g} s")
    show(" without quiescence", run("v5", TIME_LIMIT=SECONDS))
    show(" with 1 turn of quiescence",
         run("v5", TIME_LIMIT=SECONDS, QUIESCENCE_DEPTH=1))
