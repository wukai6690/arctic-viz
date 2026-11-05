"""Evidence-bounded comparison engine for the Arctic route decision prototype."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ROUTE_GEOJSON = ROOT / "geojson" / "arctic_routes.geojson"
DECISION_DIR = ROOT / "data" / "decision"
REGIONAL_PATH = ROOT / "data" / "analysis" / "regional_ice.json"


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    catalog = json.loads((DECISION_DIR / "route_metrics.json").read_text(encoding="utf-8"))
    geojson = json.loads(ROUTE_GEOJSON.read_text(encoding="utf-8"))
    features = {}
    for feature in geojson.get("features", []):
        properties = feature.get("properties", {})
        route_id = {
            "东北航道": "nsr",
            "西北航道": "nwp",
            "中央航道": "transpolar",
        }.get(properties.get("name"))
        if route_id:
            features[route_id] = feature
    for route in catalog["routes"]:
        route["feature"] = features.get(route["route_id"], {})
    return catalog


@lru_cache(maxsize=1)
def regional_frame() -> pd.DataFrame:
    payload = json.loads(REGIONAL_PATH.read_text(encoding="utf-8"))
    return pd.DataFrame(payload.get("records", []))


def decision_years() -> list[int]:
    frame = regional_frame()
    years = sorted(int(value) for value in frame["year"].dropna().unique())
    return [year for year in years if 2016 <= year <= 2025] or years


def _normalise(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    low = min(values.values())
    high = max(values.values())
    if high - low < 1e-9:
        return {key: 0.5 for key in values}
    return {key: (value - low) / (high - low) for key, value in values.items()}


def normalise_weights(weights: dict[str, float] | None) -> dict[str, float]:
    base = {
        "safety": 0.4,
        "distance": 0.25,
        "data": 0.2,
        "service": 0.15,
    }
    if weights:
        for key in base:
            if key in weights:
                base[key] = max(0.0, float(weights[key]))
    total = sum(base.values())
    return {key: value / total for key, value in base.items()} if total else base


def vessel_profile(vessel_id: str) -> dict[str, Any]:
    for vessel in load_catalog()["vessels"]:
        if vessel["id"] == vessel_id:
            return vessel
    return load_catalog()["vessels"][0]


def _region_exposure(region_id: str, year: int, month: int) -> tuple[float | None, bool, str]:
    frame = regional_frame()
    rows = frame[(frame["region_id"] == region_id) & (frame["month"] == int(month))].copy()
    rows["extent_km2"] = pd.to_numeric(rows["extent_km2"], errors="coerce")
    rows = rows.dropna(subset=["extent_km2"])
    if rows.empty:
        return None, True, "该关联海区没有可用的月度记录"
    selected = rows[rows["year"] == int(year)]
    fallback = selected.empty
    row = selected.iloc[0] if not selected.empty else rows.iloc[-1]
    value = float(row["extent_km2"])
    low = float(rows["extent_km2"].min())
    high = float(rows["extent_km2"].max())
    exposure = 0.5 if high - low < 1e-9 else (value - low) / (high - low)
    used_year = int(row["year"])
    note = f"{region_id} {used_year}-{int(month):02d} 月度海冰范围"
    if fallback:
        note += "，所选年份缺失，使用该月最近记录"
    return max(0.0, min(1.0, exposure)), fallback, note


def _route_ice(route: dict[str, Any], year: int, month: int) -> dict[str, Any]:
    values: list[float] = []
    notes: list[str] = []
    fallbacks = 0
    for region_id in route.get("evidence_regions", []):
        value, fallback, note = _region_exposure(region_id, year, month)
        if value is not None:
            values.append(value)
            notes.append(note)
        if fallback:
            fallbacks += 1
    if values:
        regional_value = sum(values) / len(values)
        exposure = 0.72 * regional_value + 0.28 * float(route.get("ice_prior", regional_value))
        source_kind = "区域海冰记录与方案先验"
    else:
        exposure = float(route.get("ice_prior", 0.8))
        source_kind = "方案先验，缺少关联区域记录"
        notes.append("中央航道没有对应的区域海冰记录")
    season_penalty = 0.0 if int(month) in route.get("open_months", []) else 0.55
    if int(month) not in route.get("open_months", []):
        notes.append("所选月份不在资料中列出的主要通航月份内")
    return {
        "ice_exposure": max(0.0, min(1.0, exposure)),
        "season_penalty": season_penalty,
        "notes": notes,
        "source_kind": source_kind,
        "fallback_count": fallbacks,
    }


def calculate_decision(year: int, month: int, vessel_id: str, weights: dict[str, float] | None = None) -> dict[str, Any]:
    weights = normalise_weights(weights)
    vessel = vessel_profile(vessel_id)
    routes = load_catalog()["routes"]
    distance_norm = _normalise({route["route_id"]: float(route["distance_nm"]) for route in routes})
    rows: list[dict[str, Any]] = []
    for route in routes:
        ice = _route_ice(route, year, month)
        safety = min(1.0, (0.78 * ice["ice_exposure"] + 0.22 * ice["season_penalty"]) * float(vessel["ice_factor"]))
        data_penalty = 1.0 - float(route["data_coverage"])
        service_penalty = min(1.0, (1.0 - float(route["service_index"])) * float(vessel["service_factor"]))
        contributions = {
            "safety": weights["safety"] * safety,
            "distance": weights["distance"] * distance_norm[route["route_id"]],
            "data": weights["data"] * data_penalty,
            "service": weights["service"] * service_penalty,
        }
        total = sum(contributions.values())
        confidence = max(0.0, min(1.0, float(route["data_coverage"]) * (1.0 - 0.25 * ice["fallback_count"])))
        rows.append({
            "route_id": route["route_id"],
            "name": route["name"],
            "name_en": route["name_en"],
            "distance_nm": float(route["distance_nm"]),
            "distance_norm": distance_norm[route["route_id"]],
            "ice_exposure": ice["ice_exposure"],
            "season_penalty": ice["season_penalty"],
            "data_coverage": float(route["data_coverage"]),
            "service_index": float(route["service_index"]),
            "safety_cost": safety,
            "data_penalty": data_penalty,
            "service_penalty": service_penalty,
            "contributions": contributions,
            "total_cost": total,
            "confidence": confidence,
            "confidence_label": "较高" if confidence >= 0.72 else "中等" if confidence >= 0.48 else "较低",
            "evidence_regions": route.get("evidence_regions", []),
            "evidence_notes": ice["notes"],
            "source_kind": ice["source_kind"],
            "limits": route["limits"],
            "service_note": route["service_note"],
            "feature": route.get("feature", {}),
        })
    rows.sort(key=lambda row: (row["total_cost"], -row["confidence"]))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
        row["reasons"] = _reasons(row, weights)
    return {
        "version": load_catalog()["version"],
        "year": int(year),
        "month": int(month),
        "vessel_id": vessel["id"],
        "vessel_name": vessel["name"],
        "weights": weights,
        "routes": rows,
        "recommendation": rows[0]["route_id"],
        "recommendation_name": rows[0]["name"],
        "method_note": "综合成本越低表示在当前偏好和资料条件下越适合作为比较方案。结果是研究原型输出，不替代实时航海决策。",
    }


def _reasons(row: dict[str, Any], weights: dict[str, float]) -> list[str]:
    contributions = row["contributions"]
    strongest = sorted(contributions, key=contributions.get, reverse=True)[:2]
    labels = {"safety": "海冰与季节适配", "distance": "相对航程", "data": "资料覆盖", "service": "服务节点"}
    reasons = [f"{labels[key]}对当前综合成本的影响最大" for key in strongest]
    if row["confidence"] < 0.48:
        reasons.append("资料覆盖有限，建议把结果作为待核查方案")
    elif row["confidence"] >= 0.72:
        reasons.append("关联资料覆盖相对完整，结果可追溯性较好")
    return reasons


def route_geometry(result: dict[str, Any]) -> list[tuple[str, str, list[float], list[float], str]]:
    output = []
    for row in result["routes"]:
        geometry = row.get("feature", {}).get("geometry", {})
        coordinates = geometry.get("coordinates", [])
        if geometry.get("type") != "LineString" or not coordinates:
            continue
        output.append((row["route_id"], row["name"], [point[1] for point in coordinates], [point[0] for point in coordinates], row.get("feature", {}).get("properties", {}).get("color", "#497b6a")))
    return output
