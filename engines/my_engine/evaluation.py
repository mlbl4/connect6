"""
Static evaluation of a Connect6 position.

Gives ONE number for ONE board, without looking ahead:
  - positive  -> the position looks better for Black
  - negative  -> the position looks better for White
  - 0         -> balanced (or a draw)

Search (minimax) calls this function on the boards where it stops looking
ahead (the leaves of the tree), to compare them.
"""

from board import EDGE, EMPTY, BLACK, WHITE, DRAW, WIN_LENGTH, DIRECTIONS, in_bounds

# Score of a finished game. Much larger than any possible count of living
# lines (there are only 924 windows), so a win always beats any estimate.
WIN_SCORE = 1_000_000


def _all_windows():
    """Every window of 6 consecutive cells on the board, in the 4 directions.
    Each window is a tuple of 6 (x, y) positions.
    Computed once when the module is loaded, because the windows never change:
    only the stones inside them do."""
    windows = []
    for y in range(EDGE):
        for x in range(EDGE):
            for dx, dy in DIRECTIONS:
                # The window starts at (x, y) and goes 5 more steps in (dx, dy).
                end_x = x + dx * (WIN_LENGTH - 1)
                end_y = y + dy * (WIN_LENGTH - 1)
                if in_bounds(end_x, end_y):
                    windows.append(tuple((x + i * dx, y + i * dy)
                                         for i in range(WIN_LENGTH)))
    return windows


WINDOWS = _all_windows()   # 924 windows on a 19x19 board


def living_lines(board):
    """Count the living lines of each colour.
    A living line is a window that contains stones of only one colour
    (plus empty cells): that player could still complete six there.
    A window with both colours is dead (nobody can win in it) and an
    empty window belongs to nobody, so neither is counted.
    Returns (black_count, white_count)."""
    black = white = 0
    grid = board.grid
    for window in WINDOWS:
        has_black = has_white = False
        for x, y in window:
            cell = grid[y][x]
            if cell == BLACK:
                has_black = True
            elif cell == WHITE:
                has_white = True
        if has_black and not has_white:
            black += 1
        elif has_white and not has_black:
            white += 1
    return black, white


def evaluate(board, last_stones=None):
    """Score the board from Black's point of view.
    `last_stones` are the stones of the last move played; they are used to
    detect the end of the game with board.check_winner(), which only needs
    to look at those stones.
      1. Game over: +WIN_SCORE if Black won, -WIN_SCORE if White won, 0 if draw.
      2. Otherwise: living lines of Black minus living lines of White."""
    if last_stones:
        result = board.check_winner(last_stones)
        if result == BLACK:
            return WIN_SCORE
        if result == WHITE:
            return -WIN_SCORE
        if result == DRAW:
            return 0

    black, white = living_lines(board)
    return black - white
