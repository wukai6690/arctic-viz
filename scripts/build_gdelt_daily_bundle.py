"""Bundle compact daily GDELT pair files into one deployable gzip stream."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/analysis/gdelt/network/daily"
TARGET = ROOT / "data/analysis/gdelt/network/daily_edges.json.gz"


def main() -> None:
    files = sorted(SOURCE.glob("*.json"))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with gzip.open(TARGET, "wt", encoding="utf-8", compresslevel=9) as handle:
        for path in files:
            package = json.loads(path.read_text(encoding="utf-8"))
            if package.get("filter_version") != "arctic-bilateral-daily-v1":
                continue
            handle.write(json.dumps(package, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")
            count += 1
    print(json.dumps({"output": str(TARGET), "days": count, "bytes": TARGET.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
