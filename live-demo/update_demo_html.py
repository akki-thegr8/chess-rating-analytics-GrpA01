"""
update_demo_html.py

Re-embeds the current contents of win_probabilities.json into
win_probability_demo.html, replacing whatever data was baked in before.

Run this any time after regenerating win_probabilities.json with a new
position, to refresh the visual demo without rebuilding the whole HTML file.

Usage:
    python3 update_demo_html.py
"""

import json
import re

JSON_PATH = "win_probabilities.json"
HTML_PATH = "win_probability_demo.html"

with open(JSON_PATH) as f:
    data = json.load(f)

with open(HTML_PATH) as f:
    html = f.read()

new_data_line = f"const WIN_DATA = {json.dumps(data)};"

# Finds the existing "const WIN_DATA = {...};" line/block and swaps it out,
# no matter what data was in there before.
pattern = re.compile(r"const WIN_DATA = .*?;", re.DOTALL)
updated_html, count = pattern.subn(new_data_line, html)

if count == 0:
    print("Could not find the WIN_DATA block in the HTML file - no changes made.")
else:
    with open(HTML_PATH, "w") as f:
        f.write(updated_html)
    print(f"Updated {HTML_PATH} with {len(data['moves'])} moves from {JSON_PATH}.")