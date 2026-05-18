"""dps_record_writer.py
目的: Step 6 - 全中間値を .dps/ フォルダに保存する。
更新履歴:
  001 2026-05-15 初版
  002 2026-05-18 分析結果を中央の .dps/ ディレクトリに保存するよう変更
  003 2026-05-18 保存先ディレクトリを動的に指定可能に変更
  004 2026-05-18 source_path を外部から指定可能に変更（相対パス対応）
"""
from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def get_result_path(file_path: Path, result_dir: Path) -> Path:
    """ファイルパスのハッシュ値を元に、指定されたディレクトリ配下の保存先パスを生成する。"""
    if not result_dir.exists():
        result_dir.mkdir(parents=True, exist_ok=True)
    
    # 絶対パスを元にハッシュ化（ファイル名衝突回避のため）
    path_hash = hashlib.sha256(str(file_path.absolute()).encode()).hexdigest()
    return result_dir / f"{path_hash}.json"


def _calculate_file_hash(file_path: Path) -> str:
    """ファイルのコンテンツの SHA-256 ハッシュ値を計算する。"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return ""


def write_record(
    file_path: Path,
    result_dir: Path,
    meta: dict,
    year_slot: int,
    year_weight: float,
    time_decay: float,
    chunk_scores: list,
    s_topic_aggregated: float,
    dps_score: float,
    embed_model: str,
    source_path: str | None = None,
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
        "source_path": source_path if source_path is not None else str(file_path),
        "file_hash": _calculate_file_hash(file_path),
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
    out_path = get_result_path(file_path, result_dir)
    out_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path
