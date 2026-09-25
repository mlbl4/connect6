"""
Board state for Connect6.

Holds the 19x19 grid, whose turn it is and how many stones have been played.
Works only with numeric coordinates (x, y); letters are handled by main.py.
"""

EDGE = 19                    # board size (19x19)
EMPTY, BLACK, WHITE = 0, 1, 2


def opponent(color):
    """Return the other player's colour."""
    return WHITE if color == BLACK else BLACK


class Board:
    def __init__(self):
        self.reset()

    def reset(self):
        """Empty board; black always moves first."""
        self.grid = [[EMPTY] * EDGE for _ in range(EDGE)]   # grid[y][x]
        self.to_move = BLACK
        self.stones_played = 0

    def place(self, color, stones):
        """Put stones on the board and hand the turn to the other player.
        Whoever did not play last is the one to move."""
        for x, y in stones:
            self.grid[y][x] = color
            self.stones_played += 1
        self.to_move = opponent(color)

    def empty_cells(self):
        """List of (x, y) positions with no stone."""
        return [(x, y) for y in range(EDGE) for x in range(EDGE)
                if self.grid[y][x] == EMPTY]

    def stones_this_turn(self):
        """Black's very first move is a single stone; every other move is 2."""
        return 1 if self.stones_played == 0 else 2