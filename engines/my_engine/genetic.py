"""
Genetic algorithm that learns the weights of the evaluation (version 4).
Run with:   python genetic.py [generations] [population]

Follows the workflow of the genetic algorithm of Unit 4 and the guide of
session 4 ("a population of individuals initialised with a random
combination of weights around a known configuration ... individuals compete
with each other to calculate their fitness score"):

  1. Representation: an individual (chromosome) is the list of the six real
     weights of evaluation.evaluate_learned(), one gene per feature.
  2. Initialisation: the hand-chosen weights (evaluation.HAND_WEIGHTS) and
     random individuals around them (each weight multiplied by a random
     factor between 0.5 and 1.5).
  3. Evaluation (fitness): every individual plays against every other one
     (round robin), twice from the same opening, once with each colour.
     A win is worth 1 point and a draw 0.5; the fitness is the fraction of
     points obtained. The games are played at depth 1, because the fitness
     is computed thousands of times and must be fast (Unit 4).
  4. Parent selection: tournament selection, picking the best of
     TOURNAMENT_K random individuals.
  5. Crossover: arithmetic recombination, used with real numbers:
     child1 = a*x + (1-a)*y, child2 = a*y + (1-a)*x, with a random a.
  6. Mutation: random reset; each gene, with probability MUTATION_RATE, is
     replaced by a random allowed value (between 0 and 4 times its hand value).
  7. Replacement by fitness: the ELITE best individuals survive and the rest
     of the population is replaced by offspring (elitism keeps the best
     solution found so far).
  8. Repetition for a fixed number of generations.

The best individual of each generation is written to genetic_log.csv.

Validation:   python genetic.py validate
The fitness of a generation comes from few games, so the best individual
of the last generation may have been lucky. The validation plays the best
individual of every generation against the hand-chosen weights on
VALIDATION_OPENINGS new openings (never used during the evolution), twice
each (both colours), and reports the fraction of points of each one.
The individual with the best validation score is the one used by the engine
(evaluation.LEARNED_WEIGHTS).
The games of each generation start from different openings (a new random
seed per generation), so the weights do not overfit a single opening.
"""

import csv
import random
import sys
import time
from itertools import combinations
from multiprocessing import Pool

import evaluation
import moves
import search
from board import BLACK, WHITE
from compare import opening

GENERATIONS = 15
POPULATION = 12
TOURNAMENT_K = 3
MUTATION_RATE = 0.2
ELITE = 2
GAME_DEPTH = 1       # depth of the search during the games of the fitness
MAX_TURNS = 60       # longer games are counted as draws
SEED = 2026          # fixed seed: the run can be repeated
VALIDATION_OPENINGS = 20

HAND = evaluation.HAND_WEIGHTS
LIMITS = [4 * w for w in HAND]   # allowed value of each gene: 0 .. 4 * hand


def play(black_weights, white_weights, seed):
    """One game from opening `seed`. Returns 1 if Black wins, 0 if White
    wins and 0.5 for a draw (or after MAX_TURNS turns)."""
    search.GENERATOR = moves.staged_moves
    search.EVALUATE = evaluation.evaluate_learned
    search.ALGORITHM = "alphabeta"
    search.DEPTH = GAME_DEPTH
    search.TIME_LIMIT = None
    board = opening(seed)
    weights = {BLACK: black_weights, WHITE: white_weights}
    for _ in range(MAX_TURNS):
        color = board.to_move
        evaluation.WEIGHTS_V4 = weights[color]
        move = search.best_move(board, color)
        board.place(color, move)
        result = board.check_winner(move)
        if result == BLACK:
            return 1.0
        if result == WHITE:
            return 0.0
        if result is not None:
            return 0.5
    return 0.5


def _game(args):
    i, j, wi, wj, seed = args
    return i, j, play(wi, wj, seed)


def fitness(population, generation, pool):
    """Round robin: each pair plays twice (both colours) from an opening
    that depends on the generation and the pair."""
    games = []
    for k, (i, j) in enumerate(combinations(range(len(population)), 2)):
        seed = 1000 * generation + k
        games.append((i, j, population[i], population[j], seed))
        games.append((j, i, population[j], population[i], seed))
    points = [0.0] * len(population)
    played = [0] * len(population)
    for black, white, result in pool.imap_unordered(_game, games):
        points[black] += result
        points[white] += 1 - result
        played[black] += 1
        played[white] += 1
    return [p / n for p, n in zip(points, played)]


def tournament(population, scores, rng):
    """Best of TOURNAMENT_K random individuals."""
    chosen = rng.sample(range(len(population)), TOURNAMENT_K)
    return population[max(chosen, key=lambda i: scores[i])]


def crossover(x, y, rng):
    """Arithmetic recombination of two parents."""
    a = rng.random()
    child1 = [a * xi + (1 - a) * yi for xi, yi in zip(x, y)]
    child2 = [a * yi + (1 - a) * xi for xi, yi in zip(x, y)]
    return child1, child2


def mutate(individual, rng):
    """Random reset of each gene with probability MUTATION_RATE."""
    return [rng.uniform(0, LIMITS[k]) if rng.random() < MUTATION_RATE else g
            for k, g in enumerate(individual)]


def initial_population(rng):
    population = [list(HAND)]
    while len(population) < POPULATION:
        population.append([w * rng.uniform(0.5, 1.5) for w in HAND])
    return population


def evolve(generations=GENERATIONS, size=POPULATION):
    global POPULATION
    POPULATION = size
    rng = random.Random(SEED)
    population = initial_population(rng)
    with Pool() as pool, open("genetic_log.csv", "w", newline="") as f:
        log = csv.writer(f)
        log.writerow(["generation", "best_fitness", "mean_fitness", "seconds"]
                     + evaluation.FEATURE_NAMES)
        for gen in range(generations):
            start = time.perf_counter()
            scores = fitness(population, gen, pool)
            order = sorted(range(len(population)), key=lambda i: -scores[i])
            best = population[order[0]]
            mean = sum(scores) / len(scores)
            seconds = time.perf_counter() - start
            log.writerow([gen, f"{scores[order[0]]:.3f}", f"{mean:.3f}",
                          f"{seconds:.0f}"] + [f"{w:.1f}" for w in best])
            f.flush()
            print(f"generation {gen}: best {scores[order[0]]:.3f}, "
                  f"mean {mean:.3f}, {seconds:.0f} s, weights "
                  + ", ".join(f"{w:.1f}" for w in best), flush=True)
            if gen == generations - 1:
                return best
            # Replacement: the elite survives, offspring fill the rest.
            new = [population[i] for i in order[:ELITE]]
            while len(new) < len(population):
                x = tournament(population, scores, rng)
                y = tournament(population, scores, rng)
                for child in crossover(x, y, rng):
                    if len(new) < len(population):
                        new.append(mutate(child, rng))
            population = new


def validate():
    """Best individual of each generation vs the hand weights on new
    openings (seeds from 100000, never used in the evolution)."""
    with open("genetic_log.csv") as f:
        rows = list(csv.DictReader(f))
    with Pool() as pool, open("genetic_validation.csv", "w", newline="") as out:
        log = csv.writer(out)
        log.writerow(["generation", "score_vs_hand"] + evaluation.FEATURE_NAMES)
        results = []
        for row in rows:
            weights = [float(row[name]) for name in evaluation.FEATURE_NAMES]
            games = []
            for k in range(VALIDATION_OPENINGS):
                seed = 100000 + k
                games.append((0, 1, weights, HAND, seed))   # candidate Black
                games.append((1, 0, HAND, weights, seed))   # candidate White
            points = 0.0
            for black, _, result in pool.imap_unordered(_game, games):
                points += result if black == 0 else 1 - result
            score = points / len(games)
            results.append((score, int(row["generation"]), weights))
            log.writerow([row["generation"], f"{score:.3f}"]
                         + [f"{w:.1f}" for w in weights])
            print(f"generation {row['generation']}: {score:.3f} against the "
                  f"hand weights, weights {weights}", flush=True)
    score, gen, weights = max(results)
    print()
    print(f"Best: generation {gen}, {score:.3f} against the hand weights")
    print("Weights:", weights)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        validate()
        sys.exit()
    generations = int(sys.argv[1]) if len(sys.argv) > 1 else GENERATIONS
    size = int(sys.argv[2]) if len(sys.argv) > 2 else POPULATION
    best = evolve(generations, size)
    print()
    print("Best weights:", [round(w, 1) for w in best])
    print("Copy them into LEARNED_WEIGHTS in evaluation.py")
