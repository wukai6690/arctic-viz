"""Evidence-bounded Arctic route decision support prototype."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.presentation import ROOT, apply_presentation, section_title, show_chart
from src.route_decision_engine import (
    calculate_decision,
    decision_years,
    load_catalog,
    normalise_weights,
    route_geometry,
)

st.set_page_config(page_title="航线决策支持 · 北极观察", page_icon="◎", layout="wide")
apply_presentation("decision")


MONTHS = {1: "1月", 2: "2月", 3: "3月", 4: "4月", 5: "5月", 6: "6月", 7: "7月", 8: "8月", 9: "9月", 10: "10月", 11: "11月", 12: "12月"}
WEIGHT_LABELS = {"safety": "安全与海冰", "distance": "距离与效率", "data": "资料覆盖", "service": "服务支持"}


def decision_map(result: dict) -> go.Figure:
    figure = go.Figure()
    top_id = result["recommendation"]
    for route_id, name, latitudes, longitudes, color in route_geometry(result):
        row = next(row for row in result["routes"] if row["route_id"] == route_id)
        selected = route_id == top_id
        figure.add_trace(
            go.Scattergeo(
                lat=latitudes,
                lon=longitudes,
                mode="lines",
                name=f"{row['rank']} · {name}",
                line=dict(color=color, width=5 if selected else 2, dash="solid" if selected else "dot"),
                opacity=0.95 if selected else 0.62,
                hovertemplate=f"{name}<br>综合成本 {row['total_cost']:.3f}<br>海冰暴露 {row['ice_exposure']:.2f}<extra></extra>",
            )
        )
    figure.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=15, b=0),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        legend=dict(orientation="h", y=0.02, x=0.02, bgcolor="rgba(255,255,255,.85)"),
        geo=dict(
            projection_type="azimuthal equal area",
            projection_rotation=dict(lon=0, lat=90),
            center=dict(lon=0, lat=78),
            lataxis_range=[60, 90],
            showland=True,
            landcolor="#f1f4ed",
            showocean=True,
            oceancolor="#e4f1f4",
            showcountries=True,
            countrycolor="#b8cec7",
            coastlinecolor="#95b9c8",
            showlakes=True,
            lakecolor="#e4f1f4",
        ),
    )
    return figure


def route_table(result: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "排序": row["rank"],
                "方案": row["name"],
                "综合成本": round(row["total_cost"], 3),
                "相对航程 / 海里": int(row["distance_nm"]),
                "海冰暴露": f"{row['ice_exposure']:.2f}",
                "资料覆盖": f"{row['data_coverage']:.0%}",
                "服务支持": f"{row['service_index']:.0%}",
                "置信度": row["confidence_label"],
            }
            for row in result["routes"]
        ]
    )


def save_current_case(result: dict) -> None:
    history = st.session_state.setdefault("decision_history", [])
    case = {
        "id": f"session-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "name": f"当前方案 · {result['year']}-{result['month']:02d} · {result['vessel_name']}",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "year": result["year"],
        "month": result["month"],
        "vessel_id": result["vessel_id"],
        "vessel_name": result["vessel_name"],
        "weights": result["weights"],
        "recommendation": result["recommendation_name"],
        "routes": [{"name": row["name"], "total_cost": row["total_cost"], "rank": row["rank"]} for row in result["routes"]],
        "data_version": result["version"],
    }
    history.insert(0, case)
    st.session_state["decision_last_saved"] = case["id"]


def build_case_payload() -> str:
    builtin_path = ROOT / "data" / "decision" / "decision_cases.json"
    builtin = json.loads(builtin_path.read_text(encoding="utf-8")) if builtin_path.exists() else []
    session_cases = st.session_state.get("decision_history", [])
    return json.dumps({"builtin_cases": builtin, "session_cases": session_cases}, ensure_ascii=False, indent=2)


def sensitivity_figure(year: int, month: int, vessel_id: str, base_weights: dict[str, float]) -> go.Figure:
    rows = []
    for safety in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        remainder = 1.0 - safety
        weights = {
            "safety": safety,
            "distance": remainder * base_weights["distance"] / max(1e-9, 1.0 - base_weights["safety"]),
            "data": remainder * base_weights["data"] / max(1e-9, 1.0 - base_weights["safety"]),
            "service": remainder * base_weights["service"] / max(1e-9, 1.0 - base_weights["safety"]),
        }
        result = calculate_decision(year, month, vessel_id, weights)
        for row in result["routes"]:
            rows.append({"安全权重": safety, "方案": row["name"], "综合成本": row["total_cost"]})
    frame = pd.DataFrame(rows)
    figure = go.Figure()
    for name, subset in frame.groupby("方案"):
        figure.add_trace(go.Scatter(x=subset["安全权重"], y=subset["综合成本"], mode="lines+markers", name=name))
    figure.update_layout(
        height=370,
        margin=dict(l=20, r=20, t=30, b=30),
        xaxis_title="安全权重",
        yaxis_title="综合成本（越低越优）",
        legend=dict(orientation="h", y=1.12, x=0),
    )
    return figure


section_title(
    "DECISION SUPPORT",
    "北极航线决策支持",
    "在给定月份、船舶类型和决策偏好下，对三条参考航线进行可解释比较。",
)
st.markdown(
    '<div class="data-note"><b>使用边界</b><span>当前版本是基于公开月度海冰资料和站内证据的方案评估原型。综合成本用于比较当前场景下的相对优先级，不能替代实时冰情、海况、航海图或通航许可。</span></div>',
    unsafe_allow_html=True,
)

catalog = load_catalog()
years = decision_years()
vessel_options = {vessel["id"]: vessel for vessel in catalog["vessels"]}

left, center, right = st.columns([0.85, 1.7, 1.05], gap="large")
with left:
    st.markdown("**设置决策场景**")
    year = st.selectbox("分析年份", years, index=len(years) - 1, key="decision_year")
    month = st.selectbox("航行月份", list(MONTHS), format_func=lambda value: MONTHS[value], index=8, key="decision_month")
    vessel_id = st.selectbox("船舶类型", list(vessel_options), format_func=lambda value: vessel_options[value]["name"], key="decision_vessel")
    st.caption(vessel_options[vessel_id]["description"])
    st.markdown("**决策偏好**")
    safety = st.slider("安全与海冰", 0.0, 1.0, 0.45, 0.05, key="weight_safety")
    distance = st.slider("距离与效率", 0.0, 1.0, 0.25, 0.05, key="weight_distance")
    data = st.slider("资料覆盖", 0.0, 1.0, 0.15, 0.05, key="weight_data")
    service = st.slider("服务支持", 0.0, 1.0, 0.15, 0.05, key="weight_service")
    weights = normalise_weights({"safety": safety, "distance": distance, "data": data, "service": service})
    st.caption("权重会自动归一化。排序反映当前偏好，不代表真实事故概率。")

result = calculate_decision(year, month, vessel_id, weights)
with center:
    st.markdown("**候选航线与结果排序**")
    show_chart(decision_map(result), key="decision-route-map")
    st.caption("实线表示当前推荐方案，虚线表示备选方案。航线几何来自站内参考 GeoJSON。")
    st.dataframe(route_table(result), hide_index=True, width="stretch")

with right:
    winner = result["routes"][0]
    st.markdown("**当前推荐**")
    st.markdown(f'<div class="evidence-card"><small>RECOMMENDED ROUTE</small><h3>{winner["name"]}</h3><p>综合成本 {winner["total_cost"]:.3f} · 资料置信度 {winner["confidence_label"]}</p></div>', unsafe_allow_html=True)
    st.metric("海冰暴露", f"{winner['ice_exposure']:.2f}")
    st.metric("资料覆盖", f"{winner['data_coverage']:.0%}")
    st.metric("服务支持", f"{winner['service_index']:.0%}")
    st.markdown("**推荐理由**")
    for reason in winner["reasons"]:
        st.write("· " + reason)
    if st.button("保存当前决策案例", use_container_width=True, key="save-decision-case"):
        save_current_case(result)
        st.success("已保存到当前会话的案例库。")

evidence_tab, sensitivity_tab, case_tab = st.tabs(["证据链", "敏感性分析", "决策案例库"])
with evidence_tab:
    st.markdown("### 当前场景使用的证据")
    st.caption(f"数据版本 {result['version']} · {result['year']} 年 {result['month']} 月 · {result['vessel_name']}")
    for row in result["routes"]:
        with st.expander(f"{row['rank']} · {row['name']} · {row['confidence_label']} 置信度", expanded=row["rank"] == 1):
            st.write(f"方案说明。{row['service_note']}")
            st.write(f"海冰资料类型。{row['source_kind']}")
            if row["evidence_notes"]:
                st.write("海冰证据。" + "；".join(row["evidence_notes"]))
            st.write(f"资料覆盖。{row['data_coverage']:.0%}。服务支持。{row['service_index']:.0%}。")
            st.caption("资料边界。" + row["limits"])
    with st.expander("查看权重和计算口径"):
        st.json({"weights": result["weights"], "method": result["method_note"]})

with sensitivity_tab:
    st.markdown("### 安全偏好变化时的排序稳定性")
    st.caption("保持其他权重按当前比例重新分配，观察安全权重变化对综合成本的影响。")
    show_chart(sensitivity_figure(year, month, vessel_id, result["weights"]), key="decision-sensitivity")

with case_tab:
    st.markdown("### 案例库")
    builtin_path = ROOT / "data" / "decision" / "decision_cases.json"
    builtin_cases = json.loads(builtin_path.read_text(encoding="utf-8")) if builtin_path.exists() else []
    session_cases = st.session_state.get("decision_history", [])
    case_rows = []
    for case in [*builtin_cases, *session_cases]:
        case_rows.append({
            "案例": case["name"],
            "年份": case["year"],
            "月份": f"{int(case['month'])}月",
            "船型": case.get("vessel_name") or vessel_options.get(case.get("vessel_id"), {}).get("name", case.get("vessel_id", "")),
            "推荐方案": case.get("recommendation", "待运行"),
            "数据版本": case.get("data_version", result["version"]),
        })
    st.dataframe(pd.DataFrame(case_rows), hide_index=True, width="stretch")
    st.download_button("导出案例库 JSON", data=build_case_payload(), file_name="arctic_decision_cases.json", mime="application/json", use_container_width=True)
    st.caption("案例保存到当前会话。导出文件包含预设案例、当前会话案例、权重和结果排序。")

