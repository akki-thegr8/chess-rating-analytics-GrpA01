# Rating-Aware Chess Analytics

A Big Data Analytics project analyzing 6.1 million real Lichess games to
answer three questions: does a rating advantage convert into a win equally
reliably at every skill level, are there distinct categories of games that
call for different coaching, and can outcomes be predicted from game
metadata. Built on Databricks/PySpark, with a live, rating-aware interactive
chess demo powered by Stockfish.

## Project Structure

\`\`\`
Notebooks/
  chess_data_engineering_databricks.ipynb   - Full Databricks pipeline: cleaning, feature engineering, ML

data-pipeline/
  extract.py                                - Parses raw Lichess PGN into structured game metadata
  extract_evaluated_games.py                - Extracts the subset of games with Stockfish evaluations

live-demo/
  win_probability_live.html                 - Interactive, playable chessboard with live win %
  stockfish.js                              - Chess engine (runs in-browser via WebAssembly)
  calibration_table.csv                     - Exported from Databricks: win % by eval bucket & rating band
  opening_stats.csv                         - Exported from Databricks: opening popularity & win rate by band
  GenerateWinProbs.py                       - Generates win-probability data for a given board position
  update_demo_html.py                       - Re-embeds fresh data into the static demo HTML
  win_probabilities.json                    - Sample output

reports/
  Chess_Analytics_Consulting_Report.docx    - Full written report
  Chess_Analytics_Presentation.pptx         - Executive slide deck
\`\`\`


## Dataset

This project uses the Lichess open database (standard-rated games,
June 2016), available at https://database.lichess.org. The raw archive is
not included in this repository due to size (5+ GB uncompressed). To
reproduce the pipeline from scratch, download the June 2016 standard-rated
archive, place it in the project root, and run the scripts in
`data-pipeline/`.

## Running the Live Demo

1. Ensure `stockfish.js`, `calibration_table.csv`, and `opening_stats.csv`
   are in the same folder as `win_probability_live.html` (they fetch each
   other using relative paths).
2. From that folder, run a local server: python3 -m http.server 8000

3. Open `http://localhost:8000/win_probability_live.html` in a browser.

## Key Findings

- **Rating changes how advantages convert.** The favored player's win rate
  climbs from 65.8% (under 1200) to 78.8% (2400+).
- **Classification:** rating differential alone explains nearly all
  predictable signal in outcomes (naive baseline 63.20%, logistic
  regression 63.39%, random forest 63.01%).
- **Clustering:** four distinct playing-style archetypes emerged, including
  a cluster where 29% of games are lost to time management rather than
  chess skill.
- **Calibration curve:** built from 765,433 engine-evaluated games, showing
  an "hourglass" pattern — rating barely matters in balanced positions but
  strongly affects conversion at decisive ones.

## Tech Stack

Databricks, PySpark, Spark SQL, Spark MLlib, Python, Stockfish (WebAssembly),
chess.js, HTML/JS.

## Team — BA Group A01

| Name | Contribution |
|---|---|
| Manav Karia | Data Acquisition & Preprocessing |
| Arjun Bhatnagar | Data Engineering (Databricks/PySpark pipeline) |
| Sarvesha Bhatgare | Machine Learning — Classification |
| Aditi Chandra Yadav | Machine Learning — Clustering & Calibration |
| Akshat Rathod | Live Demo Development |
| Jasreen Kour Bagga | Business Analysis & Documentation |

## AI Usage Disclosure

Claude (Anthropic) was used as a coding and analysis assistant throughout
data engineering, modeling, and reporting. All code was reviewed by the
team, and all conclusions were verified against actual pipeline output.

