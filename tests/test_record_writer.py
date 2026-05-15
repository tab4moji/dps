"""test_record_writer.py - dps_record_writer のテスト"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sources.dps_record_writer import write_record


def test_write_record_creates_json(tmp_path: Path) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """write_record が 元ファイルパス+.json を生成すること。"""
    fp = tmp_path / "doc.pdf"
    fp.write_text("test", encoding="utf-8")
    meta = {
        "mtime_score": 0.9, "keyword_hit_score": 0.5,
        "semantic_path_score": 0.7, "filetype_score": 0.9,
        "path_depth_score": 0.8, "size_score": 0.5,
        "folder_density_score": 1.0, "S_meta": 0.75,
    }
    out = write_record(
        fp, meta,
        year_slot=2026, year_weight=1.0, time_decay=0.95,
        chunk_scores=[
            {"chunk_index": 0, "position": "head",
             "text_preview": "test", "top_prototype": "proto",
             "cos_sim": 0.8, "S_topic": 0.76}
        ],
        s_topic_aggregated=0.76,
        dps_score=0.758,
        embed_model="nomic-embed-text",
    )
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["dps_score"] == 0.758
    assert data["year_slot"] == 2026
    assert "scored_at" in data
