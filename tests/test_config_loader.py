"""test_config_loader.py - dps_config_loader のテスト"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sources.dps_config_loader import load_config


def test_load_config_ok(tmp_path: Path) -> None:
    """有効な設定ファイルを正常に読み込めること。"""
    cfg_path = tmp_path / "dps_config.json"
    cfg_path.write_text(json.dumps({"alpha": 0.3}), encoding="utf-8")
    result = load_config(cfg_path)
    assert result["alpha"] == 0.3


def test_load_config_missing_raises(tmp_path: Path) -> None:
    """存在しないファイルは FileNotFoundError を送出すること。"""
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "no_such_file.json")
