"""
Cost of one decision of version 1 (naive moves, living-lines evaluation,
Minimax) at depths 1, 2 and 3.
Run from the engine folder with:   python measure_v1.py
Position: Black JJ, White KJ and JK, Black to move (the one in the report).
Depth 3 takes around 40 seconds, so be patient.
The numbers go into the "Choice of depth" table of version 1 in the report.
"""
import platform
import time

import search
import moves
import evaluation
from board import Board, BLACK, WHITE

print("Python", platform.python_version(), "on", platform.platform())
print("Processor:", platform.processor() or "unknown")
print()

board = Board()
board.place(BLACK, [(9, 9)])
board.place(WHITE, [(10, 9), (9, 10)])

# Version 1 settings, fixed here so the script does not depend on the
# defaults of search.py.
search.GENERATOR = moves.candidate_moves
search.EVALUATE = evaluation.evaluate
search.ALGORITHM = "minimax"
search.TIME_LIMIT = None   # fixed depth: exact node counts for the report

for depth in (1, 2, 3):
    search.DEPTH = depth
    start = time.perf_counter()
    move = search.best_move(board, BLACK)
    elapsed = time.perf_counter() - start
    print(f"depth {depth}: {search.nodes:>7} nodes, {elapsed:6.2f} s, move {move}")
