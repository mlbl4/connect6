"""
Move search for Connect6.

Step 1: random legal move. 
This module will contains minimax (for session 1) and alpha-beta (for session 2); 
main.py only calls best_move().
"""

import random


def best_move(board, color):
    """Return the list of stones (x, y) to play for `color`.
    For now `color` is unused: the move is random."""
    empties = board.empty_cells()
    n_stones = board.stones_this_turn()
    return random.sample(empties, min(n_stones, len(empties)))