"""Monthly aggregation must conserve daily counts; 3D nodes track event totals."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.gdelt_network import load_network, monthly_windows, _compact_daily_packages, network_3d_figure, _window_event_count
from src.bilateral_background import load_background, background_figure

data = load_network()
windows = monthly_windows(data)
assert len(windows) == 120
assert sum(_window_event_count(w) for w in windows) == sum(e['event_count'] for p in _compact_daily_packages() for e in p['edges'])
may = next(w for w in windows if w['label']=='2017-05')
assert len(may['observed_days']) == 31 and not may['fallback_months']
assert _window_event_count(may) > 358
assert sum(n['event_degree'] for n in may['nodes']) == 2*_window_event_count(may)
fig = network_3d_figure(may, data['countries'])
node = fig.data[-1]
assert node.type=='scatter3d' and len(node.x)==9 and len(set(node.z))>1
counts_sizes = sorted(zip([n['event_degree'] for n in may['nodes']], node.marker.size))
assert all(b[1]>=a[1] for a,b in zip(counts_sizes, counts_sizes[1:]))
assert len(set(node.marker.size))>1
june = next(w for w in windows if w['label']=='2025-06')
assert len(june['observed_days'])==13 and june['expected_days']==30
rows=load_background()[('CHN','USA')]
trend=background_figure(rows)
missing=[i for i,r in enumerate(rows) if r['source_file_available']=='0']
assert len(missing)==20 and all(trend.data[0].y[i] is None for i in missing)
assert all(t.connectgaps is False for t in trend.data)
assert not any('GRL' in pair for pair in load_background())
print({'months':len(windows), 'may_2017_events':_window_event_count(may), 'node_sizes':list(node.marker.size), 'checks':'passed'})
