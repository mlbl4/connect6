"""
Candidate move generation for Connect6 (naive version, session 1).

Each turn a player places 2 stones, so considering every empty spot gives
about 361 * 360 / 2 = 65,000 moves per turn, far too many for a search tree.
This naive version limits the candidates in two ways:
  1. Only empty spots near existing stones (within RADIUS).
  2. At most MAX_CELLS of those spots, preferring the most crowded ones.
The chosen spots are then combined into pairs without repetition.
"""

from itertools import combinations

from board import EDGE, EMPTY, in_bounds

RADIUS = 2       # how far from an existing stone a candidate spot can be
MAX_CELLS = 10   # max candidate spots -> at most 10 * 9 / 2 = 45 pairs
CENTRE = (EDGE // 2, EDGE // 2)   # (9, 9) = 'JJ'


def neighbours(board, x, y):
    """Number of stones (any colour) within RADIUS of (x, y)."""
    count = 0
    for dy in range(-RADIUS, RADIUS + 1):
        for dx in range(-RADIUS, RADIUS + 1):
            nx, ny = x + dx, y + dy
            if (dx or dy) and in_bounds(nx, ny) and board.grid[ny][nx] != EMPTY:
                count += 1
    return count


def candidate_cells(board, max_cells=MAX_CELLS):
    """Empty spots with at least one stone within RADIUS, sorted from most to
    least neighbours, cut to `max_cells`. Spots far from every stone are
    almost never useful, so they are skipped."""
    scored = []
    for x, y in board.empty_cells():
        n = neighbours(board, x, y)
        if n > 0:
            scored.append((n, (x, y)))
    # Most neighbours first; ties broken by position so the result is
    # deterministic (same board -> same candidates, useful for experiments).
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [cell for _, cell in scored[:max_cells]]


def candidate_moves(board, max_cells=MAX_CELLS):
    """List of candidate moves for the player to move.
    Each move is a list of stones [(x, y), ...], the same format that
    board.place() and best_move() use:
      - empty board (black's opening): just the centre, [[(9, 9)]]
      - otherwise: pairs of candidate spots, without repeating {A, B} as {B, A}
    """
    if board.stones_played == 0:
        return [[CENTRE]]

    cells = candidate_cells(board, max_cells)
    if len(cells) < 2:
        # Not enough spots near stones (almost full board): use any empty spot.
        cells = board.empty_cells()[:max_cells]

    if board.stones_this_turn() == 1 or len(cells) == 1:
        return [[cell] for cell in cells]

    # combinations() gives each pair once: (A, B) but never (B, A).
    return [list(pair) for pair in combinations(cells, 2)]


# ===========================================================================
# Threat-based candidate generation (version 2, session 2)
# ===========================================================================
#
# The naive generator ranks cells by how many stones are around them, so it
# cannot tell an important cell (the end of a line of five) from a merely
# crowded one. This version ranks each empty cell by the windows of six that
# pass through it: placing a stone there either brings one of our windows
# closer to six (attack) or kills one of the opponent's (defence).

from board import BLACK, WHITE, opponent
from evaluation import WINDOWS

# Windows that contain each cell, computed once: CELL_WINDOWS[(x, y)] is the
# list of windows (tuples of 6 positions) that pass through (x, y).
CELL_WINDOWS = {(x, y): [] for y in range(EDGE) for x in range(EDGE)}
for _window in WINDOWS:
    for _cell in _window:
        CELL_WINDOWS[_cell].append(_window)

# Points for a window, indexed by how many stones it already contains.
# With 4 or 5 of our stones the window can be completed THIS turn (we place
# two stones), so it is a win; with 4 or 5 of the opponent's, they win next
# turn unless we block it. Attack outranks defence at the same level because
# we move first: if we can win now, blocking does not matter.
ATTACK = [1, 3, 10, 40, 100_000, 100_000]
DEFENCE = [1, 2, 8, 30, 10_000, 10_000]


def threat_score(board, x, y, player):
    """How useful it is for `player` to place a stone on the empty cell (x, y),
    adding up the windows of six that pass through it."""
    grid = board.grid
    other = opponent(player)
    score = 0
    for window in CELL_WINDOWS[(x, y)]:
        mine = theirs = 0
        for wx, wy in window:
            cell = grid[wy][wx]
            if cell == player:
                mine += 1
            elif cell == other:
                theirs += 1
        if mine and theirs:
            continue                    # dead window: nobody can win here
        if theirs == 0:
            score += ATTACK[mine]       # brings our window closer to six
        if mine == 0:
            score += DEFENCE[theirs]    # blocks the opponent's window
    return score


def threat_cells(board, max_cells=MAX_CELLS):
    """Empty cells near stones, ranked by threat_score for the player to move,
    cut to `max_cells`. Ties are broken by distance to the centre (then by
    position), which removes the left bias of the naive version."""
    player = board.to_move
    cx, cy = CENTRE
    scored = []
    for x, y in board.empty_cells():
        if neighbours(board, x, y) > 0:            # same proximity filter
            s = threat_score(board, x, y, player)
            distance = max(abs(x - cx), abs(y - cy))
            scored.append((-s, distance, (x, y)))
    scored.sort()
    return [cell for _, _, cell in scored[:max_cells]]


def threat_moves(board, max_cells=MAX_CELLS):
    """Same output as candidate_moves(), but with cells chosen by threats.
    Pairs come out with the two best cells first, which will also help the
    move ordering of Alpha-Beta."""
    if board.stones_played == 0:
        return [[CENTRE]]

    cells = threat_cells(board, max_cells)
    if len(cells) < 2:
        cells = board.empty_cells()[:max_cells]

    if board.stones_this_turn() == 1 or len(cells) == 1:
        return [[cell] for cell in cells]

    return [list(pair) for pair in combinations(cells, 2)]


# ===========================================================================
# Move generation by stages: imminent threats first (version 3, session 3)
# ===========================================================================
#
# Before ranking cells, the generator checks the two situations that decide
# the game on the spot, as the guide of session 3 asks:
#   1. WIN:    the player to move has a window with 4 or 5 of his stones and
#              none of the opponent's -> complete it and win. Only that move
#              is returned, so the search plays it without exploring anything.
#   2. DEFEND: the opponent has such windows (threats, as defined by Wu and
#              Huang) -> he wins next turn unless every one of them is
#              blocked. Only the pairs of cells that block all of them are
#              returned. If no pair can (three or more independent threats),
#              the game is lost and the normal moves are returned.
#   3. Otherwise, the threat-based pairs of version 2, but ordered so that the
#      pairs that create new threats (windows with 4 or more stones) come
#      first, then by the threat score of their cells.

def _scan(board, player):
    """One pass over the 924 windows. Returns:
      mine:   windows where `player` has 4 or 5 stones and the opponent none
              (he can complete six this turn), as lists of their empty cells;
      theirs: the same for the opponent (his threats);
      makers: empty cells that are in a window with exactly 3 stones of
              `player` and none of the opponent's: one stone there turns
              the window into a threat."""
    grid = board.grid
    other = opponent(player)
    mine, theirs, makers = [], [], set()
    for window in WINDOWS:
        p = o = 0
        empty = []
        for x, y in window:
            cell = grid[y][x]
            if cell == player:
                p += 1
            elif cell == other:
                o += 1
            else:
                empty.append((x, y))
        if o == 0 and p >= 4:
            mine.append(empty)
        elif p == 0 and o >= 4:
            theirs.append(empty)
        elif o == 0 and p == 3:
            makers.update(empty)
    return mine, theirs, makers


MAX_MAKERS = 6   # extra threat-making cells added to the candidates


def _new_threats(board, pair, player):
    """How many windows become threats for `player` (4 or more of his stones,
    none of the opponent's) when he places the two stones of `pair`.
    Only the windows that pass through those two cells can change."""
    grid = board.grid
    other = opponent(player)
    windows = set(CELL_WINDOWS[pair[0]]) | set(CELL_WINDOWS[pair[1]])
    count = 0
    for window in windows:
        before = after = 0
        clean = True
        for cell in window:
            x, y = cell
            value = grid[y][x]
            if value == other:
                clean = False
                break
            if value == player:
                before += 1
                after += 1
            elif cell in pair:
                after += 1
        if clean and before < 4 <= after:
            count += 1
    return count


def staged_moves(board, max_cells=MAX_CELLS):
    """Candidate moves of version 3 (same output format as threat_moves)."""
    if board.stones_played == 0:
        return [[CENTRE]]
    player = board.to_move
    n_stones = board.stones_this_turn()
    mine, theirs, makers = _scan(board, player)
    cells = threat_cells(board, max_cells)

    # Stage 1: win now.
    for empty in mine:
        if len(empty) <= n_stones:
            move = list(empty)
            if len(move) < n_stones:            # one stone is enough to win:
                for cell in cells:              # add the best other cell
                    if cell not in move:
                        move.append(cell)
                        break
            return [move]

    # Stage 2: block every threat of the opponent.
    if theirs:
        blocking = sorted({cell for empty in theirs for cell in empty})
        pool = blocking + [c for c in cells if c not in blocking]
        defences = []
        for a, b in combinations(pool, 2):
            if a not in blocking and b not in blocking:
                continue
            if all(a in empty or b in empty for empty in theirs):
                defences.append([a, b])
        if defences:
            defences.sort(key=lambda m: -(threat_score(board, *m[0], player)
                                          + threat_score(board, *m[1], player)))
            return defences[:max_cells * (max_cells - 1) // 2]
        # No pair blocks everything: the game is lost; play normally.

    # Stage 3: normal moves. The cells that create a threat with one stone
    # are always candidates (the best MAX_MAKERS of them), even if their
    # threat score leaves them out of the best cells; then the pairs that
    # create the most threat windows go first.
    extra = sorted((c for c in makers if c not in cells),
                   key=lambda c: -threat_score(board, *c, player))
    cells = cells + extra[:MAX_MAKERS]
    if n_stones == 1 or len(cells) < 2:
        return [[c] for c in cells] or threat_moves(board, max_cells)
    pairs = [list(p) for p in combinations(cells, 2)]
    scored = [(-_new_threats(board, m, player), i, m)
              for i, m in enumerate(pairs)]
    scored.sort()
    return [m for _, _, m in scored]
