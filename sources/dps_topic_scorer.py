"""dps_topic_scorer.py
目的: Step 4 - チャンクベクトルからトピック重要度 S_topic を計算する。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import math
import time
from pathlib import Path
from typing import List, Tuple

from sources.dps_config_loader import load_config


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 3
    Actual Use: TRUE
    """
    """2ベクトルのコサイン類似度を返す。"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def temporal_decay(file_path: Path, half_life: float) -> float:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 1
    Actual Use: FALSE
    """
    """時間減衰係数 D(t) を返す（指数減衰、半減期 half_life 日）。"""
    days_old = (time.time() - file_path.stat().st_mtime) / 86400
    return math.exp(-0.693 * days_old / half_life)


def compute_chunk_scores(
    chunks: List[Tuple[str, List[float]]],
    prototype_vecs: List[List[float]],
    prototype_texts: List[str],
    decay: float,
    year_w: float,
) -> List[dict]:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 3
    Actual Use: TRUE
    """
    """チャンクごとの S_topic と関連プロトタイプ情報を返す。"""
    results = []
    n = len(chunks)
    for i, (text, vec) in enumerate(chunks):
        sims = [cosine_similarity(vec, pv) for pv in prototype_vecs]
        max_sim = max(sims)
        top_idx = sims.index(max_sim)
        s_topic = max_sim * decay * year_w

        if n <= 4:
            pos = "head" if i == 0 else ("tail" if i == n - 1 else "middle")
        else:
            if i < 2:
                pos = "head"
            elif i >= n - 2:
                pos = "tail"
            else:
                pos = "middle"

        results.append({
            "chunk_index": i,
            "position": pos,
            "text_preview": text[:80],
            "top_prototype": prototype_texts[top_idx],
            "cos_sim": round(max_sim, 6),
            "S_topic": round(min(max(s_topic, 0.0), 1.0), 6),
        })
    return results
