"""
extract_evaluated_games.py

Scans the full raw PGN file and pulls out ONLY the games that contain
Stockfish evaluation comments (the "[%eval ...]" tags Lichess adds when
a player requests computer analysis after a game).

Roughly 6% of games in a typical Lichess monthly archive have this data -
this script finds those and saves them, with their per-move evaluations,
to a much smaller CSV.

Why this matters for the project: this is the dataset that lets you
properly calibrate "engine evaluation + rating band -> actual win %"
instead of the simplified uniform scaling used in the live demo.

Usage:
    python extract_evaluated_games.py
"""

import re
import csv

INPUT_PATH = "lichess_db_standard_rated_2016-06.pgn"
OUTPUT_PATH = "lichess_2016-06_evaluated_games.csv"

header_re = re.compile(r'\[(\w+)\s+"(.*)"\]')
eval_re = re.compile(r'\[%eval\s+([#\-\d.]+)\]')

fields = [
    "white_elo", "black_elo", "result", "eco", "opening",
    "time_control", "num_evals", "evals"
]

with open(INPUT_PATH, encoding="utf-8", errors="ignore") as f, \
     open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as out:

    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()

    headers = {}
    total_games = 0
    evaluated_games = 0

    for line in f:
        line = line.strip()

        if line.startswith("["):
            # This is a header line, e.g. [WhiteElo "1800"]
            m = header_re.match(line)
            if m:
                headers[m.group(1)] = m.group(2)

        elif line == "":
            continue

        else:
            # This is the move-text line - the actual game, with any eval tags
            total_games += 1
            evals = eval_re.findall(line)

            if evals:
                # Only keep games that actually have evaluation data
                evaluated_games += 1
                writer.writerow({
                    "white_elo": headers.get("WhiteElo", ""),
                    "black_elo": headers.get("BlackElo", ""),
                    "result": headers.get("Result", ""),
                    "eco": headers.get("ECO", ""),
                    "opening": headers.get("Opening", ""),
                    "time_control": headers.get("TimeControl", ""),
                    "num_evals": len(evals),
                    "evals": ";".join(evals),  # e.g. "0.3;0.5;-0.2;#-4"
                })

            headers = {}
            if total_games % 500000 == 0:
                print(f"Scanned {total_games} games, found {evaluated_games} with evaluations...")

print(f"Done. Scanned {total_games} total games.")
print(f"Found {evaluated_games} evaluated games ({100 * evaluated_games / total_games:.1f}%).")
print(f"Saved to {OUTPUT_PATH}")