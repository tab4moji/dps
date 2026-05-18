"""dps_runner.py
Purpose: DPS overall orchestration.
Update: 006 2026-05-18 support rank.md, rank.json
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import List

from sources.dps_config_loader import load_config
from sources.dps_init import build_prototype_vecs
from sources.dps_meta_scorer import compute_meta_score
from sources.dps_year_classifier import extract_year, year_weight
from sources.dps_chunk_embedder import embed_file_chunks
from sources.dps_topic_scorer import compute_chunk_scores, temporal_decay
from sources.dps_aggregator import aggregate_dps
from sources.dps_record_writer import write_record, get_result_path, _calculate_file_hash
from sources.dps_queue_builder import build_priority_queue
from sources.dps_checkpoint import load_checkpoint, save_checkpoint, mark_complete


def _read_text(file_path: Path) -> str:
    """file read"""
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _walk_files(root: Path) -> List[Path]:
    """walk files"""
    files = []
    for p in root.rglob("*"):
        if p.is_file():
            try:
                rel = p.relative_to(root)
                if any(part.startswith(".") for part in rel.parts[:-1]):
                    continue
            except ValueError:
                continue
            files.append(p)
    return files


def run(root_dir: str) -> None:
    """run DPS"""
    root = Path(root_dir).absolute()
    if not root.exists():
        print(f"ERROR: {root}", file=sys.stderr)
        raise SystemExit(1)

    result_dir = root / ".dps"
    cfg = load_config()
    checkpoint = load_checkpoint()
    already_scored = set(checkpoint.get("scored_paths", []))

    prototype_vecs = build_prototype_vecs(cfg)
    files = _walk_files(root)

    all_records: List[dict] = []

    for fp in files:
        rel_path = str(fp.relative_to(root))
        json_path = get_result_path(fp, result_dir)
        current_hash = _calculate_file_hash(fp)
        
        if json_path.exists():
            try:
                rec = json.loads(json_path.read_text(encoding="utf-8"))
                if (rel_path in already_scored or str(fp) in already_scored) and rec.get("file_hash") == current_hash:
                    all_records.append(rec)
                    continue
            except Exception:
                pass

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
            "source_path": rel_path,
            "file_hash": current_hash,
            "dps_score": agg["dps_score"],
            "year_slot": yr,
            "meta": meta,
            "S_topic_aggregated": agg["S_topic_aggregated"],
            "topics_detected": list({c['top_prototype'] for c in chunk_scores if c['cos_sim'] >= 0.5})
        }
        all_records.append(rec)

        write_record(
            fp, result_dir, meta, yr, yw, decay, chunk_scores,
            agg["S_topic_aggregated"], agg["dps_score"], cfg["embed_model"],
            source_path=rel_path
        )
        already_scored.add(rel_path)

    build_priority_queue(
        all_records, 
        rank_md_path=result_dir / 'rank.md',
        rank_json_path=result_dir / 'rank.json'
    )
    
    mark_complete(len(files))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(1)
    run(sys.argv[1])
