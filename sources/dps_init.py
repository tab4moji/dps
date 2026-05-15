"""dps_init.py
目的: 業務プロトタイプテキストを起動時に1回だけ Embedding し、
      prototype_vecs をメモリに保持する。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import json
import urllib.request
from typing import List

from sources.dps_config_loader import load_config


def _embed_text(text: str, ollama_url: str, model: str) -> List[float]:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 0
    Actual Use: FALSE
    """
    """Ollama embed API を呼び出して embedding ベクトルを返す。"""
    payload = json.dumps({"model": model, "input": text}).encode()
    req = urllib.request.Request(
        ollama_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["embeddings"][0]


def build_prototype_vecs(
    config: dict | None = None,
) -> List[List[float]]:
    """
    Type: function
    Scope: global
    Updates: 1
    Created: 2026-05-15T16:18:57+09:00 (e59d103a)
    Last Updated: 2026-05-15T16:18:57+09:00 (e59d103a)
    Ref Count: 1
    Actual Use: FALSE
    """
    """プロトタイプテキストを Embedding してベクトルリストを返す。"""
    cfg = config if config is not None else load_config()
    url = cfg["ollama_url"]
    model = cfg["embed_model"]
    return [
        _embed_text(text, url, model)
        for text in cfg["prototype_texts"]
    ]
