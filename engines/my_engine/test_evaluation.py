"""
Tests for evaluation.py. Run from the engine folder with:

    python test_evaluation.py

Each test builds a board, calls evaluate() and compares the result with the
value we expect. If everything is correct it prints "OK" for every test.
If something is wrong it stops and shows which test failed and why.
"""

from board import Board, BLACK, WHITE
from evaluation import evaluate, living_lines, WINDOWS, WIN_SCORE


def check(name, got, expected):
    """Print the result of one test and stop if it is wrong."""
    status = "OK  " if got == expected else "FAIL"
    print(f"{status} {name}: got {got}, expected {expected}")
    assert got == expected, name


# 0. The board has 924 windows of six cells.
#    Horizontal: 19 rows x 14 windows per row = 266
#    Vertical:   19 columns x 14             = 266
#    Each diagonal direction: 14 x 14        = 196 (x2)
check("number of windows", len(WINDOWS), 266 + 266 + 196 + 196)

# 1. Empty board: no stones, so no living lines for anybody.
b = Board()
check("empty board", evaluate(b), 0)

# 2. One black stone in the centre (9, 9) = JJ.
#    In each direction, 6 different windows contain the centre
#    (the stone can be in position 1, 2, 3, 4, 5 or 6 of the window).
#    4 directions x 6 = 24 windows, all with only black -> +24.
b = Board()
b.place(BLACK, [(9, 9)])
check("black stone in the centre", evaluate(b, [(9, 9)]), 24)

# 3. One black stone in the corner (0, 0) = AA.
#    Only one window per direction starts there and fits on the board:
#    horizontal, vertical and diagonal down-right. The diagonal up-right
#    would leave the board. 3 windows -> +3.
b = Board()
b.place(BLACK, [(0, 0)])
check("black stone in the corner", evaluate(b, [(0, 0)]), 3)

# 4. Symmetry: one WHITE stone in the centre must give exactly -24.
b = Board()
b.place(WHITE, [(9, 9)])
check("white stone in the centre", evaluate(b, [(9, 9)]), -24)

# 5. Black in the centre, White answers at KJ (10, 9) and JK (9, 10).
#    Black keeps 14 living lines, White gets 33 -> 14 - 33 = -19.
b = Board()
b.place(BLACK, [(9, 9)])
b.place(WHITE, [(10, 9), (9, 10)])
check("living lines after White's reply", living_lines(b), (14, 33))
check("evaluation after White's reply", evaluate(b, [(10, 9), (9, 10)]), -19)

# 6. Black completes six in a row (row 5, columns 0 to 5) -> +WIN_SCORE.
b = Board()
b.place(BLACK, [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5)])
b.place(WHITE, [(0, 0), (1, 1)])
b.place(BLACK, [(5, 5), (10, 10)])        # (5, 5) completes the six
check("black makes six", evaluate(b, [(5, 5), (10, 10)]), WIN_SCORE)

# 7. White completes six in a column -> -WIN_SCORE.
b = Board()
b.place(WHITE, [(3, y) for y in range(6)])
check("white makes six", evaluate(b, [(3, 5)]), -WIN_SCORE)

# 8. Full board with no six in a row -> draw -> 0.
#    The pattern below alternates colours so that no line ever reaches six.
b = Board()
for y in range(19):
    for x in range(19):
        b.grid[y][x] = BLACK if ((x + 2 * y) // 2) % 2 == 0 else WHITE
b.stones_played = 19 * 19
check("full board, nobody wins (draw)", evaluate(b, [(18, 18)]), 0)

print("\nAll tests passed.")
