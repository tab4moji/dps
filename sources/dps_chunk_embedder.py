"""dps_chunk_embedder.py
目的: Step 3 - テキストを固定幅チャンクに分割し Embedding する。
      キャッシュ（dps_embed_cache.jsonl）でスキップ制御。
更新履歴:
  001 2026-05-15 初版
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import List, Tuple

from sources.dps_config_loader import load_config

CACHE_FILE = Path("dps_embed_cache.jsonl")


def _cache_key(file_path: Path) -> str:
    """ファイルパスと mtime の sha256 をキャッシュキーとして返す。"""
    mtime = file_path.stat().st_mtime
    raw = f"{file_path}:{mtime}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _load_cache() -> dict:
    """キャッシュファイルを読み込んで辞書を返す。"""
    cache: dict = {}
    if not CACHE_FILE.exists():
        return cache
    with CACHE_FILE.open(encoding="utf-8") as fh:
        for line in fh:
            entry = json.loads(line.strip())
            cache[entry["key"]] = entry["chunks"]
    return cache


def _save_cache(key: str, chunks: list) -> None:
    """チャンクリストをキャッシュファイルに追記する。"""
    with CACHE_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"key": key, "chunks": chunks}, ensure_ascii=False) + "\n")


def _split_chunks(
    text: str, chunk_size: int, overlap: int, min_len: int
) -> List[str]:
    """テキストを固定幅スライドウィンドウで分割したリストを返す。"""
    if len(text) < min_len:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += chunk_size - overlap
    return chunks


def _embed_text(text: str, ollama_url: str, model: str) -> List[float]:
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


def embed_file_chunks(
    file_path: Path,
    text: str,
    config: dict | None = None,
) -> List[Tuple[str, List[float]]]:
    """チャンク分割+Embedding 結果を [(text, vec), ...] で返す。キャッシュ利用。"""
    cfg = config if config is not None else load_config()
    key = _cache_key(file_path)
    cache = _load_cache()
    if key in cache:
        return [(c["text"], c["vec"]) for c in cache[key]]

    raw_chunks = _split_chunks(
        text,
        cfg["chunk_size"],
        cfg["chunk_overlap"],
        cfg["min_text_len"],
    )
    result = []
    for chunk_text in raw_chunks:
        vec = _embed_text(chunk_text, cfg["ollama_url"], cfg["embed_model"])
        result.append((chunk_text, vec))

    _save_cache(key, [{"text": t, "vec": v} for t, v in result])
    return result
