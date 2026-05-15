"""test_topic_scorer.py - dps_topic_scorer のテスト"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from sources.dps_topic_scorer import cosine_similarity, compute_chunk_scores


def test_cosine_similarity_identical() -> None:
    """同一ベクトルのコサイン類似度は 1.0 になること。"""
    v = [1.0, 0.0, 0.0]
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-9


def test_cosine_similarity_orthogonal() -> None:
    """直交ベクトルのコサイン類似度は 0.0 になること。"""
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert abs(cosine_similarity(a, b)) < 1e-9


def test_cosine_similarity_zero_vector() -> None:
    """ゼロベクトルとの類似度は 0.0 になること。"""
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_compute_chunk_scores_position_assignment() -> None:
    """先頭チャンクは 'head'、末尾は 'tail' が割り当てられること。"""
    proto_vecs = [[1.0, 0.0, 0.0]]
    proto_texts = ["prototype"]
    chunks = [
        ("chunk0", [1.0, 0.0, 0.0]),
        ("chunk1", [0.5, 0.5, 0.0]),
        ("chunk2", [0.0, 1.0, 0.0]),
    ]
    results = compute_chunk_scores(chunks, proto_vecs, proto_texts, decay=1.0, year_w=1.0)
    assert results[0]["position"] == "head"
    assert results[-1]["position"] == "tail"


def test_compute_chunk_scores_s_topic_range() -> None:
    """S_topic が 0.0〜1.0 の範囲内であること。"""
    proto_vecs = [[1.0, 0.0]]
    proto_texts = ["proto"]
    chunks = [("text", [0.8, 0.6])]
    results = compute_chunk_scores(chunks, proto_vecs, proto_texts, decay=0.9, year_w=0.8)
    assert 0.0 <= results[0]["S_topic"] <= 1.0
