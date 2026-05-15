"""dps_meta_scorer.py
目的: Step 1 - ファイルメタデータから S_meta を計算する（LLM不要）。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import math
import os
import re
import time
from pathlib import Path
from typing import List

from sources.dps_config_loader import load_config


# --- 個別シグナル計算 ---

def _mtime_score(file_path: Path, half_life: float) -> float:
    """mtime 新しさスコア（指数減衰）を返す。"""
    days_old = (time.time() - file_path.stat().st_mtime) / 86400
    return math.exp(-0.693 * days_old / half_life)


def _keyword_hit_score(file_path: Path, seed_keywords: List[str]) -> float:
    """フォルダパストークンとシード語の一致割合を返す。"""
    tokens = set(re.split(r'[^a-zA-Z0-9]+', file_path.as_posix().lower()))
    if not seed_keywords:
        return 0.0
    hits = sum(1 for kw in seed_keywords if kw.lower() in tokens)
    return min(hits / len(seed_keywords), 1.0)


def _filetype_score(file_path: Path, filetype_scores: dict) -> float:
    """拡張子テーブルからファイル種別スコアを返す。"""
    return filetype_scores.get(file_path.suffix.lower(), 0.40)


def _path_depth_score(file_path: Path, ideal_depth: int) -> float:
    """パス深さが ideal_depth からの乖離で減点したスコアを返す。"""
    depth = len(file_path.parts)
    diff = abs(depth - ideal_depth)
    return max(0.0, 1.0 - diff * 0.1)


def _size_score(file_path: Path, min_bytes: int, max_bytes: int) -> float:
    """ファイルサイズが範囲内なら 1.0、範囲外は 0.5 を返す。"""
    size = file_path.stat().st_size
    return 1.0 if min_bytes <= size <= max_bytes else 0.5


def _folder_density_score(
    file_path: Path, density_threshold: int
) -> float:
    """同フォルダ内ファイル数が閾値超なら減点したスコアを返す。"""
    parent = file_path.parent
    try:
        count = sum(1 for _ in parent.iterdir() if _.is_file())
    except PermissionError:
        return 0.5
    return 0.5 if count > density_threshold else 1.0


def _semantic_path_score(
    file_path: Path,
    prototype_vecs: list,
    ollama_url: str,
    model: str,
    fallback_score: float,
    threshold: float,
) -> float:
    """Semantic Path Score を計算して返す。失敗時はフォールバック値を返す。"""
    import json
    import urllib.request
    from sources.dps_topic_scorer import cosine_similarity

    tokens = re.split(r'[^a-zA-Z0-9]+', file_path.as_posix().lower())
    text = " ".join(t for t in tokens if t)
    try:
        payload = json.dumps({"model": model, "input": text}).encode()
        req = urllib.request.Request(
            ollama_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        vec = data["embeddings"][0]
        score = max(cosine_similarity(vec, pv) for pv in prototype_vecs)
    except Exception:
        return fallback_score
    if score < threshold:
        return fallback_score
    return score


# --- 統合 S_meta 計算 ---

def compute_meta_score(
    file_path: Path,
    prototype_vecs: list,
    config: dict | None = None,
) -> dict:
    """7シグナルを加重合計して S_meta と各シグナル値を返す。"""
    cfg = config if config is not None else load_config()

    kw_score = _keyword_hit_score(file_path, cfg["seed_keywords"])
    sem_score = _semantic_path_score(
        file_path,
        prototype_vecs,
        cfg["ollama_url"],
        cfg["embed_model"],
        fallback_score=kw_score * 0.8,
        threshold=cfg["sem_score_fallback_threshold"],
    )
    mt_score = _mtime_score(file_path, cfg["half_life_days"])
    ft_score = _filetype_score(file_path, cfg["filetype_scores"])
    pd_score = _path_depth_score(file_path, cfg["ideal_path_depth"])
    sz_score = _size_score(file_path, cfg["min_file_bytes"], cfg["max_file_bytes"])
    fd_score = _folder_density_score(file_path, cfg["folder_density_threshold"])

    s_meta = (
        0.28 * mt_score
        + 0.25 * kw_score
        + 0.20 * sem_score
        + 0.13 * ft_score
        + 0.07 * pd_score
        + 0.05 * sz_score
        + 0.02 * fd_score
    )
    return {
        "mtime_score": mt_score,
        "keyword_hit_score": kw_score,
        "semantic_path_score": sem_score,
        "filetype_score": ft_score,
        "path_depth_score": pd_score,
        "size_score": sz_score,
        "folder_density_score": fd_score,
        "S_meta": min(max(s_meta, 0.0), 1.0),
    }
