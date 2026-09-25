#!/usr/bin/env python3
# Shebang: lets Linux/Mac run this file directly as a program, using Python 3.
"""
Connect6 engine - API (entry point).

The GUI starts this program as a separate process and talks to it through
text lines: it writes commands to our stdin and reads our answers from stdout.
This file only handles that conversation and the letters <-> numbers
translation; the board lives in board.py and the thinking in search.py.
Anything that is not an answer for the GUI must go to stderr (see debug()).
"""

import sys

from board import Board, EDGE, EMPTY, BLACK, WHITE
from search import best_move

ENGINE_NAME = "MariaEngine"


# ---------------------------------------------------------------------------
# Input / output helpers
# ---------------------------------------------------------------------------

def send(msg):
    """Send one line to the GUI. flush=True is essential: without it the text
    stays in Python's buffer and the GUI waits until it times out."""
    print(msg, flush=True)


def debug(msg):
    """Debug messages go to stderr so they never confuse the GUI."""
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Coordinate conversion: letters <-> (x, y)
# ---------------------------------------------------------------------------

def parse_stones(text):
    """Convert 'JJKK' -> [(9, 9), (10, 10)] (incoming, from the GUI).
    Each stone is 2 letters (x, y) in A..S. Black's opening single stone
    arrives duplicated as 'JJJJ' (that's how the GUI sends it), so repeated
    positions are removed."""
    text = text.strip().upper()
    stones = []
    for i in range(0, len(text) - 1, 2):
        x = ord(text[i]) - ord('A')          # letter -> number: 'A'=0 ... 'S'=18
        y = ord(text[i + 1]) - ord('A')
        if 0 <= x < EDGE and 0 <= y < EDGE and (x, y) not in stones:
            stones.append((x, y))
    return stones


def stones_to_text(stones):
    """Convert [(9, 9), (10, 10)] -> 'JJKK' (outgoing, to the GUI).
    A single stone is duplicated ('JJJJ'), the same format the GUI uses."""
    if len(stones) == 1:
        stones = stones * 2
    return "".join(chr(ord('A') + x) + chr(ord('A') + y) for x, y in stones)


# ---------------------------------------------------------------------------
# Engine controller: receives commands, delegates the work, answers
# ---------------------------------------------------------------------------

class Engine:
    def __init__(self):
        self.board = Board()
        self.time_limit = None   # set by the 'depth' command

    def play_and_answer(self):
        """Ask the search for a move, apply it to our board and send it."""
        color = self.board.to_move
        stones = best_move(self.board, color)
        self.board.place(color, stones)
        send("move " + stones_to_text(stones))

    def print_board(self):
        """Human-readable board ('print' command): X = black, O = white."""
        symbols = {EMPTY: '.', BLACK: 'X', WHITE: 'O'}
        letters = "".join(chr(ord('A') + i) for i in range(EDGE))
        send("  " + letters)
        for y in range(EDGE):
            row = "".join(symbols[self.board.grid[y][x]] for x in range(EDGE))
            send(chr(ord('A') + y) + " " + row)

    def run(self):
        """Command loop: read one line, answer it, repeat until exit."""
        while True:
            line = sys.stdin.readline()
            if not line:                 # stdin closed: the GUI has exited
                break
            parts = line.strip().split()
            if not parts:
                continue
            cmd, args = parts[0].lower(), parts[1:]

            if cmd == "name":
                send("name " + ENGINE_NAME)

            elif cmd in ("exit", "quit"):
                break

            elif cmd == "print":
                self.print_board()

            elif cmd == "new":
                # 'new black' / 'new white' give us a colour; the GUI sends
                # 'new xxx', which just means "reset the board".
                self.board.reset()
                if args and args[0].lower() == "black":
                    # We are black and black starts: play the opening now.
                    # (Assumed behaviour; check with the teacher's tests.)
                    self.play_and_answer()

            elif cmd in ("black", "white") and args:
                color = BLACK if cmd == "black" else WHITE
                self.board.place(color, parse_stones(args[0]))

            elif cmd == "next":
                self.play_and_answer()

            elif cmd == "move" and args:
                # The opponent played these stones; now it is our turn.
                self.board.place(self.board.to_move, parse_stones(args[0]))
                self.play_and_answer()

            elif cmd == "depth" and args:
                # Originally the search depth; in this practice, the time
                # limit per turn. Stored now, used once the search exists.
                try:
                    self.time_limit = int(args[0])
                except ValueError:
                    pass

            elif cmd in ("vcf", "unvcf"):
                pass                     # the statement says to ignore these

            elif cmd == "help":
                send("Commands: name, print, exit/quit, black XXXX, white XXXX, "
                     "next, move XXXX, new black, new white, depth d, vcf, "
                     "unvcf, help")

            else:
                debug("Unknown command: " + line.strip())


if __name__ == "__main__":
    Engine().run()