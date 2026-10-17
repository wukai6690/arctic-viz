"""Data and page checks for the standalone patent database."""
import json
import os
import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
package = json.loads((ROOT / "data/analysis/patents/patents.json").read_text(encoding="utf-8"))
records = package["records"]
assert len(records) >= 60
assert len({r["publication_number"] for r in records}) == len(records)
assert all(r["source_url"].startswith("https://patents.google.com/patent/") for r in records)
assert sum(bool(r.get("abstract_zh")) for r in records) >= 25
assert {r["technology"] for r in records} >= {"冰区航线规划", "冰区船舶/破冰技术"}

app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
assert not app.exception
app.switch_page("pages/16_patents.py").run()
assert not app.exception
assert len(app.get("plotly_chart")) == 3
assert any("匹配公开文本" in str(item.label) for item in app.metric)
print({"records": len(records), "abstracts_zh": sum(bool(r.get("abstract_zh")) for r in records), "page": "passed"})
