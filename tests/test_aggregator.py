"""test_aggregator.py - dps_aggregator のテスト"""
from __future__ import annotations

import pytest

from sources.dps_aggregator import aggregate_dps, POSITION_WEIGHT


def test_aggregate_dps_empty_chunks() -> None:
    """チャンクが空のときは dps_score = s_meta になること。"""
    result = aggregate_dps([], s_meta=0.5, alpha=0.30)
    assert result["dps_score"] == 0.5


def test_aggregate_dps_formula() -> None:
    """alpha=0.30 で DPS スコアが正しく計算されること。"""
    chunks = [
        {"position": "head", "S_topic": 0.8},
        {"position": "middle", "S_topic": 0.6},
        {"position": "tail", "S_topic": 0.8},
    ]
    result = aggregate_dps(chunks, s_meta=0.7, alpha=0.30)
    # weighted_sum = 1.2*0.8 + 1.0*0.6 + 1.2*0.8 = 0.96+0.60+0.96 = 2.52
    # weight_total = 1.2+1.0+1.2 = 3.4
    # S_topic_agg = 2.52/3.4 ≈ 0.7412
    # DPS = 0.30*0.7 + 0.70*0.7412 ≈ 0.2100+0.5188 ≈ 0.7288
    assert abs(result["dps_score"] - 0.7288) < 0.001


def test_aggregate_dps_score_range() -> None:
    """DPS スコアが 0.0〜1.0 の範囲内であること。"""
    chunks = [{"position": "head", "S_topic": 1.0}]
    result = aggregate_dps(chunks, s_meta=1.0, alpha=0.30)
    assert 0.0 <= result["dps_score"] <= 1.0
