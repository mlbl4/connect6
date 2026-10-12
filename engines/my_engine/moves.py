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
