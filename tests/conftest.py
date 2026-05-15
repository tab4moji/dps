"""conftest.py - pytest 共通フィクスチャ"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_file(tmp_path: Path) -> Path:
    """テスト用の一時テキストファイルを返す。"""
    p = tmp_path / "projects" / "contracts" / "2026" / "invoice_test.pdf"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "This is a test invoice document. " * 20,  # > 500 chars
        encoding="utf-8",
    )
    return p


@pytest.fixture()
def small_file(tmp_path: Path) -> Path:
    """2KB 未満の小さいファイルを返す。"""
    p = tmp_path / "tiny.txt"
    p.write_text("hello", encoding="utf-8")
    return p


@pytest.fixture()
def sample_config(tmp_path: Path) -> dict:
    """テスト用設定辞書を返す。"""
    return {
        "alpha": 0.30,
        "half_life_days": 30,
        "chunk_size": 500,
        "chunk_overlap": 200,
        "min_text_len": 500,
        "min_file_bytes": 2048,
        "max_file_bytes": 20971520,
        "embed_model": "nomic-embed-text",
        "ollama_url": "http://localhost:11434/api/embed",
        "ideal_path_depth": 3,
        "folder_density_threshold": 50,
        "sem_score_fallback_threshold": 0.20,
        "year_weights": {"0": 1.00, "1": 0.80, "2": 0.60, "default": 0.40},
        "filetype_scores": {
            ".msg": 1.0, ".eml": 1.0, ".pdf": 0.9,
            ".docx": 0.85, ".pptx": 0.80, ".xlsx": 0.70,
            ".txt": 0.50, ".csv": 0.30,
        },
        "seed_keywords": [
            "projects", "contracts", "invoice", "legal", "budget",
            "proposal", "minutes", "report", "urgent", "confidential",
        ],
        "prototype_texts": [
            "project contract invoice proposal budget",
            "meeting minutes agenda action items",
            "legal compliance regulation policy",
            "urgent escalation critical incident",
            "technical specification design architecture",
            "customer client stakeholder communication",
            "report analysis result summary",
        ],
    }
