"""test_sensitivity.py - dps_sensitivity のテスト"""
from __future__ import annotations

import pytest

from sources.dps_sensitivity import spearman_rho, run_sensitivity


def test_spearman_rho_identical() -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """同一リストの Spearman ρ は 1.0 になること。"""
    x = [3.0, 1.0, 2.0, 4.0]
    assert abs(spearman_rho(x, x) - 1.0) < 1e-9


def test_spearman_rho_single_element() -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """要素が1つのときは 1.0 を返すこと。"""
    assert spearman_rho([0.5], [0.5]) == 1.0


def test_run_sensitivity_stable() -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """alpha 摂動が ±20% 以内なら ρ > 0.9 になること（安定な設計）。"""
    records = [
        {"meta": {"S_meta": 0.8}, "S_topic_aggregated": 0.7},
        {"meta": {"S_meta": 0.5}, "S_topic_aggregated": 0.4},
        {"meta": {"S_meta": 0.9}, "S_topic_aggregated": 0.85},
        {"meta": {"S_meta": 0.3}, "S_topic_aggregated": 0.2},
        {"meta": {"S_meta": 0.6}, "S_topic_aggregated": 0.65},
    ]
    result = run_sensitivity(records, alpha_base=0.30)
    assert result["alpha_up"] > 0.9
    assert result["alpha_down"] > 0.9
