"""dps_record_writer.py
目的: Step 6 - 全中間値を 元ファイルパス+.json に保存する。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def write_record(
    file_path: Path,
    meta: dict,
    year_slot: int,
    year_weight: float,
    time_decay: float,
    chunk_scores: list,
    s_topic_aggregated: float,
    dps_score: float,
    embed_model: str,
) -> Path:
    """スコアリング結果を JSON ファイルに書き出してパスを返す。"""
    topics = list({
        c["top_prototype"]
        for c in chunk_scores
        if c["cos_sim"] >= 0.5
    })
    for c in chunk_scores:
        c["embedding_model"] = embed_model

    record = {
        "source_path": str(file_path),
        "scored_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dps_score": dps_score,
        "meta": meta,
        "year_slot": year_slot,
        "year_weight": year_weight,
        "time_decay": time_decay,
        "chunks": chunk_scores,
        "S_topic_aggregated": s_topic_aggregated,
        "topics_detected": topics,
    }
    out_path = Path(str(file_path) + ".json")
    out_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path
