"""Ensure every published photo reference resolves to a bundled local asset."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = []

def walk(value):
    if isinstance(value, dict):
        src = value.get("src")
        if isinstance(src, str) and "static/places" in src:
            records.append(src)
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)

for relative in ("data/reference/places.json", "data/reference/project_media.json"):
    walk(json.loads((ROOT / relative).read_text(encoding="utf-8")))

missing = [src for src in records if not (ROOT / "static/places" / Path(src).name).is_file()]
assert len(records) == 167, len(records)
assert not missing, missing
print({"referenced": len(records), "missing": missing, "checks": "passed"})
