"""
Plays two versions of the engine against each other, once with each colour.
Run with:  python match.py
A version is a set of settings for search.py (generator, evaluation,
algorithm and depth). Prints the result and the slowest move of each game.
"""
import time
import search, moves, evaluation
from board import Board, BLACK, WHITE, DRAW

VERSIONS = {
    "v1": dict(GENERATOR=moves.candidate_moves, EVALUATE=evaluation.evaluate,
               ALGORITHM="minimax", DEPTH=2),
    "v2": dict(GENERATOR=moves.threat_moves, EVALUATE=evaluation.evaluate_weighted,
               ALGORITHM="alphabeta", DEPTH=3),
}

def use(version):
    for name, value in VERSIONS[version].items():
        setattr(search, name, value)

def play(black, white, max_turns=120):
    board = Board()
    players = {BLACK: black, WHITE: white}
    slowest = {black: 0.0, white: 0.0}
    for turn in range(max_turns):
        color = board.to_move
        use(players[color])
        t = time.perf_counter()
        move = search.best_move(board, color)
        slowest[players[color]] = max(slowest[players[color]], time.perf_counter() - t)
        board.place(color, move)
        result = board.check_winner(move)
        if result is not None:
            return result, turn + 1, slowest
    return None, max_turns, slowest

if __name__ == "__main__":
    for black, white in (("v2", "v1"), ("v1", "v2")):
        result, turns, slowest = play(black, white)
        winner = {BLACK: f"Black ({black})", WHITE: f"White ({white})",
                  DRAW: "nobody (draw)", None: "nobody (move limit)"}[result]
        print(f"Black {black} vs White {white}: {winner} wins after {turns} turns. "
              f"Slowest move: {black} {slowest[black]:.1f} s, {white} {slowest[white]:.1f} s")
