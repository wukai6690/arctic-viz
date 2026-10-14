"""Deterministic checks for the published GDELT Arctic network artifact."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.gdelt_network import load_network, network_figure, trend_figure

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "data/analysis/gdelt/network/network.json"
data = json.loads(path.read_text(encoding="utf-8"))
assert data["version"] == "gdelt-arctic-network-20261013-v1"
assert [w["id"] for w in data["windows"]] == ["2015", "2019", "2020", "2025"]
assert len(data["countries"]) == 9 and {"CHN", "USA", "RUS", "CAN", "NOR", "DNK", "FIN", "SWE", "ISL"} == {x["code"] for x in data["countries"]}
for window in data["windows"]:
    assert window["events"] and window["edges"]
    assert all(e["source"] != e["target"] for e in window["edges"])
    assert all(e["event_count"] >= 1 for e in window["edges"])
    assert all((not e["source_url"]) or isinstance(e["source_url"], str) for e in window["events"])
    assert sum(e["event_count"] for e in window["edges"]) == len(window["events"])
fig = network_figure(data["windows"][1], data["countries"])
assert len(fig.data) >= 2 and any(getattr(t, "mode", None) == "markers+text" for t in fig.data)
assert len(trend_figure(data).data) == 2
print(json.dumps({"version": data["version"], "windows": [(w["id"], len(w["events"]), len(w["edges"])) for w in data["windows"]], "checks": "passed"}, ensure_ascii=False))
