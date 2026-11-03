"""
Move search for Connect6.

Version 1: Minimax with a fixed depth.
Version 2: Alpha-Beta pruning (same decisions as Minimax, fewer nodes),
           protected by a time limit (see TIME_LIMIT).
Version 3: same search; new move generator and evaluation (threats).

  - Black is MAX: it wants the evaluation as high as possible.
  - White is MIN: it wants the evaluation as low as possible.
The evaluation is always from Black's point of view (see evaluation.py),
so the same search works for both colours.

main.py only calls best_move(). The settings below choose which version of
each component is used, so every version can be compared in the experiments
without changing any other code.
"""

import random
import time

from board import BLACK
import moves
import evaluation

DEPTH = 3          # turns looked ahead (version 1 used 2; Alpha-Beta allows 3)

# Settings (version 3 by default). Previous versions:
#   version 1: GENERATOR = moves.candidate_moves, EVALUATE = evaluation.evaluate,
#              ALGORITHM = "minimax", DEPTH = 2
#   version 2: GENERATOR = moves.threat_moves,
#              EVALUATE = evaluation.evaluate_weighted
GENERATOR = moves.staged_moves           # candidate moves
EVALUATE = evaluation.evaluate_threats   # static evaluation
ALGORITHM = "alphabeta"                  # "minimax" or "alphabeta"

# Time protection. The GUI waits at most 30 seconds for a move, and a late
# move means the engine is not evaluated. With TIME_LIMIT set, best_move()
# searches depth 1, then 2, ..., up to DEPTH (iterative deepening). If the
# time runs out in the middle of a depth, that unfinished depth is discarded
# and the engine plays the best move of the last depth it completed.
# None = plain fixed-depth search (used by the measurement scripts, so their
# node counts are those of a single depth).
TIME_LIMIT = 20.0  # seconds: 10 s of margin below the 30 s of the GUI

# Counters for the experiments, reset at the start of every best_move():
#   nodes:  positions explored (expanded nodes)
#   pruned: candidate moves that Alpha-Beta skipped without exploring them
#   depth_reached: deepest search completed in the last best_move()
nodes = 0
pruned = 0
depth_reached = 0

_deadline = None   # time.perf_counter() value at which the search must stop


class _OutOfTime(Exception):
    """Raised inside the search when the deadline has passed."""


def _check_time():
    """Called at every node: stop the search if the deadline has passed."""
    if _deadline is not None and time.perf_counter() > _deadline:
        raise _OutOfTime


def random_move(board, color):
    """Baseline engine (step 1 of the practice): a random legal move."""
    empties = board.empty_cells()
    n_stones = board.stones_this_turn()
    return random.sample(empties, min(n_stones, len(empties)))


# ---------------------------------------------------------------------------
# Version 1: Minimax
# ---------------------------------------------------------------------------

def minimax(board, depth, last_move):
    """Value of the current board, looking `depth` more turns ahead.
    `last_move` is the move that produced this board; it is used to detect
    whether that move ended the game.
      - Game over, or depth exhausted -> ask the evaluation (a leaf).
      - Otherwise try every candidate move for the player to move,
        compute its value recursively, and keep the maximum if Black is
        to move or the minimum if White is to move."""
    global nodes
    nodes += 1
    _check_time()

    # Leaf 1: the last move ended the game -> exact result.
    if board.check_winner(last_move) is not None:
        return EVALUATE(board, last_move)
    # Leaf 2: we have looked as far as we wanted -> estimate.
    if depth == 0:
        return EVALUATE(board)

    candidates = GENERATOR(board)
    if not candidates:                 # no legal moves left
        return EVALUATE(board)

    maximising = (board.to_move == BLACK)
    best = float("-inf") if maximising else float("inf")
    for move in candidates:
        color = board.to_move
        board.place(color, move)                      # try the move...
        try:
            value = minimax(board, depth - 1, move)   # ...look ahead...
        finally:
            board.undo(move)                          # ...and always take it back
        if maximising:
            best = max(best, value)
        else:
            best = min(best, value)
    return best


# ---------------------------------------------------------------------------
# Version 2: Alpha-Beta
# ---------------------------------------------------------------------------

def alphabeta(board, depth, last_move, alpha, beta):
    """Same value as minimax(), but it stops exploring a node's remaining
    moves as soon as it can prove they cannot change the final decision.
      alpha: the best value Black is already GUARANTEED elsewhere in the tree.
      beta:  the best value White is already GUARANTEED elsewhere in the tree.
    If a node's value can no longer fall between alpha and beta, the player
    above will never choose it, so its remaining moves are skipped (pruned)."""
    global nodes, pruned
    nodes += 1
    _check_time()

    if board.check_winner(last_move) is not None:
        return EVALUATE(board, last_move)
    if depth == 0:
        return EVALUATE(board)

    candidates = GENERATOR(board)
    if not candidates:
        return EVALUATE(board)

    color = board.to_move
    if color == BLACK:                                 # MAX node
        value = float("-inf")
        for i, move in enumerate(candidates):
            board.place(color, move)
            try:
                value = max(value, alphabeta(board, depth - 1, move, alpha, beta))
            finally:
                board.undo(move)
            alpha = max(alpha, value)
            if alpha >= beta:          # White already has something better
                pruned += len(candidates) - i - 1
                break
        return value
    else:                                              # MIN node
        value = float("inf")
        for i, move in enumerate(candidates):
            board.place(color, move)
            try:
                value = min(value, alphabeta(board, depth - 1, move, alpha, beta))
            finally:
                board.undo(move)
            beta = min(beta, value)
            if alpha >= beta:          # Black already has something better
                pruned += len(candidates) - i - 1
                break
        return value


# ---------------------------------------------------------------------------
# Root: choose the move to play
# ---------------------------------------------------------------------------

def _search_root(board, color, candidates, depth):
    """One complete search of `depth` turns: try every candidate, ask the
    search for its value, and keep the best one (the first one found on
    ties, so the same board always gives the same answer). With Alpha-Beta,
    the best value found so far is passed down as alpha (Black) or beta
    (White), so later moves can be pruned."""
    maximising = (color == BLACK)
    best_value = float("-inf") if maximising else float("inf")
    chosen = candidates[0]
    for move in candidates:
        board.place(color, move)
        try:
            if ALGORITHM == "minimax":
                value = minimax(board, depth - 1, move)
            elif maximising:
                value = alphabeta(board, depth - 1, move, best_value, float("inf"))
            else:
                value = alphabeta(board, depth - 1, move, float("-inf"), best_value)
        finally:
            board.undo(move)
        if (maximising and value > best_value) or \
           (not maximising and value < best_value):
            best_value, chosen = value, move
    return chosen


def best_move(board, color):
    """Return the move (list of stones) chosen for `color`."""
    global nodes, pruned, depth_reached, _deadline
    nodes = pruned = 0

    candidates = GENERATOR(board)
    if len(candidates) == 1:           # e.g. the opening: nothing to compare
        depth_reached = 0
        return candidates[0]

    if TIME_LIMIT is None:             # fixed depth, no time control
        _deadline = None
        depth_reached = DEPTH
        return _search_root(board, color, candidates, DEPTH)

    # Iterative deepening under a time limit.
    _deadline = time.perf_counter() + TIME_LIMIT
    chosen = candidates[0]             # safety net: always a legal move
    depth_reached = 0
    try:
        for depth in range(1, DEPTH + 1):
            chosen = _search_root(board, color, candidates, depth)
            depth_reached = depth
    except _OutOfTime:
        pass                           # keep the move of the last full depth
    finally:
        _deadline = None
    return chosen
