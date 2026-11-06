Connect6 engine "mlb" - Practice 1, Tecnicas de Inteligencia Artificial
=======================================================================

REQUIREMENTS
------------
Python 3 (tested with 3.12). The engine only uses the standard library; the
only package in requirements.txt is PyInstaller, to build the executable.

BUILDING THE EXECUTABLE (Linux)
-------------------------------
From this folder (my_engine):

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pyinstaller --onefile --name mlb main.py
    deactivate

The executable is created at dist/mlb. Load it in the GUI (ConnectMore.py)
with "Load Black Engine" or "Load White Engine".

Without building it, the engine can also be run directly with:
    python3 main.py

TIME LIMIT
----------
The 'depth d' command sent by the GUI (Low = 4, Medium = 5, High = 6) is
taken as the time limit per turn in seconds; the engine uses 80% of it.
Without 'depth', it uses at most 20 seconds per move.

FILES
-----
Engine:       main.py (GUI protocol), board.py, moves.py, evaluation.py,
              search.py
Learning:     genetic.py (genetic algorithm of version 4),
              genetic_log.csv, genetic_validation.csv (its results)
Experiments:  test_evaluation.py, test_tactics.py, experiments.py,
              compare.py, match.py, measure_v1.py, measure_v2.py,
              measure_v5.py, vs_cloudict.py
The five versions of the engine are kept in the code; match.py selects one
by name (v1 ... v5). The engine plays version 5.
