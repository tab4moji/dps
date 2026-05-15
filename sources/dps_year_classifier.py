"""dps_year_classifier.py
目的: Step 2 - フォルダパスから年代スロットを判定し、年代重み A(y) を返す。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from sources.dps_config_loader import load_config

YEAR_PATTERN = re.compile(r'(?:FY)?(\d{4})', re.IGNORECASE)


def extract_year(file_path: Path) -> int:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 5
    Actual Use: TRUE
    """
    """パストークンから年度を抽出して返す。見つからなければ mtime の年を返す。"""
    tokens = file_path.as_posix()
    matches = YEAR_PATTERN.findall(tokens)
    years = [int(y) for y in matches if 1990 <= int(y) <= 2100]
    if years:
        return max(years)
    import datetime
    mtime = file_path.stat().st_mtime
    return datetime.datetime.fromtimestamp(mtime).year


def year_weight(year: int, config: dict | None = None) -> float:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 5
    Actual Use: TRUE
    """
    """年代スロット重み A(y) を返す。"""
    cfg = config if config is not None else load_config()
    current_year = time.gmtime().tm_year
    diff = current_year - year
    weights = cfg["year_weights"]
    key = str(diff)
    return float(weights.get(key, weights["default"]))
