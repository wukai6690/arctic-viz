"""Checks for the visible GDELT event search and filtered network aggregation."""
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.gdelt_network import EVENT_TYPES, aggregate_events, all_events, fetch_web_article, load_network, search_events  # noqa: E402

data = load_network()
events = all_events(data)
assert len(events) >= 1000
assert min(row["date"] for row in events) <= "2015-09-15" <= max(row["date"] for row in events)

all_types = list(EVENT_TYPES)
rows = search_events(data, date(2015, 9, 15), date(2015, 9, 15), "USA", "CHN", all_types)
assert rows and all(row["date"] == "2015-09-15" and row["actor1"] == "USA" and row["actor2"] == "CHN" for row in rows)

reverse = search_events(data, date(2015, 9, 15), date(2015, 9, 15), "CHN", "USA", all_types, ignore_direction=True)
assert len(reverse) >= len(rows)
edges, nodes = aggregate_events(reverse, data["countries"])
assert edges and any(edge["source"] == "CHN" and edge["target"] == "USA" for edge in edges)
assert len(nodes) == len(data["countries"])

only_conflict = search_events(data, date(2015, 9, 15), date(2015, 9, 15), "ALL", "ALL", ["18", "19", "20"])
assert all(str(row.get("event_code", ""))[:2] in {"18", "19", "20"} for row in only_conflict)
assert fetch_web_article("not-a-url")["status"] == "invalid"

print({"events": len(events), "usa_to_chn": len(rows), "undirected_chn_usa": len(reverse), "edges": len(edges), "checks": "passed"})
