"""
generate_win_probabilities.py

For a given chess position (FEN), evaluates every legal move using Stockfish,
converts the raw engine evaluation into a win probability, and then applies
a rating-band adjustment derived from the empirical rating-conversion curve
found earlier in the project (win rate of the favored player, by rating band,
from the Lichess dataset).

This is the core "move -> win %" engine behind the live demo.

Requirements:
    pip install python-chess
    Stockfish installed and on PATH (macOS: brew install stockfish)

Usage:
    python generate_win_probabilities.py
"""

import json
import chess
import chess.engine
import math

# ---------------------------------------------------------------------------
# 1. Real, fitted calibration table: P(White wins | eval bucket, rating band),
#    computed directly from ~765,000 evaluated Lichess games (2016-06),
#    exploded to one row per move and grouped by evaluation bucket and the
#    higher-rated player's rating band. This replaces the earlier uniform
#    scaling approximation with actual empirical data.
# ---------------------------------------------------------------------------
RATING_BANDS = ["<1200", "1200-1600", "1600-2000", "2000-2400", "2400+"]

# Bucket boundaries in centipawns, matching the PySpark bucketing logic.
EVAL_BUCKETS = [
    (float("-inf"), -500, "< -500"),
    (-500, -300, "-500 to -300"),
    (-300, -100, "-300 to -100"),
    (-100, 100, "-100 to +100"),
    (100, 300, "+100 to +300"),
    (300, 500, "+300 to +500"),
    (500, float("inf"), "> +500"),
]

# White win % (0-100) for each (eval_bucket, rating_band).
# Loaded from calibration_table.csv, which is exported directly from the
# Databricks notebook (see the toPandas().to_csv(...) cell in that notebook)
# - this is the real link between the big-data analysis and this live demo.
# A fallback table is used only if the CSV isn't found, so the script still
# runs for testing without needing Databricks access every time.
import os
import csv as _csv

CALIBRATION_CSV_PATH = "calibration_table.csv"

_FALLBACK_CALIBRATION_TABLE = {
    ("< -500", "<1200"): 20.2, ("< -500", "1200-1600"): 15.8, ("< -500", "1600-2000"): 13.4,
    ("< -500", "2000-2400"): 9.9, ("< -500", "2400+"): 8.2,
    ("-500 to -300", "<1200"): 35.5, ("-500 to -300", "1200-1600"): 29.7, ("-500 to -300", "1600-2000"): 25.2,
    ("-500 to -300", "2000-2400"): 19.3, ("-500 to -300", "2400+"): 14.6,
    ("-300 to -100", "<1200"): 40.1, ("-300 to -100", "1200-1600"): 36.3, ("-300 to -100", "1600-2000"): 32.4,
    ("-300 to -100", "2000-2400"): 26.7, ("-300 to -100", "2400+"): 21.3,
    ("-100 to +100", "<1200"): 47.6, ("-100 to +100", "1200-1600"): 48.3, ("-100 to +100", "1600-2000"): 47.7,
    ("-100 to +100", "2000-2400"): 46.9, ("-100 to +100", "2400+"): 45.3,
    ("+100 to +300", "<1200"): 56.5, ("+100 to +300", "1200-1600"): 60.2, ("+100 to +300", "1600-2000"): 63.1,
    ("+100 to +300", "2000-2400"): 67.6, ("+100 to +300", "2400+"): 70.1,
    ("+300 to +500", "<1200"): 60.9, ("+300 to +500", "1200-1600"): 67.3, ("+300 to +500", "1600-2000"): 71.3,
    ("+300 to +500", "2000-2400"): 77.5, ("+300 to +500", "2400+"): 81.3,
    ("> +500", "<1200"): 76.3, ("> +500", "1200-1600"): 81.1, ("> +500", "1600-2000"): 84.1,
    ("> +500", "2000-2400"): 87.8, ("> +500", "2400+"): 87.7,
}


def load_calibration_table(path: str = CALIBRATION_CSV_PATH) -> dict:
    """
    Reads the calibration table exported from Databricks. Expected columns:
    eval_bucket, rating_band, avg(white_won) - the same shape produced by
    calibration_table.show() / calibration_table.toPandas().to_csv(...).
    Falls back to the last-known table if the file isn't present yet.
    """
    if not os.path.exists(path):
        print(f"[info] {path} not found - using fallback calibration values. "
              f"Export the table from Databricks and place it next to this script to use live data.")
        return _FALLBACK_CALIBRATION_TABLE

    table = {}
    with open(path, newline="") as f:
        reader = _csv.DictReader(f)
        win_col = next(c for c in reader.fieldnames if "white_won" in c.lower())
        for row in reader:
            bucket = row["eval_bucket"]
            band = row["rating_band"]
            win_pct = float(row[win_col]) * 100  # Spark's avg() returns a 0-1 fraction
            table[(bucket, band)] = round(win_pct, 1)

    print(f"[info] Loaded live calibration table from {path} ({len(table)} entries).")
    return table


CALIBRATION_TABLE = load_calibration_table()


def centipawns_to_win_pct(centipawns: float) -> float:
    """
    Standard centipawn -> win probability conversion, the same logistic
    formula used by Lichess's own analysis board. Kept here for reference
    and as a fallback; the calibration table above is now the primary
    source of truth for the demo.
    Returns White's win probability as a percentage (0-100).
    """
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * centipawns)) - 1)


def get_eval_bucket(centipawns: float) -> str:
    """Maps a raw centipawn value to the matching calibration bucket label."""
    for low, high, label in EVAL_BUCKETS:
        if low <= centipawns < high:
            return label
    return "> +500"  # fallback for +inf edge case


def apply_band_adjustment(raw_win_pct: float, band: str, centipawns: float) -> float:
    """
    Looks up White's real, empirically observed win % for this exact
    (eval bucket, rating band) combination, instead of applying a uniform
    scaling factor to the engine's raw estimate.

    Note: the calibration table gives White's win %. If the position being
    evaluated is from Black's perspective (i.e. we're scoring a move Black
    is considering), the caller is responsible for flipping this value
    (100 - value) - see generate_move_data() below.
    """
    bucket = get_eval_bucket(centipawns)
    return CALIBRATION_TABLE.get((bucket, band), raw_win_pct)


def evaluate_position(engine, board: chess.Board, depth: int = 14) -> float:
    """Returns Stockfish's centipawn evaluation from White's perspective."""
    info = engine.analyse(board, chess.engine.Limit(depth=depth))
    score = info["score"].white()
    if score.is_mate():
        # Treat mate as a very large centipawn value in the winning direction
        mate_in = score.mate()
        return 10000 if mate_in > 0 else -10000
    return score.score()


def generate_move_data(fen: str, engine_path: str = "stockfish", depth: int = 14) -> dict:
    """
    For every legal move in the given position, evaluate the resulting
    position and return win% (raw) plus win% adjusted for every rating band.
    """
    board = chess.Board(fen)
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)

    results = []
    try:
        for move in board.legal_moves:
            board.push(move)
            cp = evaluate_position(engine, board, depth=depth)
            board.pop()

            raw_win_pct = centipawns_to_win_pct(cp)

            # The calibration table stores White's win % for a given
            # (eval bucket, rating band). Look it up using the raw
            # centipawn value (from White's perspective, as Stockfish
            # returns it), then flip to the mover's perspective if needed.
            band_adjusted = {}
            for band in RATING_BANDS:
                white_win_pct = apply_band_adjustment(raw_win_pct, band, cp)
                mover_pct = white_win_pct if board.turn == chess.WHITE else (100 - white_win_pct)
                band_adjusted[band] = round(mover_pct, 1)

            # Keep a mover-perspective raw % too, for the "raw_win_pct" field below
            mover_win_pct = raw_win_pct if board.turn == chess.WHITE else (100 - raw_win_pct)

            results.append({
                "move_san": board.san(move) if False else None,  # filled below
                "move_uci": move.uci(),
                "centipawns": cp,
                "raw_win_pct": round(mover_win_pct, 1),
                "band_adjusted_win_pct": band_adjusted,
            })
    finally:
        engine.quit()

    # fill in SAN notation (needs move object + board before push)
    board = chess.Board(fen)
    for r, move in zip(results, board.legal_moves):
        r["move_san"] = board.san(move)

    results.sort(key=lambda r: r["raw_win_pct"], reverse=True)
    return {"fen": fen, "side_to_move": "white" if board.turn == chess.WHITE else "black", "moves": results}


if __name__ == "__main__":
    # Starting position - swap this FEN for any position you want to demo
    START_FEN = chess.STARTING_FEN

    # On macOS after `brew install stockfish`, "stockfish" resolves on PATH.
    # If you get a "file not found" error, run `which stockfish` in Terminal
    # and paste the full path here instead.
    ENGINE_PATH = "stockfish"

    print("Evaluating all legal moves from the starting position...")
    data = generate_move_data(START_FEN, engine_path=ENGINE_PATH, depth=14)

    with open("win_probabilities.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"Done. Evaluated {len(data['moves'])} moves.")
    print(f"Top 3 moves by win%: {[m['move_san'] for m in data['moves'][:3]]}")
    print("Saved to win_probabilities.json")