"""
Games against Cloudict (experiments of session 5: starting positions).

Run from the engine folder, for example on Windows:
    python vs_cloudict.py dist\\mlb.exe ..\\cloudict.exe
or on Linux:
    python3 vs_cloudict.py dist/mlb ../cloudict.linux
Options:
    --level 4        value sent with 'depth' to both engines (AI level of
                     the GUI: Low = 4, Medium = 5, High = 6)
    --max-plies 40   the game is stopped (unfinished) after this many turns
    --out results.txt

Both engines are driven exactly as the GUI drives them (engine.py of the
GUI): before each turn the engine receives 'new xxx', every move of the game
so far ('black XXXX' / 'white XXXX') and 'next', and must answer
'move XXXX' within 30 seconds.

Each opening fixes Black's first stone in the centre and White's first two
stones, so the games are different; every opening is played twice, once
with our engine as Black and once as White. For each game the script
records the result, its length and, for our engine, the time per move and
the depth and nodes of its search (read from the 'stats' lines that main.py
writes to stderr).
"""

import argparse
import queue
import re
import subprocess
import threading
import time

from board import Board, BLACK, WHITE, EMPTY, EDGE

TIMEOUT = 30.0   # seconds the GUI waits for a move

# A real answer: 'move' and four letters A-S. Other lines are ignored (for
# example, Cloudict prints its help at start-up, where one line begins with
# 'move XXXX - tell the engine...').
MOVE_LINE = re.compile(r"^move [A-S]{4}$")

# White's first two stones after Black's stone in the centre (JJ).
OPENINGS = [
    ("adjacent", "JIKI"),     # touching Black's stone
    ("diagonal", "IIKK"),     # on both diagonals
    ("line", "HJLJ"),         # on Black's row, one cell apart
    ("knight", "LKHI"),       # a knight's move away
    ("far", "MMGG"),          # far from Black's stone
]


def to_text(stones):
    if len(stones) == 1:
        stones = stones * 2
    return "".join(chr(65 + x) + chr(65 + y) for x, y in stones)


def to_stones(text):
    stones = []
    for i in range(0, len(text) - 1, 2):
        cell = (ord(text[i]) - 65, ord(text[i + 1]) - 65)
        if cell not in stones:
            stones.append(cell)
    return stones


class Engine:
    """An engine process, driven through stdin/stdout as the GUI does."""

    def __init__(self, command, level):
        self.proc = subprocess.Popen(command, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True,
                                     bufsize=1)
        self.lines = queue.Queue()
        self.stats = queue.Queue()
        threading.Thread(target=self._read, args=(self.proc.stdout, self.lines),
                         daemon=True).start()
        threading.Thread(target=self._read_stats, daemon=True).start()
        self.send("name")
        self.name = self.wait_for("name ", 10)[5:].strip()
        self.send(f"depth {level}")

    @staticmethod
    def _read(stream, out):
        for line in stream:
            out.put(line.strip())

    def _read_stats(self):
        for line in self.proc.stderr:
            parts = line.split()
            if parts[:1] == ["stats"]:
                self.stats.put((int(parts[2]), int(parts[4])))

    def send(self, text):
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def wait_for(self, prefix, timeout):
        end = time.perf_counter() + timeout
        while True:
            left = end - time.perf_counter()
            if left <= 0:
                return None
            try:
                line = self.lines.get(timeout=left)
            except queue.Empty:
                return None
            if (prefix.match(line) if hasattr(prefix, "match")
                    else line.startswith(prefix)):
                return line

    def play(self, history):
        """Ask for the next move; returns (move text or None, seconds)."""
        while not self.lines.empty():         # discard old output
            self.lines.get()
        while not self.stats.empty():
            self.stats.get()
        self.send("new xxx")
        for color, text in history:
            self.send(f"{'black' if color == BLACK else 'white'} {text}")
        start = time.perf_counter()
        self.send("next")
        line = self.wait_for(MOVE_LINE, TIMEOUT)
        elapsed = time.perf_counter() - start
        return (line[5:].strip() if line else None), elapsed

    def last_stats(self):
        try:
            return self.stats.get(timeout=1)
        except queue.Empty:
            return None

    def close(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=2)
        except Exception:
            self.proc.kill()


def legal(board, stones):
    needed = min(board.stones_this_turn(), len(board.empty_cells()))
    return (len(stones) == needed and len(set(stones)) == len(stones)
            and all(0 <= x < EDGE and 0 <= y < EDGE and board.grid[y][x] == EMPTY
                    for x, y in stones))


def play_game(ours_cmd, cloudict_cmd, level, opening, our_color, max_plies):
    ours = Engine(ours_cmd, level)
    cloudict = Engine(cloudict_cmd, level)
    engines = {our_color: ours, 3 - our_color: cloudict}
    board = Board()
    history = []
    for color, text in ((BLACK, "JJJJ"), (WHITE, opening)):
        board.place(color, to_stones(text))
        history.append((color, text))
    times, depths, nodes = [], [], []
    result, reason = "unfinished", "ply limit"
    try:
        while len(history) < max_plies:
            color = board.to_move
            engine = engines[color]
            text, elapsed = engine.play(history)
            if engine is ours:
                times.append(elapsed)
                stats = ours.last_stats()
                if stats:
                    depths.append(stats[0])
                    nodes.append(stats[1])
            if text is None:
                reason = "timeout"
            else:
                stones = to_stones(text)
                if not legal(board, stones):
                    reason, text = "illegal move", None
            if text is None:
                result = "loss" if engine is ours else "win"
                break
            board.place(color, stones)
            history.append((color, to_text(stones)))
            winner = board.check_winner(stones)
            if winner in (BLACK, WHITE):
                result = "win" if winner == our_color else "loss"
                reason = "six stones"
                break
            if winner is not None:
                result, reason = "draw", "full board"
                break
    finally:
        ours.close()
        cloudict.close()
    moves = " ".join(f"{'B' if c == BLACK else 'W'}:{t}" for c, t in history)
    return dict(moves=moves, result=result, reason=reason, plies=len(history),
                our_moves=len(times),
                avg_time=sum(times) / len(times) if times else 0,
                max_time=max(times) if times else 0,
                avg_depth=sum(depths) / len(depths) if depths else 0,
                avg_nodes=sum(nodes) / len(nodes) if nodes else 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ours", help="our engine, e.g. dist/mlb or dist\\mlb.exe")
    parser.add_argument("cloudict", help="Cloudict executable")
    parser.add_argument("--level", type=int, default=4)
    parser.add_argument("--max-plies", type=int, default=40)
    parser.add_argument("--out", default="results_cloudict.txt")
    args = parser.parse_args()

    ours_cmd = args.ours.split()
    totals = {"win": 0, "loss": 0, "draw": 0, "unfinished": 0}
    with open(args.out, "w") as out:
        for name, opening in OPENINGS:
            for our_color in (BLACK, WHITE):
                g = play_game(ours_cmd, [args.cloudict], args.level, opening,
                              our_color, args.max_plies)
                totals[g["result"]] += 1
                line = (f"opening {name} ({opening})  level {args.level}  "
                        f"our colour {'Black' if our_color == BLACK else 'White'}  "
                        f"result {g['result']}  reason {g['reason']}  "
                        f"plies {g['plies']}  our moves {g['our_moves']}  "
                        f"avg time {g['avg_time']:.2f}  max time {g['max_time']:.2f}  "
                        f"avg depth {g['avg_depth']:.1f}  "
                        f"avg nodes {g['avg_nodes']:.0f}\n    moves {g['moves']}")
                print(line, flush=True)
                out.write(line + "\n")
                out.flush()
        summary = (f"Games {sum(totals.values())}  wins {totals['win']}  "
                   f"losses {totals['loss']}  draws {totals['draw']}  "
                   f"unfinished {totals['unfinished']}")
        print(summary)
        out.write(summary + "\n")


if __name__ == "__main__":
    main()
