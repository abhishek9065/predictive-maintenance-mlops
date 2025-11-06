"""
Quick Data Inspection
"""
import json
from pathlib import Path

data_files = list(Path("data/raw").glob("historical_*.json"))
with open(data_files[0], 'r') as f:
    data = json.load(f)

# Print first record structure
print("First Record:")
print(json.dumps(data[0], indent=2))
