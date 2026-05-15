"""test_queue_builder.py - dps_queue_builder のテスト"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sources.dps_queue_builder import build_priority_queue


def _make_records() -> list:
    return [
        {"source_path": "/a/b.pdf", "dps_score": 0.5, "year_slot": 2024},
        {"source_path": "/a/c.pdf", "dps_score": 0.9, "year_slot": 2026},
        {"source_path": "/a/d.pdf", "dps_score": 0.1, "year_slot": 2023},
    ]


def test_queue_sorted_descending(tmp_path: Path) -> None:
    """JSONL が dps_score 降順に出力されること。"""
    out = tmp_path / "pq.jsonl"
    build_priority_queue(_make_records(), output_path=out)
    lines = [json.loads(l) for l in out.read_text().splitlines()]
    scores = [l["dps_score"] for l in lines]
    assert scores == sorted(scores, reverse=True)


def test_queue_rank_starts_at_1(tmp_path: Path) -> None:
    """rank が 1 始まりであること。"""
    out = tmp_path / "pq.jsonl"
    build_priority_queue(_make_records(), output_path=out)
    first = json.loads(out.read_text().splitlines()[0])
    assert first["rank"] == 1


def test_queue_entry_count(tmp_path: Path) -> None:
    """出力行数が入力レコード数と一致すること。"""
    records = _make_records()
    out = tmp_path / "pq.jsonl"
    build_priority_queue(records, output_path=out)
    lines = out.read_text().splitlines()
    assert len(lines) == len(records)
