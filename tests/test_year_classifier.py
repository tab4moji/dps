"""test_year_classifier.py - dps_year_classifier のテスト"""
from __future__ import annotations

from pathlib import Path

import pytest

from sources.dps_year_classifier import extract_year, year_weight


def test_extract_year_from_path(tmp_path: Path) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """パスに含まれる年度を正しく抽出できること。"""
    p = tmp_path / "FY2025" / "doc.pdf"
    p.parent.mkdir(parents=True)
    p.write_text("x", encoding="utf-8")
    assert extract_year(p) == 2025


def test_extract_year_fallback_to_mtime(tmp_path: Path) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """年度がパスにない場合は mtime の年を返すこと。"""
    import datetime
    p = tmp_path / "scan001.pdf"
    p.write_text("x", encoding="utf-8")
    year = extract_year(p)
    assert year == datetime.datetime.now().year


def test_year_weight_current(sample_config: dict) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """当年は重み 1.0 を返すこと。"""
    import time
    current = time.gmtime().tm_year
    assert year_weight(current, sample_config) == 1.0


def test_year_weight_old(sample_config: dict) -> None:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: TRUE
    """
    """3年以上前はデフォルト重み 0.4 を返すこと。"""
    import time
    old_year = time.gmtime().tm_year - 5
    assert year_weight(old_year, sample_config) == 0.40
