"""dps_aggregator.py
目的: Step 5 - チャンク位置重みを適用して S_topic_agg を算出し、
      S_meta と合わせて DPS スコアを集約する。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

from typing import List

POSITION_WEIGHT = {"head": 1.20, "tail": 1.20, "middle": 1.00}


def aggregate_dps(
    chunk_scores: List[dict],
    s_meta: float,
    alpha: float = 0.30,
) -> dict:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 4
    Actual Use: TRUE
    """
    """チャンクスコアを集約して DPS スコアと S_topic_agg を返す。"""
    if not chunk_scores:
        return {"S_topic_aggregated": 0.0, "dps_score": s_meta}

    weighted_sum = sum(
        POSITION_WEIGHT[c["position"]] * c["S_topic"]
        for c in chunk_scores
    )
    weight_total = sum(
        POSITION_WEIGHT[c["position"]]
        for c in chunk_scores
    )
    s_topic_agg = weighted_sum / weight_total if weight_total > 0 else 0.0
    dps_score = alpha * s_meta + (1 - alpha) * s_topic_agg

    return {
        "S_topic_aggregated": round(min(max(s_topic_agg, 0.0), 1.0), 6),
        "dps_score": round(min(max(dps_score, 0.0), 1.0), 6),
    }
