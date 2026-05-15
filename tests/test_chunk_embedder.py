"""test_chunk_embedder.py - dps_chunk_embedder のテスト"""
from __future__ import annotations

from pathlib import Path

import pytest

from sources.dps_chunk_embedder import _split_chunks, _cache_key


def test_split_chunks_small_text() -> None:
    """500文字未満のテキストは1チャンクになること。"""
    text = "short text"
    chunks = _split_chunks(text, chunk_size=500, overlap=200, min_len=500)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_split_chunks_large_text() -> None:
    """500文字以上のテキストは複数チャンクに分割されること。"""
    text = "a" * 1500
    chunks = _split_chunks(text, chunk_size=500, overlap=200, min_len=500)
    assert len(chunks) > 1


def test_split_chunks_overlap() -> None:
    """オーバーラップが正しく適用されること。"""
    text = "a" * 1000
    chunks = _split_chunks(text, chunk_size=500, overlap=200, min_len=100)
    # stride = 500 - 200 = 300
    # chunks: [0:500], [300:800], [600:1000] -> 3 chunks
    assert len(chunks) == 3


def test_cache_key_differs_on_mtime(tmp_path: Path) -> None:
    """mtime が変わるとキャッシュキーが変わること。"""
    import time
    p = tmp_path / "doc.txt"
    p.write_text("hello", encoding="utf-8")
    key1 = _cache_key(p)
    # mtime を1秒後に変更
    time.sleep(0.01)
    import os
    os.utime(p, (p.stat().st_atime, p.stat().st_mtime + 1))
    key2 = _cache_key(p)
    assert key1 != key2
