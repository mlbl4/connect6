"""
Move search for Connect6.

Version 1: Minimax with a fixed depth.
  - Black is MAX: it wants the evaluation as high as possible.
  - White is MIN: it wants the evaluation as low as possible.
The evaluation is always from Black's point of view (see evaluation.py),
so the same search works for both colours.

main.py only calls best_move(). random_move() is kept as the baseline
engine for the experiments.
"""

import random

from board import BLACK
from moves import candidate_moves
from evaluation import evaluate

DEPTH = 2          # turns looked ahead: my move + the opponent's reply

# Counter of positions explored in the last search (for the experiments:
# "number of expanded nodes"). Reset at the start of every best_move().
nodes = 0


def random_move(board, color):
    """Baseline engine (step 1 of the practice): a random legal move."""
    empties = board.empty_cells()
    n_stones = board.stones_this_turn()
    return random.sample(empties, min(n_stones, len(empties)))


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

    # Leaf 1: the last move ended the game -> exact result.
    if board.check_winner(last_move) is not None:
        return evaluate(board, last_move)
    # Leaf 2: we have looked as far as we wanted -> estimate.
    if depth == 0:
        return evaluate(board)

    moves = candidate_moves(board)
    if not moves:                      # no legal moves left
        return evaluate(board)

    maximising = (board.to_move == BLACK)
    best = float("-inf") if maximising else float("inf")
    for move in moves:
        color = board.to_move
        board.place(color, move)                  # try the move...
        value = minimax(board, depth - 1, move)   # ...look ahead...
        board.undo(move)                          # ...and take it back
        if maximising:
            best = max(best, value)
        else:
            best = min(best, value)
    return best


def best_move(board, color):
    """Return the move (list of stones) that Minimax chooses for `color`.
    Same loop as minimax() at the root, but it remembers WHICH move gave
    the best value, not only the value. On ties, the first move found is
    kept, so the same board always gives the same answer."""
    global nodes
    nodes = 0

    moves = candidate_moves(board)
    if len(moves) == 1:                # e.g. the opening: nothing to compare
        return moves[0]

    maximising = (color == BLACK)
    best_value = float("-inf") if maximising else float("inf")
    chosen = moves[0]
    for move in moves:
        board.place(color, move)
        value = minimax(board, DEPTH - 1, move)
        board.undo(move)
        if (maximising and value > best_value) or \
           (not maximising and value < best_value):
            best_value, chosen = value, move
    return chosen