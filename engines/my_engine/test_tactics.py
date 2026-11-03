"""
Tactical tests of the whole engine (moves.py + search.py + evaluation.py).
Run from the engine folder with:

    python test_tactics.py          (the current version, set in search.py)
    python test_tactics.py v2       (any version defined in match.py)

Unlike test_evaluation.py, these tests do not check a number: they give the
engine a position and check whether the MOVE it chooses is the right one.
They are the test positions of the practice (forced wins and defences in
1 and 2 turns), also used in the Experimentation section.

  1. Forced win in 1 turn: Black has five in a row and completes six.
  2. Defence against a threat in 1 turn: White has an open four
     (two threats) and Black must block both.
  3. Forced win in 2 turns: Black has two separate open threes. Turning
     both into open fours gives 4 threats; White can block only 2, so
     Black wins on the next turn. Passed if Black has 3+ threats after
     its move.
  4. Defence against a threat in 2 turns: the same position with the
     colours swapped. If Black does nothing, White makes 4 threats and
     wins. Passed if, after Black's move, no reply of White gives it
     3 or more threats.

With version 1 (naive generator) tests 1 and 2 fail: the cells at the ends
of a line have few neighbouring stones, so they are never candidates.
"""

import sys
import time
from itertools import combinations

import search
from board import Board, BLACK, WHITE, EMPTY
from evaluation import count_threats
from moves import neighbours

if len(sys.argv) > 1:
    from match import use
    use(sys.argv[1])
search.TIME_LIMIT = None   # fixed depth: exact node counts for the report


def show(name, ok, detail):
    print(f"{'PASS' if ok else 'FAIL'} {name}")
    print(f"     {detail}")


def position(black, white, to_move):
    """Board with these stones and this player to move."""
    b = Board()
    for x, y in black:
        b.grid[y][x] = BLACK
    for x, y in white:
        b.grid[y][x] = WHITE
    b.stones_played = len(black) + len(white)
    b.to_move = to_move
    return b


def think(b):
    """Ask the engine for Black's move; returns (move, detail text)."""
    t = time.perf_counter()
    move = search.best_move(b, BLACK)
    elapsed = time.perf_counter() - t
    return move, f"played {move}, {elapsed:.2f} s, {search.nodes} nodes"


# ---------------------------------------------------------------------------
# 1. Forced win in 1 turn: Black has five in a row on row J (columns G..K).
# ---------------------------------------------------------------------------
b = Board()
b.place(BLACK, [(9, 9)])
b.place(WHITE, [(3, 3), (15, 15)])
b.place(BLACK, [(6, 9), (7, 9)])
b.place(WHITE, [(3, 15), (15, 3)])
b.place(BLACK, [(8, 9), (10, 9)])
b.place(WHITE, [(0, 0), (18, 18)])
move, detail = think(b)
b.place(BLACK, move)
show("forced win in 1 turn (Black completes six)",
     b.check_winner(move) == BLACK, detail)

# ---------------------------------------------------------------------------
# 2. Defence against a threat in 1 turn: White has an open four on row E
#    (columns G..J). Black must block, or White makes six next turn.
# ---------------------------------------------------------------------------
b = Board()
b.place(BLACK, [(9, 9)])
b.place(WHITE, [(6, 4), (7, 4)])
b.place(BLACK, [(9, 10), (2, 15)])
b.place(WHITE, [(8, 4), (9, 4)])
move, detail = think(b)
b.place(BLACK, move)
white_can_win = False
for x in range(19):
    for x2 in range(x + 1, 19):
        reply = [(x, 4), (x2, 4)]
        if all(b.grid[y][xx] == EMPTY for xx, y in reply):
            b.place(WHITE, reply)
            if b.check_winner(reply) == WHITE:
                white_can_win = True
            b.undo(reply)
show("defence against a threat in 1 turn (Black blocks an open four)",
     not white_can_win, detail)

# ---------------------------------------------------------------------------
# 3. Forced win in 2 turns: open threes on row J (G, H, I) and on
#    column O (rows D, E, F); the other stones are far away.
# ---------------------------------------------------------------------------
THREES = [(6, 9), (7, 9), (8, 9), (14, 3), (14, 4), (14, 5)]
FAR_8 = [(0, 0), (18, 0), (0, 18), (18, 18), (18, 9), (0, 9), (9, 0), (9, 18)]
FAR_7 = [(3, 15)] + FAR_8[:6]

b = position(THREES + [(3, 15)], FAR_8, BLACK)
move, detail = think(b)
b.place(BLACK, move)
show("forced win in 2 turns (Black makes 3+ threats)",
     count_threats(b, BLACK) >= 3,
     detail + f", {count_threats(b, BLACK)} threats")

# ---------------------------------------------------------------------------
# 4. Defence against a threat in 2 turns: the same open threes, now White's.
# ---------------------------------------------------------------------------
b = position(FAR_7, THREES + FAR_8[6:], BLACK)
move, detail = think(b)
b.place(BLACK, move)
# Every reply of White near its stones: can it reach 3 or more threats?
cells = [c for c in b.empty_cells() if neighbours(b, *c) > 0]
worst = 0
for reply in combinations(cells, 2):
    b.place(WHITE, list(reply))
    worst = max(worst, count_threats(b, WHITE))
    b.undo(list(reply))
show("defence against a threat in 2 turns (White cannot reach 3 threats)",
     worst < 3, detail + f", White's best reply: {worst} threats")
