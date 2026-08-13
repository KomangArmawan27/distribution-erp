import json
import sys
import urllib.request

BASE = "http://localhost:8000"

groups = json.load(urllib.request.urlopen(f"{BASE}/groups/?per_page=100"))["data"]
for g in groups:
    print(g["group_name"], g["group_noid"], g["group_value"])