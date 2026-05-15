"""dps_sensitivity.py
目的: 重みパラメータを ±20% 摂動させ Spearman ρ で順位安定性を検証する。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


def _rank_list(records: List[dict], key: str = "dps_score") -> List[float]:
    """スコア降順のランクリストを返す。"""
    sorted_r = sorted(records, key=lambda r: r[key], reverse=True)
    return [r[key] for r in sorted_r]


def spearman_rho(x: List[float], y: List[float]) -> float:
    """2つのリストの Spearman 順位相関係数を返す。"""
    n = len(x)
    if n < 2:
        return 1.0
    rank_x = _rank_values(x)
    rank_y = _rank_values(y)
    d_sq_sum = sum((rx - ry) ** 2 for rx, ry in zip(rank_x, rank_y))
    return 1 - 6 * d_sq_sum / (n * (n ** 2 - 1))


def _rank_values(values: List[float]) -> List[int]:
    """値リストを順位リストに変換して返す（降順）。"""
    indexed = sorted(enumerate(values), key=lambda t: t[1], reverse=True)
    ranks = [0] * len(values)
    for rank, (idx, _) in enumerate(indexed, start=1):
        ranks[idx] = rank
    return ranks


def run_sensitivity(
    records: List[dict],
    alpha_base: float = 0.30,
    perturbation: float = 0.20,
    top_n: int = 100,
) -> dict:
    """alpha を ±20% 変動させて Spearman ρ を計算して返す。"""
    base_scores = [
        alpha_base * r["meta"]["S_meta"]
        + (1 - alpha_base) * r["S_topic_aggregated"]
        for r in records
    ]
    results = {}
    for label, alpha in [
        ("alpha_up", alpha_base * (1 + perturbation)),
        ("alpha_down", alpha_base * (1 - perturbation)),
    ]:
        perturbed = [
            alpha * r["meta"]["S_meta"]
            + (1 - alpha) * r["S_topic_aggregated"]
            for r in records
        ]
        rho = spearman_rho(base_scores[:top_n], perturbed[:top_n])
        results[label] = round(rho, 6)
    return results
