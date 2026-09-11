# Rating-Aware Chess Analytics

A Big Data Analytics project analyzing 6.1 million real Lichess games to
answer three questions: does a rating advantage convert into a win equally
reliably at every skill level, are there distinct categories of games that
call for different coaching, and can outcomes be predicted from game
metadata. Built on Databricks/PySpark, with a live, rating-aware interactive
chess demo powered by Stockfish.

## Project Structure
├── Notebooks/
│ └── chess_data_engineering_databricks.ipynb # Full Databricks pipeline: cleaning, feature engineering, ML
├── data-pipeline/
│ ├── extract.py # Parses raw Lichess PGN into structured game metadata
│ └── extract_evaluated_games.py # Extracts the subset of games with Stockfish evaluations
├── live-demo/
│ ├── win_probability_live.html # Interactive, playable chessboard with live win %
│ ├── stockfish.js # Chess engine (runs in-browser via WebAssembly)
│ ├── calibration_table.csv # Exported from Databricks: win % by eval bucket & rating band
│ ├── opening_stats.csv # Exported from Databricks: opening popularity & win rate by band
│ ├── GenerateWinProbs.py # Generates win-probability data for a given board position
│ ├── update_demo_html.py # Re-embeds fresh data into the static demo HTML
│ └── win_probabilities.json # Sample output
└── reports/
├── Chess_Analytics_Consulting_Report.docx # Full written report
└── Chess_Analytics_Presentation.pptx # Executive slide deck
