"""dps_config_loader.py
目的: dps_config.json を読み込み、設定値を提供するモジュール。
更新履歴:
  001 2026-05-15 初版
  002 2026-05-18 環境変数による上書き機能を追加
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "dps_config.json"


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """設定ファイルを読み込み、環境変数で上書きして辞書を返す。"""
    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つからない: {config_path}")
    with config_path.open(encoding="utf-8") as fh:
        config = json.load(fh)

    # Ollama 関連の環境変数による上書き (ollama.md 準拠)
    # OLLAMA_HOST が指定されている場合、ollama_url を上書きする
    ollama_host = os.getenv("OLLAMA_HOST")
    if ollama_host and "ollama_url" in config:
        if ollama_host.startswith(("http://", "https://")):
            # スキーマが含まれている場合は、パス部分 (/api/embed) を維持して置換
            parsed_base = urlparse(ollama_host)
            parsed_orig = urlparse(config["ollama_url"])
            new_url = urlunparse(parsed_base._replace(path=parsed_orig.path))
            config["ollama_url"] = new_url
        else:
            # ホスト名のみの場合は netloc を置換
            parsed = urlparse(config["ollama_url"])
            new_url = urlunparse(parsed._replace(netloc=ollama_host))
            config["ollama_url"] = new_url

    # OLLAMA_KEEP_ALIVE -> ollama_keep_alive
    keep_alive = os.getenv("OLLAMA_KEEP_ALIVE")
    if keep_alive:
        config["ollama_keep_alive"] = keep_alive

    # OLLAMA_CONTEXT_LENGTH -> ollama_context_length
    ctx_len = os.getenv("OLLAMA_CONTEXT_LENGTH")
    if ctx_len:
        try:
            config["ollama_context_length"] = int(ctx_len)
        except ValueError:
            pass

    # 汎用的な DPS_ プレフィックスによる上書き
    for key, value in os.environ.items():
        if key.startswith("DPS_"):
            config_key = key[4:].lower()
            # 数値やブール値への変換試行
            if value.lower() == "true":
                config[config_key] = True
            elif value.lower() == "false":
                config[config_key] = False
            else:
                try:
                    if "." in value:
                        config[config_key] = float(value)
                    else:
                        config[config_key] = int(value)
                except ValueError:
                    config[config_key] = value

    return config
