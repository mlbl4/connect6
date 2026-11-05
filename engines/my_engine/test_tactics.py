"""
Tactical tests of the whole engine (moves.py + search.py + evaluation.py).
Run from the engine folder with:

    python test_tactics.py          (the current version, set in search.py)
    python test_tactics.py v2       (any version defined in match.py)
    python test_tactics.py v5 4     (version 5 with the time of level 4)

Versions 1 to 4 are tested at their fixed depth. Version 5 gets the time
limit that the GUI would send (level 6 = High = 6 seconds by default, or the
level given), and searches as deep as that time allows.

Unlike test_evaluation.py, these tests do not check a number: they give the
engine a position and check whether the MOVE it chooses is the right one.
They are the test positions of the practice (forced wins and defences in
1, 2 and 3 turns), also used in the Experimentation section.

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
  5. Forced win in 3 turns: Black has an open three and two pairs that
     cross at one empty cell. No single move gives 3 threats (checked by
     the test), so Black cannot win in 2 turns. The winning sequence is:
     turn 1, an open four (White must spend both stones blocking it) plus
     the crossing stone, which makes two new open threes; turn 2, both
     threes become open fours (4 threats); turn 3, six. The game is played
     out against a fixed opponent (version 4, depth 3); passed if Black
     makes six within its 3 turns.
  6. Defence against a threat in 3 turns: the same position with the
     colours swapped. Passed if White (the same fixed opponent) has not
     made six after its 3 turns.

With version 1 (naive generator) tests 1 and 2 fail: the cells at the ends
of a line have few neighbouring stones, so they are never candidates.
"""

import sys
import time
from itertools import combinations

import search
import match
from board import Board, BLACK, WHITE, EMPTY
from evaluation import count_threats
from moves import neighbours

if len(sys.argv) > 1:
    from match import use
    use(sys.argv[1])
LEVEL = int(sys.argv[2]) if len(sys.argv) > 2 else 6
if search.ALGORITHM != "optimised":
    search.TIME_LIMIT = None   # fixed depth: exact node counts for the report
else:
    # Version 5 gets the time the GUI gives it: 'depth LEVEL' (High = 6 s),
    # of which it uses 80%, and searches as deep as that time allows.
    search.set_time_limit(LEVEL)


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
    return move, (f"played {move}, {elapsed:.2f} s, {search.nodes} nodes, "
                  f"{search.pruned} pruned, depth {search.depth_reached}")


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

# ---------------------------------------------------------------------------
# 5. Forced win in 3 turns: open three on row O (C, D, E), a pair on column M
#    (rows C, D) and a pair on row E (columns K, L). The pairs cross at the
#    empty cell ME (12, 4).
# ---------------------------------------------------------------------------
SHAPES = [(2, 14), (3, 14), (4, 14), (12, 2), (12, 3), (10, 4), (11, 4)]
SETTINGS = ["GENERATOR", "EVALUATE", "ALGORITHM", "DEPTH", "TIME_LIMIT"]
TESTED = {name: getattr(search, name) for name in SETTINGS}


def opponent_move(b, color):
    """Move of the fixed opponent: version 4 at depth 3 (no time limit)."""
    match.use("v4")
    search.TIME_LIMIT = None
    move = search.best_move(b, color)
    for name, value in TESTED.items():      # back to the tested version
        setattr(search, name, value)
    return move


def play_out(b, turns):
    """Black (tested version) and White (fixed opponent) play `turns` turns
    each. Returns (winner or None, Black's first move, its detail text)."""
    first = detail = None
    for _ in range(2 * turns):
        color = b.to_move
        if color == BLACK:
            move, text = think(b)
            if first is None:
                first, detail = move, text
        else:
            move = opponent_move(b, color)
        b.place(color, move)
        winner = b.check_winner(move)
        if winner is not None:
            return winner, first, detail
    return None, first, detail


b = position(SHAPES + [(16, 16)], FAR_8, BLACK)
cells = [c for c in b.empty_cells() if neighbours(b, *c) > 0]
best_one_move = 0
for pair in combinations(cells, 2):
    b.place(BLACK, list(pair))
    best_one_move = max(best_one_move, count_threats(b, BLACK))
    b.undo(list(pair))
winner, first, detail = play_out(b, 3)
show("forced win in 3 turns (Black makes six within 3 turns)",
     winner == BLACK and best_one_move < 3,
     detail + f", no move gives 3 threats (max {best_one_move})")

# ---------------------------------------------------------------------------
# 6. Defence against a threat in 3 turns: the same shapes, now White's.
# ---------------------------------------------------------------------------
b = position(FAR_8[:7] + [(16, 16), (16, 2)], SHAPES + FAR_8[7:], BLACK)
winner, first, detail = play_out(b, 3)
show("defence against a threat in 3 turns (White has not won after 3 turns)",
     winner != WHITE, detail)
