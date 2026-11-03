"""
Static evaluation of a Connect6 position (naive version, session 1).

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


# ===========================================================================
# Weighted evaluation (version 2, session 2)
# ===========================================================================
#
# The naive evaluation counts every living line as 1, so a window with one
# stone is worth as much as a window with five, one move away from winning.
# Here each living line is weighted by the number of stones it already holds,
# and the weight grows geometrically: every extra stone in a window brings it
# one step closer to six, so it is worth several times more.
#
# WEIGHTS[k] is the value of a living line with k stones of one colour.
# The largest possible total (924 windows x 625) stays below WIN_SCORE, so a
# real win is always worth more than any estimate.
WEIGHTS = [0, 1, 5, 25, 125, 625]


def weighted_lines(board):
    """Sum of WEIGHTS[k] over the living lines of each colour.
    Returns (black_total, white_total)."""
    black = white = 0
    grid = board.grid
    for window in WINDOWS:
        b = w = 0
        for x, y in window:
            cell = grid[y][x]
            if cell == BLACK:
                b += 1
            elif cell == WHITE:
                w += 1
        if b and not w:
            black += WEIGHTS[b]
        elif w and not b:
            white += WEIGHTS[w]
    return black, white


def evaluate_weighted(board, last_stones=None):
    """Same structure as evaluate(): exact result if the game is over,
    otherwise Black's weighted living lines minus White's."""
    if last_stones:
        result = board.check_winner(last_stones)
        if result == BLACK:
            return WIN_SCORE
        if result == WHITE:
            return -WIN_SCORE
        if result == DRAW:
            return 0

    black, white = weighted_lines(board)
    return black - white


# ===========================================================================
# Own evaluation function (version 3, session 3)
# ===========================================================================
#
# Based on the state of the art:
#   - Wu and Huang (2006) define a THREAT: a player has t threats if the
#     opponent needs t stones to stop him from making six on his next move.
#     Since each player places two stones per turn, three threats win, and
#     whoever is to move and has at least one threat wins at once.
#     They count threats on each line with a sliding window of six cells:
#     a window with at least 4 stones of the player, no opponent stones and
#     no cell already marked is a threat; its empty cells are then marked so
#     that one blocking stone is never counted twice.
#   - Liu and Lin (2009) stress that open space matters: the same pattern is
#     worth more when it has more room around it. Counting the living windows
#     of each size measures this, because an open line belongs to more
#     windows than a blocked one.
#
# The evaluation is a weighted sum of these features (Black minus White).
# The weights are chosen by hand here; version 4 learns them.

def _all_lines():
    """Every line of the board (rows, columns and both diagonals) with at
    least 6 cells, as a list of (x, y) cells in order."""
    lines = []
    for y in range(EDGE):                                   # rows
        lines.append([(x, y) for x in range(EDGE)])
    for x in range(EDGE):                                   # columns
        lines.append([(x, y) for y in range(EDGE)])
    for d in range(-(EDGE - WIN_LENGTH), EDGE - WIN_LENGTH + 1):
        lines.append([(x, x - d) for x in range(EDGE)       # diagonals ↘
                      if 0 <= x - d < EDGE])
        lines.append([(x, EDGE - 1 - x + d) for x in range(EDGE)   # diagonals ↗
                      if 0 <= EDGE - 1 - x + d < EDGE])
    return lines


LINES = _all_lines()   # 92 lines: 19 rows, 19 columns, 2 x 27 diagonals

# The windows of each line, in order along the line, computed once.
LINE_WINDOWS = [[tuple(line[i:i + WIN_LENGTH])
                 for i in range(len(line) - WIN_LENGTH + 1)]
                for line in LINES]


# Weights of the features, chosen by hand (tuned in version 4).
#   W_LINES[k]: a living window with k stones (k = 1, 2, 3), as in version 2.
#   W_THREAT:   one threat. Each threat forces the opponent to spend a stone
#               on defence, so it is worth more than any shape that is not
#               yet a threat.
W_LINES = [0, 1, 5, 25]
W_THREAT = 500
NEAR_WIN = WIN_SCORE // 2   # a win that is certain on the next move


def features(board):
    """The features of the position, in a single pass over the board:
      lines:   living windows with 1, 2 and 3 stones, for Black and White;
      threats: threats of Black and of White, counted with Wu and Huang's
               sliding window: along each line, a window with at least 4
               stones of a player, none of the opponent's and no cell marked
               yet is one threat, and its empty cells are then marked so that
               a single blocking stone is never counted twice."""
    grid = board.grid
    lines_b = [0, 0, 0, 0]
    lines_w = [0, 0, 0, 0]
    threats_b = threats_w = 0
    for windows in LINE_WINDOWS:
        marked_b = set()
        marked_w = set()
        for window in windows:
            b = w = 0
            empty = []
            for x, y in window:
                cell = grid[y][x]
                if cell == BLACK:
                    b += 1
                elif cell == WHITE:
                    w += 1
                else:
                    empty.append((x, y))
            if b and not w:
                if b <= 3:
                    lines_b[b] += 1
                elif not marked_b.intersection(empty):
                    threats_b += 1
                    marked_b.update(empty)
            elif w and not b:
                if w <= 3:
                    lines_w[w] += 1
                elif not marked_w.intersection(empty):
                    threats_w += 1
                    marked_w.update(empty)
    return {"lines": (lines_b, lines_w), "threats": (threats_b, threats_w)}


def count_threats(board, player):
    """Number of threats of `player` (Wu and Huang's definition)."""
    tb, tw = features(board)["threats"]
    return tb if player == BLACK else tw


def evaluate_threats(board, last_stones=None):
    """Version 3 evaluation, from Black's point of view.
      1. Game over: exact result, as before.
      2. The player to move has a threat: he completes six now -> near win.
      3. The player who has just moved has 3 or more threats: the opponent
         cannot block them all with two stones -> near win for him.
      4. Otherwise: weighted sum of the features (Black minus White)."""
    if last_stones:
        result = board.check_winner(last_stones)
        if result == BLACK:
            return WIN_SCORE
        if result == WHITE:
            return -WIN_SCORE
        if result == DRAW:
            return 0

    f = features(board)
    tb, tw = f["threats"]
    mover = board.to_move
    sign = 1 if mover == BLACK else -1           # +1 if Black is to move
    mover_threats, waiting_threats = (tb, tw) if mover == BLACK else (tw, tb)
    if mover_threats >= 1:
        return sign * NEAR_WIN
    if waiting_threats >= 3:
        return -sign * NEAR_WIN

    lines_b, lines_w = f["lines"]
    score = W_THREAT * (tb - tw)
    for k in (1, 2, 3):
        score += W_LINES[k] * (lines_b[k] - lines_w[k])
    return score
