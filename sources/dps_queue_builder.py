"""dps_queue_builder.py
目的: DPS スコア降順にソートした priority_queue.jsonl を生成する。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


def build_priority_queue(
    records: List[dict],
    output_path: Path = Path("priority_queue.jsonl"),
) -> Path:
    """records を dps_score 降順でソートして JSONL に書き出し、パスを返す。"""
    sorted_records = sorted(records, key=lambda r: r["dps_score"], reverse=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for rank, rec in enumerate(sorted_records, start=1):
            entry = {
                "rank": rank,
                "source_path": rec["source_path"],
                "dps_score": rec["dps_score"],
                "year_slot": rec["year_slot"],
            }
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return output_path
