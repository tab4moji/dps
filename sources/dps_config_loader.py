"""dps_config_loader.py
目的: dps_config.json を読み込み、設定値を提供するモジュール。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "dps_config.json"


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 7
    Actual Use: TRUE
    """
    """設定ファイルを読み込んで辞書を返す。"""
    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つからない: {config_path}")
    with config_path.open(encoding="utf-8") as fh:
        return json.load(fh)
