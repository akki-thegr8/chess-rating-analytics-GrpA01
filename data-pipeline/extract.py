import re
import csv

input_path = "lichess_db_standard_rated_2016-06.pgn"
output_path = "lichess_2016-06_parsed.csv"

fields = [
    "white_elo", "black_elo", "eco", "opening",
    "result", "num_moves", "time_control", "termination", "date"
]

header_re = re.compile(r'\[(\w+)\s+"(.*)"\]')
move_num_re = re.compile(r'\d+\.')

with open(input_path, encoding="utf-8", errors="ignore") as f, \
     open(output_path, "w", newline="", encoding="utf-8") as out:

    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()

    headers = {}
    count = 0
    for line in f:
        line = line.strip()
        if line.startswith("["):
            m = header_re.match(line)
            if m:
                headers[m.group(1)] = m.group(2)
        elif line == "":
            continue
        else:
            # this is the movetext line
            num_moves = len(move_num_re.findall(line))
            writer.writerow({
                "white_elo": headers.get("WhiteElo", ""),
                "black_elo": headers.get("BlackElo", ""),
                "eco": headers.get("ECO", ""),
                "opening": headers.get("Opening", ""),
                "result": headers.get("Result", ""),
                "num_moves": num_moves,
                "time_control": headers.get("TimeControl", ""),
                "termination": headers.get("Termination", ""),
                "date": headers.get("UTCDate", ""),
            })
            headers = {}
            count += 1
            if count % 500000 == 0:
                print(f"Processed {count} games...")

print(f"Done. Total games: {count}")