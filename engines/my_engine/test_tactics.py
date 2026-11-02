"""
Tactical tests of the whole engine (moves.py + search.py + evaluation.py).
Run from the engine folder with:

    python test_tactics.py

Unlike test_evaluation.py, these tests do not check a number: they give the
engine a position and check whether the MOVE it chooses is the right one.

With version 1 (naive move generation) both tests are EXPECTED TO FAIL:
the cells at the ends of a line have few neighbouring stones, so the naive
generator never puts them among its 10 candidates, and Minimax never gets to
consider them. They should pass once the threat-based generator exists.
They are also test positions for the Experimentation section.
"""

import time

import search
from board import Board, BLACK, WHITE
from moves import candidate_moves
search.TIME_LIMIT = None   # fixed depth: exact node counts for the report


def show(name, ok, detail):
    print(f"{'PASS' if ok else 'FAIL'} {name}")
    print(f"     {detail}")


# ---------------------------------------------------------------------------
# 1. Win in one: Black has five in a row on row J (columns G..K) and plays.
#    Completing six at F J or L J wins immediately.
# ---------------------------------------------------------------------------
b = Board()
b.place(BLACK, [(9, 9)])
b.place(WHITE, [(3, 3), (15, 15)])
b.place(BLACK, [(6, 9), (7, 9)])
b.place(WHITE, [(3, 15), (15, 3)])
b.place(BLACK, [(8, 9), (10, 9)])
b.place(WHITE, [(0, 0), (18, 18)])

t = time.perf_counter()
move = search.best_move(b, BLACK)
elapsed = time.perf_counter() - t
b.place(BLACK, move)
won = b.check_winner(move) == BLACK
show("win in one (Black completes six)", won,
     f"played {move}, {elapsed:.2f} s, {search.nodes} nodes")

# ---------------------------------------------------------------------------
# 2. Forced defence: White has four in a row on row E (columns G..J) with
#    both ends open. Black must block, or White makes six next turn.
# ---------------------------------------------------------------------------
b = Board()
b.place(BLACK, [(9, 9)])
b.place(WHITE, [(6, 4), (7, 4)])
b.place(BLACK, [(9, 10), (2, 15)])
b.place(WHITE, [(8, 4), (9, 4)])

t = time.perf_counter()
move = search.best_move(b, BLACK)
elapsed = time.perf_counter() - t
b.place(BLACK, move)

# After Black's move, can White still make six anywhere on row E?
white_can_win = False
for x in range(19):
    for x2 in range(x + 1, 19):
        reply = [(x, 4), (x2, 4)]
        if all(b.grid[y][xx] == 0 for xx, y in reply):
            b.place(WHITE, reply)
            if b.check_winner(reply) == WHITE:
                white_can_win = True
            b.undo(reply)
show("forced defence (Black blocks an open four)", not white_can_win,
     f"played {move}, {elapsed:.2f} s, {search.nodes} nodes")