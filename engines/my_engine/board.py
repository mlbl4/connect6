
"""
Board state for Connect6.
 
Holds the 19x19 grid, whose turn it is and how many stones have been played,
and detects the end of the game.
Works only with numeric coordinates (x, y); letters are handled by main.py.
"""
 
EDGE = 19                    # board size (19x19)
EMPTY, BLACK, WHITE = 0, 1, 2
DRAW = 3                     # result when the board is full and nobody won
WIN_LENGTH = 6               # stones in a line needed to win
 
# The 4 directions a line can go. Each one is checked forwards and backwards,
# so these 4 cover all 8 neighbours of a stone.
DIRECTIONS = [(1, 0),        # horizontal (row)
              (0, 1),        # vertical (column)
              (1, 1),        # diagonal ↘
              (1, -1)]       # diagonal ↗
 
 
def opponent(color):
    """Return the other player's colour."""
    return WHITE if color == BLACK else BLACK
 
 
def in_bounds(x, y):
    """True if (x, y) is inside the board."""
    return 0 <= x < EDGE and 0 <= y < EDGE
 
 
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
 
    # -----------------------------------------------------------------------
    # End-of-game detection
    # -----------------------------------------------------------------------
 
    def count_direction(self, x, y, dx, dy, color):
        """Count consecutive stones of `color` starting next to (x, y)
        and walking in direction (dx, dy). The stone at (x, y) is not counted."""
        count = 0
        x, y = x + dx, y + dy
        while in_bounds(x, y) and self.grid[y][x] == color:
            count += 1
            x, y = x + dx, y + dy
        return count
 
    def is_win(self, x, y):
        """True if the stone at (x, y) is part of a line of 6 or more
        stones of its colour: horizontal, vertical or diagonal.
        Both ways are counted because the stone may be in the middle
        of the line, not only at one end."""
        color = self.grid[y][x]
        if color == EMPTY:
            return False
        for dx, dy in DIRECTIONS:
            length = (1                                            # the stone itself
                      + self.count_direction(x, y, dx, dy, color)     # forwards
                      + self.count_direction(x, y, -dx, -dy, color))  # backwards
            if length >= WIN_LENGTH:
                return True
        return False
 
    def check_winner(self, stones):
        """Call after placing `stones` (the last move).
        Return BLACK or WHITE if that move won, DRAW if the board is full,
        or None if the game goes on.
        A new line of 6 must pass through one of the stones just placed,
        so only those need to be checked, not the whole board."""
        for x, y in stones:
            if self.is_win(x, y):
                return self.grid[y][x]
        if self.stones_played == EDGE * EDGE:
            return DRAW
        return None
 
