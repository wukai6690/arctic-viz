"""Import the team's confirmed 871-row patent export alongside the original 66 records."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"D:\r\patent_supplement\patents_confirmed_871.csv")
TARGET = ROOT / "data/analysis/patents/patents.json"
SOURCE_COPY = ROOT / "data/analysis/patents/patents_confirmed_871.csv"


def split_list(value: str) -> list[str]:
    return [item.strip() for item in (value or "").replace("；", ";").split(";") if item.strip()]


def csv_record(row: dict[str, str]) -> dict:
    publication = row.get("publication_number", "").strip()
    title = row.get("title", "").strip()
    abstract = row.get("abstract_original", "").strip()
    return {
        "publication_number": publication,
        "technology": row.get("technology", "").strip() or row.get("preliminary_categories", "").strip() or "未分类",
        "source_url": row.get("source_url", "").strip() or f"https://patents.google.com/patent/{publication}",
        "title": title,
        "title_zh": row.get("title_zh", "").strip(),
        "country": row.get("country", "").strip(),
        "assignee": row.get("assignee", "").strip(),
        "inventors": split_list(row.get("inventors", "")),
        "priority_date": row.get("priority_date", "").strip(),
        "filing_date": row.get("filing_date", "").strip(),
        "publication_date": row.get("publication_date", "").strip(),
        "application_number": row.get("application_number", "").strip(),
        "status": row.get("status", "").strip(),
        "classifications": split_list(row.get("classifications", "")),
        "abstract_original": abstract,
        "abstract_zh": row.get("abstract_zh", "").strip(),
        "abstract_zh_source": row.get("abstract_zh_source", "").strip(),
        "claim_1": row.get("claim_1", "").strip(),
        "family_hint": row.get("family_hint", "").strip(),
        "verification_status": row.get("verification_status", "已核验").strip() or "已核验",
        "verification_note": row.get("verification_note", "").strip(),
        "preliminary_categories": row.get("preliminary_categories", "").strip(),
        "screening_note": row.get("screening_note", "").strip(),
        "source_file_row": row.get("source_file_row", "").strip(),
        "data_quality_note": row.get("data_quality_note", "").strip(),
        "key_information": row.get("key_information", "").strip(),
    }


def main() -> None:
    existing = json.loads(TARGET.read_text(encoding="utf-8"))
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        imported = [csv_record(row) for row in csv.DictReader(f) if row.get("publication_number")]
    by_id = {record["publication_number"]: record for record in existing.get("records", [])}
    for record in imported:
        current = by_id.get(record["publication_number"])
        if current is None:
            by_id[record["publication_number"]] = record
            continue
        # Keep the richer existing 66-row detail wherever the two exports overlap.
        for key, value in record.items():
            if not current.get(key) and value:
                current[key] = value
    records = sorted(by_id.values(), key=lambda r: (r.get("publication_date") or "0000-00-00", r["publication_number"]), reverse=True)
    merged = dict(existing)
    merged.update({
        "version": "confirmed-937",
        "generated_at": "2026-10-23",
        "source_note": "66 条原始详情记录与团队已核验的 871 条补充记录合并；保留每条公开文本的来源链接和字段缺失状态。",
        "verification_note": "补充 871 条来自项目组确认导入；网站不把缺失公开日、申请人、族号或摘要字段改写为推测值。",
        "records": records,
    })
    TARGET.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    SOURCE_COPY.write_bytes(SOURCE.read_bytes())
    print(json.dumps({"imported": len(imported), "merged": len(records), "target": str(TARGET)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
