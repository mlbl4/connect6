"""
Cost of one decision of version 2 with Minimax and with Alpha-Beta.
Run from the engine folder with:   python measure_v2.py
Same position as measure_depth.py (Black JJ, White KJ and JK, Black to move).
Takes about 2 minutes (Minimax at depth 3 and Alpha-Beta at depth 4 are slow).
The numbers go into the "Choice of depth" table of version 2 in the report.
"""
import platform
import time

import search
import moves
import evaluation
from board import Board, BLACK, WHITE

print("Python", platform.python_version(), "on", platform.platform())
print()

board = Board()
board.place(BLACK, [(9, 9)])
board.place(WHITE, [(10, 9), (9, 10)])

search.GENERATOR = moves.threat_moves
search.EVALUATE = evaluation.evaluate_weighted
search.TIME_LIMIT = None   # fixed depth: exact node counts for the report

for depth in (1, 2, 3, 4):
    for algorithm in ("minimax", "alphabeta"):
        if algorithm == "minimax" and depth == 4:
            continue                      # far too slow
        search.DEPTH = depth
        search.ALGORITHM = algorithm
        start = time.perf_counter()
        move = search.best_move(board, BLACK)
        elapsed = time.perf_counter() - start
        print(f"depth {depth} {algorithm:9}: {search.nodes:>7} nodes, "
              f"{search.pruned:>7} pruned, {elapsed:6.2f} s, move {move}")
