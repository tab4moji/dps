"""dps_queue_builder.py
目的: DPS スコア降順にソートした priority_queue.jsonl, rank.md, rank.json を生成する。
更新履歴:
  001 2026-05-15 初版
  002 2026-05-18 自然言語形式のランキング表示 (rank.md) 生成機能を追加
  003 2026-05-18 構造化されたランキング表示 (rank.json) 生成機能を追加
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List


def build_priority_queue(
    records: List[dict],
    output_path: Path = Path('priority_queue.jsonl'),
    rank_md_path: Path | None = None,
    rank_json_path: Path | None = None,
) -> Path:
    """records を dps_score 降順でソートして各種形式に書き出す。"""
    sorted_records = sorted(records, key=lambda r: r['dps_score'], reverse=True)
    
    # JSONL 出力 (Phase 1 連携用)
    with output_path.open('w', encoding='utf-8') as fh:
        for rank, rec in enumerate(sorted_records, start=1):
            entry = {
                'rank': rank,
                'source_path': rec['source_path'],
                'dps_score': rec['dps_score'],
                'year_slot': rec['year_slot'],
            }
            fh.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # rank.md 出力 (人間用)
    if rank_md_path:
        with rank_md_path.open('w', encoding='utf-8') as fh:
            fh.write('# DPS 資料重要度ランキング\n\n')
            fh.write('このリストは、メタデータおよびセマンティック分析に基づき、優先的に処理すべき資料を順位付けしたものです。\n\n')
            fh.write('| 順位 | 重要度 | ファイルパス | 年度 | 主なトピック |\n')
            fh.write('| :--- | :--- | :--- | :--- | :--- |\n')
            
            for rank, rec in enumerate(sorted_records, start=1):
                score_pct = f"{rec['dps_score'] * 100:.1f}%"
                topics = ', '.join(rec.get('topics_detected', []))
                fh.write(f"| {rank} | {score_pct} | {rec['source_path']} | {rec['year_slot']} | {topics} |\n")
            
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fh.write(f'\n\n---\n*生成日時: {now_str} (自動生成)*\n')

    # rank.json 出力 (ツール連携・可視化用)
    if rank_json_path:
        rank_data = []
        for rank, rec in enumerate(sorted_records, start=1):
            rank_data.append({
                'rank': rank,
                'importance_pct': f"{rec['dps_score'] * 100:.1f}%",
                'dps_score': rec['dps_score'],
                'source_path': rec['source_path'],
                'year_slot': rec['year_slot'],
                'topics_detected': rec.get('topics_detected', [])
            })
        
        output_data = {
            'generated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'ranking': rank_data
        }
        
        with rank_json_path.open('w', encoding='utf-8') as fh:
            json.dump(output_data, fh, ensure_ascii=False, indent=2)

    return output_path
