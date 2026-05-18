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


def _embed_batch(texts: List[str], ollama_url: str, model: str) -> List[List[float]]:
    """Ollama embed API を呼び出して、複数のテキストの embedding ベクトルを一度に取得する。"""
    payload = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(
        ollama_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data["embeddings"]
    except Exception as e:
        raise RuntimeError(f"Batch Embedding API 呼び出し失敗 (URL: {ollama_url}): {e}") from e


def build_prototype_vecs(
    config: dict | None = None,
) -> List[List[float]]:
    """プロトタイプテキストを一括で Embedding してベクトルリストを返す。"""
    cfg = config if config is not None else load_config()
    url = cfg["ollama_url"]
    model = cfg["embed_model"]
    texts = cfg["prototype_texts"]
    return _embed_batch(texts, url, model)
