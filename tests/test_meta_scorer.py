"""test_meta_scorer.py - dps_meta_scorer のテスト"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from sources.dps_meta_scorer import (
    _mtime_score,
    _keyword_hit_score,
    _filetype_score,
    _path_depth_score,
    _size_score,
    _folder_density_score,
)


def test_mtime_score_recent(tmp_file: Path) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """直近ファイルは高い mtime スコアを返すこと。"""
    score = _mtime_score(tmp_file, half_life=30)
    assert 0.9 <= score <= 1.0


def test_keyword_hit_score_match(tmp_file: Path, sample_config: dict) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """パスにキーワードが含まれるとスコアが正の値になること。"""
    score = _keyword_hit_score(tmp_file, sample_config["seed_keywords"])
    assert score > 0.0


def test_keyword_hit_score_no_match(tmp_path: Path, sample_config: dict) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """キーワードが含まれないパスはスコア 0.0 を返すこと。"""
    p = tmp_path / "zzz" / "xyz.txt"
    p.parent.mkdir()
    p.write_text("x", encoding="utf-8")
    score = _keyword_hit_score(p, sample_config["seed_keywords"])
    assert score == 0.0


def test_filetype_score_pdf(tmp_file: Path, sample_config: dict) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """PDF は 0.9 のスコアを返すこと。"""
    assert _filetype_score(tmp_file, sample_config["filetype_scores"]) == 0.9


def test_filetype_score_unknown(tmp_path: Path, sample_config: dict) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """未知の拡張子はデフォルト 0.4 を返すこと。"""
    p = tmp_path / "file.xyz"
    p.write_text("x", encoding="utf-8")
    assert _filetype_score(p, sample_config["filetype_scores"]) == 0.40


def test_size_score_in_range(tmp_file: Path, sample_config: dict) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """サイズ範囲内のファイルは 1.0 を返すこと（tmp_file は小さいので 0.5）。"""
    score = _size_score(
        tmp_file,
        sample_config["min_file_bytes"],
        sample_config["max_file_bytes"],
    )
    assert score in (0.5, 1.0)


def test_path_depth_score(tmp_file: Path, sample_config: dict) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """パス深さスコアが 0.0〜1.0 の範囲内であること。"""
    score = _path_depth_score(tmp_file, sample_config["ideal_path_depth"])
    assert 0.0 <= score <= 1.0


def test_folder_density_score_sparse(tmp_file: Path, sample_config: dict) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """ファイル数が少ないフォルダは 1.0 を返すこと。"""
    score = _folder_density_score(
        tmp_file, sample_config["folder_density_threshold"]
    )
    assert score == 1.0
