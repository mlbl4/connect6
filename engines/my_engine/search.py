"""
Move search for Connect6.

Version 1: Minimax with a fixed depth.
Version 2: Alpha-Beta pruning (same decisions as Minimax, fewer nodes),
           protected by a time limit (see TIME_LIMIT).
Version 3: same search; new move generator and evaluation (threats).
Version 4: same search; evaluation with weights learned by a genetic algorithm.
Version 5: Alpha-Beta with the optimisations of session 4 (see the end of
           the file): transposition table, quiescence search, N-best forward
           pruning, move ordering from the previous iteration, and a time
           limit taken from the GUI.

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

DEPTH = 6          # maximum turns looked ahead (version 1: 2; versions 2-4: 3;
                   # version 5 goes as deep as the time limit allows)

# Settings (version 3 by default). Previous versions:
#   version 1: GENERATOR = moves.candidate_moves, EVALUATE = evaluation.evaluate,
#              ALGORITHM = "minimax", DEPTH = 2
#   version 2: GENERATOR = moves.threat_moves,
#              EVALUATE = evaluation.evaluate_weighted
#   version 3: EVALUATE = evaluation.evaluate_threats, ALGORITHM = "alphabeta",
#              DEPTH = 3
#   version 4: EVALUATE = evaluation.evaluate_learned, ALGORITHM = "alphabeta",
#              DEPTH = 3
GENERATOR = moves.staged_moves           # candidate moves
EVALUATE = evaluation.evaluate_learned   # static evaluation
ALGORITHM = "optimised"                  # "minimax", "alphabeta" or "optimised"

# Time protection. The GUI waits at most 30 seconds for a move, and a late
# move means the engine is not evaluated. With TIME_LIMIT set, best_move()
# searches depth 1, then 2, ..., up to DEPTH (iterative deepening). If the
# time runs out in the middle of a depth, that unfinished depth is discarded
# and the engine plays the best move of the last depth it completed.
# None = plain fixed-depth search (used by the measurement scripts, so their
# node counts are those of a single depth).
TIME_LIMIT = 20.0  # seconds: 10 s of margin below the 30 s of the GUI
                   # (version 5: replaced by the time sent by the GUI, see
                   # set_time_limit())

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
            elif ALGORITHM == "optimised":
                value = optimised(board, depth - 1, move,
                                  *((best_value, float("inf")) if maximising
                                    else (float("-inf"), best_value)),
                                  _child_key(_root_key, move, color))
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
    global nodes, pruned, depth_reached, _deadline, _root_key
    nodes = pruned = 0
    _table.clear()
    _root_key = _key_of(board)

    candidates = GENERATOR(board)
    if len(candidates) == 1:           # e.g. the opening: nothing to compare
        depth_reached = 0
        return candidates[0]

    if TIME_LIMIT is None:             # fixed depth, no time control
        _deadline = None
        depth_reached = DEPTH
        return _search_root(board, color, candidates, DEPTH)

    # Iterative deepening under a time limit.
    start = time.perf_counter()
    _deadline = start + TIME_LIMIT
    chosen = candidates[0]             # safety net: always a legal move
    depth_reached = 0
    try:
        for depth in range(1, DEPTH + 1):
            chosen = _search_root(board, color, candidates, depth)
            depth_reached = depth
            if ALGORITHM == "optimised":
                # Move ordering: the best move of this depth is searched
                # first at the next depth, so Alpha-Beta prunes more.
                candidates = [chosen] + [m for m in candidates if m != chosen]
                # Each depth costs several times the previous one: if half
                # of the time is gone, the next depth cannot finish.
                if time.perf_counter() - start > TIME_LIMIT / 2:
                    break
    except _OutOfTime:
        pass                           # keep the move of the last full depth
    finally:
        _deadline = None
    return chosen


# ---------------------------------------------------------------------------
# Version 5: optimised Alpha-Beta (session 4)
# ---------------------------------------------------------------------------
#
# The optimisations proposed in the guide of session 4 and in Unit 3:
#
#  - Transposition table: the same position can be reached by different
#    orders of moves (A then B, or B then A). Its value is stored the first
#    time it is searched and reused afterwards. Each position is identified
#    by a Zobrist key: a random 64-bit number per (colour, cell), combined
#    with XOR, which can be updated in two operations per stone when a move
#    is played or undone. The table also stores the best move found in each
#    position, which is searched first the next time (move ordering).
#
#  - Quiescence search (horizon effect): when the depth runs out just after
#    a player has created a threat, the static evaluation of that position is
#    not reliable: the opponent is forced to block, and the result of that
#    block is unknown. Instead of stopping there, the search goes on with
#    only the forced moves (the blocks) until the position is quiet, up to
#    QUIESCENCE_DEPTH more turns.
#
#  - Forward pruning (N-best): inside the tree only the N_BEST first candidate
#    moves of the generator are searched (they are already ordered from best
#    to worst). The root still considers all of them.
#
#  - Iterative deepening and move ordering: the best move of each depth is
#    searched first at the next depth (see best_move()).
#
#  - Real-time response: the time limit comes from the GUI (set_time_limit()).

N_BEST = 20              # candidate moves searched at each inner node
QUIESCENCE_DEPTH = 0     # extra turns of forced moves at the leaves.
# Measured: with 1 extra turn the search reaches depth 3 in 20 s; without
# it, depth 4 or 5. The deeper plain search is preferred (set to 1 or 2 to
# use the quiescence search).

_rng = random.Random(6)
_ZOBRIST = {(color, x, y): _rng.getrandbits(64)
            for color in (1, 2) for x in range(19) for y in range(19)}
_table = {}              # Zobrist key -> (depth, value, flag, best move)
_root_key = 0
EXACT, LOWER, UPPER = 0, 1, 2


def _key_of(board):
    """Zobrist key of a board: XOR of the numbers of all its stones."""
    key = 0
    for y, row in enumerate(board.grid):
        for x, cell in enumerate(row):
            if cell in (1, 2):
                key ^= _ZOBRIST[(cell, x, y)]
    return key


def _child_key(key, move, color):
    """Key after `color` places the stones of `move` (XOR adds a stone)."""
    for x, y in move:
        key ^= _ZOBRIST[(color, x, y)]
    return key


def set_time_limit(seconds):
    """Time limit per turn sent by the GUI with the 'depth' command. 80% of
    it is used, never more than the 20 s safety limit, so that the answer
    always arrives in time even on a slower computer."""
    global TIME_LIMIT
    TIME_LIMIT = max(0.5, min(20.0, 0.8 * seconds))


def quiescence(board, depth, alpha, beta, key):
    """Value of a leaf, looking further only while the position is forced:
    the player to move must block a threat of the opponent."""
    global nodes
    nodes += 1
    _check_time()
    value = EVALUATE(board)
    if depth == 0 or abs(value) >= evaluation.NEAR_WIN:
        return value
    player = board.to_move
    _, theirs, _ = moves._scan(board, player)
    if not theirs:                     # quiet: the evaluation is reliable
        return value
    color = player
    maximising = (color == BLACK)
    best = float("-inf") if maximising else float("inf")
    for move in GENERATOR(board)[:N_BEST]:   # only the blocks
        board.place(color, move)
        try:
            v = quiescence(board, depth - 1, alpha, beta,
                           _child_key(key, move, color))
        finally:
            board.undo(move)
        if maximising:
            best = max(best, v)
            alpha = max(alpha, v)
        else:
            best = min(best, v)
            beta = min(beta, v)
        if alpha >= beta:
            break
    return best


def optimised(board, depth, last_move, alpha, beta, key):
    """Alpha-Beta (same structure as alphabeta()) with transposition table,
    quiescence search at the leaves and N-best forward pruning."""
    global nodes, pruned
    if board.check_winner(last_move) is not None:
        nodes += 1
        return EVALUATE(board, last_move)
    if depth == 0:
        return quiescence(board, QUIESCENCE_DEPTH, alpha, beta, key)
    nodes += 1
    _check_time()

    # Transposition table: reuse a previous search of this position.
    alpha0, beta0 = alpha, beta
    entry = _table.get(key)
    first = None
    if entry is not None:
        stored_depth, stored_value, flag, first = entry
        if stored_depth >= depth:
            if flag == EXACT:
                return stored_value
            if flag == LOWER:
                alpha = max(alpha, stored_value)
            else:
                beta = min(beta, stored_value)
            if alpha >= beta:
                return stored_value

    candidates = GENERATOR(board)[:N_BEST]
    if not candidates:
        return EVALUATE(board)
    if first in candidates:            # best move of a previous search first
        candidates.remove(first)
        candidates.insert(0, first)

    color = board.to_move
    maximising = (color == BLACK)
    value = float("-inf") if maximising else float("inf")
    best_move_here = candidates[0]
    for i, move in enumerate(candidates):
        board.place(color, move)
        try:
            v = optimised(board, depth - 1, move, alpha, beta,
                          _child_key(key, move, color))
        finally:
            board.undo(move)
        if (maximising and v > value) or (not maximising and v < value):
            value, best_move_here = v, move
        if maximising:
            alpha = max(alpha, value)
        else:
            beta = min(beta, value)
        if alpha >= beta:
            pruned += len(candidates) - i - 1
            break

    # Store the result. If the search was cut by alpha or beta, the value is
    # only a bound of the real value.
    if value <= alpha0:
        flag = UPPER
    elif value >= beta0:
        flag = LOWER
    else:
        flag = EXACT
    _table[key] = (depth, value, flag, best_move_here)
    return value
