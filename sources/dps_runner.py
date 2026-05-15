"""dps_runner.py
目的: DPS 全体オーケストレーション。ファイルを巡回してスコアリングし、
      priority_queue.jsonl と dps_checkpoint.json を出力する。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from sources.dps_config_loader import load_config
from sources.dps_init import build_prototype_vecs
from sources.dps_meta_scorer import compute_meta_score
from sources.dps_year_classifier import extract_year, year_weight
from sources.dps_chunk_embedder import embed_file_chunks
from sources.dps_topic_scorer import compute_chunk_scores, temporal_decay
from sources.dps_aggregator import aggregate_dps
from sources.dps_record_writer import write_record
from sources.dps_queue_builder import build_priority_queue
from sources.dps_checkpoint import load_checkpoint, save_checkpoint, mark_complete


def _read_text(file_path: Path) -> str:
    """ファイルテキストを読み込んで返す。バイナリは空文字を返す。"""
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _walk_files(root: Path) -> List[Path]:
    """ルートディレクトリ以下の全ファイルパスを返す。"""
    return [p for p in root.rglob("*") if p.is_file()]


def run(root_dir: str) -> None:
    """DPS スコアリングを実行してキューとチェックポイントを書き出す。"""
    root = Path(root_dir)
    if not root.exists():
        print(f"ERROR: ディレクトリが見つからない: {root}", file=sys.stderr)
        raise SystemExit(1)

    cfg = load_config()
    checkpoint = load_checkpoint()
    already_scored = set(checkpoint.get("scored_paths", []))

    print("[DPS] プロトタイプベクトル生成中...")
    prototype_vecs = build_prototype_vecs(cfg)

    files = _walk_files(root)
    print(f"[DPS] 対象ファイル数: {len(files)}")

    all_records: List[dict] = []

    for fp in files:
        if str(fp) in already_scored:
            json_path = Path(str(fp) + ".json")
            if json_path.exists():
                import json
                rec = json.loads(json_path.read_text(encoding="utf-8"))
                all_records.append(rec)
                continue

        text = _read_text(fp)
        meta = compute_meta_score(fp, prototype_vecs, cfg)
        yr = extract_year(fp)
        yw = year_weight(yr, cfg)
        decay = temporal_decay(fp, cfg["half_life_days"])
        chunks = embed_file_chunks(fp, text, cfg)
        chunk_scores = compute_chunk_scores(
            chunks, prototype_vecs, cfg["prototype_texts"], decay, yw
        )
        agg = aggregate_dps(chunk_scores, meta["S_meta"], cfg["alpha"])

        rec = {
            "source_path": str(fp),
            "dps_score": agg["dps_score"],
            "year_slot": yr,
            "meta": meta,
            "S_topic_aggregated": agg["S_topic_aggregated"],
        }
        all_records.append(rec)

        write_record(
            fp, meta, yr, yw, decay, chunk_scores,
            agg["S_topic_aggregated"], agg["dps_score"], cfg["embed_model"]
        )
        already_scored.add(str(fp))

    build_priority_queue(all_records)
    mark_complete(len(files))
    print(f"[DPS] 完了 - {len(files)} ファイル処理済み")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m sources.dps_runner <root_dir>", file=sys.stderr)
        raise SystemExit(1)
    run(sys.argv[1])
