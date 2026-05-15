"""dps_checkpoint.py
目的: dps_checkpoint.json の読み書きと完了判定を管理する。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import json
from pathlib import Path

CHECKPOINT_FILE = Path("dps_checkpoint.json")


def load_checkpoint() -> dict:
    """チェックポイントを読み込んで辞書を返す。存在しなければ初期値を返す。"""
    if not CHECKPOINT_FILE.exists():
        return {"dps_complete": False, "scored_paths": []}
    with CHECKPOINT_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_checkpoint(data: dict) -> None:
    """チェックポイントを JSON ファイルに書き出す。"""
    CHECKPOINT_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def mark_complete(total_files: int) -> None:
    """DPS 完了フラグを立てて total_files を記録する。"""
    data = load_checkpoint()
    data["dps_complete"] = True
    data["total_files"] = total_files
    save_checkpoint(data)
