"""
Compares two versions of the engine over several openings.
Run with:   python compare.py v3 v2 [number_of_openings] [first_opening]

The engines are deterministic, so a single game between them always gives
the same result. To compare them fairly, each game starts from a different
opening: Black's first stone near the centre and two random turns of two
stones each near the centre (always the same openings, thanks to a fixed
random seed). Each opening is played twice, once with each version as Black.

Prints the result of every game and a summary: wins of each version, draws,
and the slowest move of each version (to check the time limit).
"""
import random
import sys
import time

import search
from board import Board, BLACK, WHITE, DRAW, EMPTY
from match import VERSIONS, use


def opening(seed):
    """Board after a random opening: 1 black stone and 2 turns near the centre."""
    rng = random.Random(seed)
    board = Board()
    board.place(BLACK, [(rng.randint(7, 11), rng.randint(7, 11))])
    for _ in range(2):
        cells = [c for c in board.empty_cells()
                 if 6 <= c[0] <= 12 and 6 <= c[1] <= 12]
        board.place(board.to_move, rng.sample(cells, 2))
    return board


def play_from(board, black, white, max_turns=100):
    """Play until the end; returns (result, turns, slowest move per version)."""
    players = {BLACK: black, WHITE: white}
    slowest = {black: 0.0, white: 0.0}
    for turn in range(max_turns):
        color = board.to_move
        use(players[color])
        start = time.perf_counter()
        move = search.best_move(board, color)
        elapsed = time.perf_counter() - start
        slowest[players[color]] = max(slowest[players[color]], elapsed)
        legal = (len(set(move)) == len(move) == board.stones_this_turn()
                 and all(board.grid[y][x] == EMPTY for x, y in move))
        if not legal:
            raise RuntimeError(f"illegal move {move} by {players[color]}")
        board.place(color, move)
        result = board.check_winner(move)
        if result is not None:
            return result, turn + 1, slowest
    return None, max_turns, slowest


if __name__ == "__main__":
    a, b = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    first = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    wins = {a: 0, b: 0}
    draws = 0
    slowest = {a: 0.0, b: 0.0}
    for seed in range(first, first + n):
        for black, white in ((a, b), (b, a)):
            result, turns, times = play_from(opening(seed), black, white)
            winner = {BLACK: black, WHITE: white}.get(result)
            if winner:
                wins[winner] += 1
            else:
                draws += 1
            for v in (a, b):
                slowest[v] = max(slowest[v], times[v])
            print(f"opening {seed}: Black {black} vs White {white} -> "
                  f"{winner or 'draw'} in {turns} turns", flush=True)
    print()
    print(f"{a}: {wins[a]} wins   {b}: {wins[b]} wins   draws: {draws}")
    print(f"slowest move: {a} {slowest[a]:.1f} s, {b} {slowest[b]:.1f} s")
