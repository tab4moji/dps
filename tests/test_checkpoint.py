"""test_checkpoint.py - dps_checkpoint のテスト"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from sources import dps_checkpoint


def test_load_checkpoint_no_file(tmp_path: Path) -> None:
    """チェックポイントファイルが存在しない場合に初期値を返すこと。"""
    with patch.object(dps_checkpoint, "CHECKPOINT_FILE", tmp_path / "cp.json"):
        result = dps_checkpoint.load_checkpoint()
    assert result["dps_complete"] is False


def test_save_and_load_checkpoint(tmp_path: Path) -> None:
    """保存したチェックポイントを正しく読み込めること。"""
    cp_file = tmp_path / "cp.json"
    with patch.object(dps_checkpoint, "CHECKPOINT_FILE", cp_file):
        dps_checkpoint.save_checkpoint({"dps_complete": True, "total_files": 42})
        result = dps_checkpoint.load_checkpoint()
    assert result["dps_complete"] is True
    assert result["total_files"] == 42


def test_mark_complete(tmp_path: Path) -> None:
    """mark_complete 後に dps_complete が True になること。"""
    cp_file = tmp_path / "cp.json"
    with patch.object(dps_checkpoint, "CHECKPOINT_FILE", cp_file):
        dps_checkpoint.mark_complete(100)
        result = dps_checkpoint.load_checkpoint()
    assert result["dps_complete"] is True
    assert result["total_files"] == 100
