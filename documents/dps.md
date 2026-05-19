# Phase 0 設計報告書：資料重要度スコアリングシステム（DPS）

**作成日：2026年5月15日**
**更新日：2026年5月18日（v1.1 - 環境変数上書き・ランキング機能追記）**

***

## 1. 概要

ネットワークドライブ上の全ファイルを Phase 1（FastPass）に投入する前に、**LLM を使わずに高速に重要度スコア（DPS スコア）を算出し、処理優先順位を確定させる**前段バッチ処理システムだ。

**本システムは「後から重要な資料が出てきて全体が変わる」を抑止する。** Phase 1 の SBTA/クラスタリングは処理順序に影響されるため、重要ファイルを先頭から投入することで、ラベル辞書の早期安定化を図る。

**本システムは Phase 1/1-I/2 のコードに一切手を入れない。** `priority_queue.jsonl`（DPS スコア降順）を出力し、`file_walker.py` の処理順序を置き換えるだけで統合が完了する。

**1ファイルに複数トピックが含まれることを前提とする。** ファイルをチャンク単位で Embedding し、トピック重要度を集約することでファイルスコアを算出する。分析結果はすべて `.dps/` ディレクトリに記録し、途中計算も含めて漏れなく保存する。

***

## 2. 処理全体フロー

```
[事前] プロトタイプベクトル生成        (dps_init.py)
  ↓ → prototype_vecs をメモリに保持（起動時1回だけ Embedding）
[入力] ネットワークドライブ上のファイル群
  ↓
Step 0:   ファイルメタデータ収集        (file_walker.py ※既存流用)
  ↓
Step 1:   メタデータスコア計算          (dps_meta_scorer.py)
  ↓
Step 2:   年代スロット判定              (dps_year_classifier.py)
  ↓
Step 3:   チャンク分割 + Embedding      (dps_chunk_embedder.py)
  ↓
Step 4:   トピック重要度スコア計算      (dps_topic_scorer.py)
  ↓
Step 5:   DPS スコア集約               (dps_aggregator.py)
  ↓
Step 6:   結果記録                      (dps_record_writer.py)
  ↓
[出力] .dps/[path_hash].json（全中間値）
      priority_queue.jsonl（DPS スコア降順）
      rank.md（人間用レポート）
      rank.json（構造化ランキング）
        ↓
        Phase 1（FastPass）へ引き継ぎ
```

※ 全モジュールは `dps_config_loader.py` を介して `dps_config.json` および環境変数の設定値を読み込む。

***

## 3. スコアリング式

ファイル \( f \) の DPS スコアを次のように定義する：

\[
\text{DPS}(f) = \alpha \cdot S_{\text{meta}}(f) \;+\; (1-\alpha) \cdot \frac{\sum_{i=1}^{N} w_i \cdot S_{\text{topic}}(c_i)}{\sum_{i=1}^{N} w_i}
\]

- \( S_{\text{meta}}(f) \)：メタデータ7シグナルの加重合計（LLM不要）
- \( S_{\text{topic}}(c_i) \)：チャンク \( c_i \) のトピック重要度
- \( w_i \)：チャンク位置重み（先頭・末尾を 1.2 倍、中間を 1.0 倍）
- \( \alpha = 0.30 \)：メタと意味の混合比（`dps_config.json` で変更可）

### トピック重要度

\[
S_{\text{topic}}(c_i) = \max_{p \in P} \cos(\vec{c_i},\, \vec{p}) \;\cdot\; D(t_f) \;\cdot\; A(y_f)
\]

- \( P \)：業務プロトタイプベクトル群（起動時1回生成）
- \( D(t_f) \)：時間減衰（指数、半減期30日）
- \( A(y_f) \)：年代スロット重み

***

## 4. Step 1：メタデータスコア（S_meta）

LLM を一切使わずに即時算出する。

### 4-1. シグナル一覧

| シグナル | 算出方法 | 重み |
|---|---|---|
| mtime 新しさ | 指数減衰（半減期30日）`exp(-0.693 * days_old / 30)` | 0.28 |
| キーワードヒット | フォルダパストークン ∩ シード語辞書 の割合 | 0.25 |
| **Semantic Path Score** | ファイル名＋パストークンの Embedding cos類似度 | 0.20 |
| ファイル種別 | 拡張子テーブル（`.msg/.eml` = 1.0 〜 `.csv` = 0.3） | 0.13 |
| フォルダパス深さ | 理想深さ3階層からの乖離で減点 | 0.07 |
| サイズフィルタ | 2KB〜20MB = 満点、範囲外は半減 | 0.05 |
| フォルダ内ファイル密度 | 同フォルダ50件超で減点（雑多フォルダ判定） | 0.02 |

合計 1.00

### 4-2. Semantic Path Score のフォールバック

```
sem_score = cos(embed(パストークン + ファイル名stem), prototype_vecs の最大値)
sem_score < 0.20 の場合 → keyword_hit_score × 0.8 で補完
```

ファイル名が `scan001.pdf` のような無意味名のときの精度低下を防ぐ。

### 4-3. シード語辞書（`dps_config.json` で外部管理）

```json
{
  "seed_keywords": [
    "projects", "contracts", "invoice", "legal", "budget",
    "proposal", "minutes", "report", "urgent", "confidential"
  ]
}
```

***

## 5. Step 2：年代スロット判定

フォルダパストークンから年度を正規表現で抽出する。見つからない場合は mtime の年を使う。

### 年代スロット重み（`dps_config.json` で変更可）

| 年度 | 重み `A(y)` |
|---|---|
| 当年（2026） | 1.00 |
| 1年前（2025） | 0.80 |
| 2年前（2024） | 0.60 |
| 3年以上前 | 0.40 |

### 年度抽出ルール

```
正規表現: r'(?:FY)?(\d{4})' でパストークンを検索
マッチ例: "2026", "FY2025", "fy2024"
未検出時: os.stat().st_mtime の年を使用
```

***

## 6. Step 3：チャンク分割 + Embedding

LLM は使わない。固定サイズのスライドウィンドウで分割し、`nomic-embed-text`（Ollama 既存）でベクトル化する。

### チャンク分割仕様

| 条件 | 処理 |
|---|---|
| ファイルサイズ < 2KB | 1チャンク固定（分割しない） |
| 本文テキスト < 500文字 | 1チャンク固定 |
| それ以外 | 500文字スライド、200文字オーバーラップ |

Semantic Chunking（LLM境界検出）は**使わない**。Phase 1 の SBTA がその役割を担うため、DPS では高速な固定分割で十分だ。

### キャッシュ戦略

`{source_path}:{mtime}` の sha256 をキーに `dps_embed_cache.jsonl` へ保存。mtime が変わっていなければ再 Embedding をスキップする。

***

## 7. Step 4：トピック重要度スコア計算（S_topic）

### 業務プロトタイプテキスト（起動時1回だけ Embedding）

```json
[
  "project contract invoice proposal budget",
  "meeting minutes agenda action items",
  "legal compliance regulation policy",
  "urgent escalation critical incident",
  "technical specification design architecture",
  "customer client stakeholder communication",
  "report analysis result summary"
]
```

### 時間減衰の計算

```python
import math
days_old = (now_ts - file_mtime) / 86400
D = math.exp(-0.693 * days_old / 30)  # 半減期30日
```

### チャンクごとのスコア算出

```python
cos_sim  = max(cosine(chunk_vec, pv) for pv in prototype_vecs)
S_topic  = cos_sim * D * A_year
```

***

## 8. Step 5：DPS スコア集約

チャンク位置重みを適用して加重平均を取る。

```python
POSITION_WEIGHT = {"head": 1.20, "tail": 1.20, "middle": 1.00}

# 先頭2チャンク・末尾2チャンクを head/tail として判定
weighted_sum = sum(w_i * S_topic_i for ...)
weight_total = sum(w_i for ...)
S_topic_agg  = weighted_sum / weight_total

DPS_score = 0.30 * S_meta + 0.70 * S_topic_agg
```

***

## 9. Step 6：結果記録（.dps/ ディレクトリ）

分析結果は、分析対象ディレクトリ直下の `.dps/` ディレクトリに一括保存される。

### 出力ファイル一覧

1.  **個別分析結果 (`[path_hash].json`)**:
    各ファイルの詳細な分析データ。途中計算値、チャンクごとのスコア、コンテンツハッシュ等を含む。
2.  **ランキングレポート (`rank.md`)**:
    人間が確認するためのサマリー。重要度順にソートされた表形式のレポート。
3.  **構造化ランキング (`rank.json`)**:
    プログラムや外部ツールから利用するための構造化データ。
4.  **処理順序リスト (`priority_queue.jsonl`)**:
    Phase 1 (FastPass) 等の後続システムが直接読み込むための、軽量な処理待ち行列リスト。

### 記録フォーマット (個別 JSON)
...
```json
{
  "source_path": "/mnt/share/projects/ACME/2026/invoice_202604.pdf",
  "scored_at": "2026-05-15T13:20:00Z",
  "dps_score": 0.801,
  "meta": {
    "mtime_score": 0.91,
    "keyword_hit_score": 0.60,
    "semantic_path_score": 0.82,
    "filetype_score": 0.80,
    "path_depth_score": 0.75,
    "size_score": 1.00,
    "folder_density_score": 0.90,
    "S_meta": 0.792
  },
  "year_slot": 2026,
  "year_weight": 1.00,
  "time_decay": 0.95,
  "chunks": [
    {
      "chunk_index": 0,
      "position": "head",
      "position_weight": 1.20,
      "text_preview": "ACME社 請求書 2026年4月分...",
      "embedding_model": "nomic-embed-text",
      "top_prototype": "project contract invoice proposal budget",
      "cos_sim": 0.87,
      "S_topic": 0.826
    },
    {
      "chunk_index": 1,
      "position": "middle",
      "position_weight": 1.00,
      "text_preview": "品目: バーコードリーダー 数量...",
      "embedding_model": "nomic-embed-text",
      "top_prototype": "project contract invoice proposal budget",
      "cos_sim": 0.79,
      "S_topic": 0.750
    }
  ],
  "S_topic_aggregated": 0.791,
  "topics_detected": [
    "project contract invoice proposal budget"
  ]
}
```

***

## 10. 出力仕様：`priority_queue.jsonl`

DPS スコア降順でソートしたファイルリスト。Phase 1 の `file_walker.py` が処理する順序をこのファイルで上書きする。

```json
{"rank": 1, "source_path": "/mnt/share/projects/ACME/2026/invoice_202604.pdf", "dps_score": 0.801, "year_slot": 2026}
{"rank": 2, "source_path": "/mnt/share/contracts/NDA_202603.docx",             "dps_score": 0.774, "year_slot": 2026}
{"rank": 3, "source_path": "/mnt/share/projects/ACME/2025/proposal_draft.pptx","dps_score": 0.721, "year_slot": 2025}
```

***

## 11. DPS Complete の完了基準

| 条件 | 内容 |
|---|---|
| 全ファイルスコア済み | `priority_queue.jsonl` のエントリ数 == `file_walker` が列挙したファイル数 |
| キャッシュ整合 | 全 `.dps/[path_hash].json` が存在し、`scored_at` が記録済み |
| スコア値妥当性 | 全エントリの `dps_score` が 0.0〜1.0 の範囲内 |

完了後、`dps_checkpoint.json` に `dps_complete: true` および `total_files` を記録して Phase 1 起動を許可する。

***

### 12. 再実行・差分処理

```
.dps/ 配下の JSON に記録された file_hash と現在のファイルハッシュが一致 → スコア計算をスキップして JSON を再利用
ハッシュが不一致 または JSON 不在 → 該当ファイルを再スコアリング
```


***

## 13. プログラム構成

```
dps/
├── dps_config.json          # シード語・年代重み・α・半減期・プロトタイプテキスト
├── dps_checkpoint.json      # DPS 完了状態・差分管理
├── dps_embed_cache.jsonl    # Embedding キャッシュ（path:mtime → vec）
├── priority_queue.jsonl     # Phase 1 連携用キュー
├── sources/                 # Python ソースコード
│   ├── dps_runner.py        # エントリポイント・全体オーケストレーション
│   ├── dps_init.py          # プロトタイプベクトル生成（起動時1回）
│   ├── dps_config_loader.py # 設定読み込み（環境変数上書き対応）
│   ├── dps_meta_scorer.py   # Step 1：S_meta 計算（7シグナル）
│   ├── dps_year_classifier.py # Step 2：年代スロット判定・A(y)計算
│   ├── dps_chunk_embedder.py  # Step 3：固定幅チャンク分割 + Embedding
│   ├── dps_topic_scorer.py  # Step 4：S_topic 計算（cos・時間減衰・年代重み）
│   ├── dps_aggregator.py    # Step 5：チャンク位置重み付き集約 → DPS スコア
│   ├── dps_record_writer.py # Step 6：.dps/[path_hash].json 記録
│   ├── dps_queue_builder.py # priority_queue.jsonl, rank.md/json 生成
│   ├── dps_sensitivity.py   # 感度分析（Spearman ρ 検証）
│   └── dps_checkpoint.py    # チェックポイント管理ロジック
└── tests/                   # ユニットテスト
```

***

## 14. 実行環境

| 項目 | 内容 |
|---|---|
| 実行ホスト | 会社 Linux サーバ（Ollama/Gemma4 稼働機と同一） |
| ファイルアクセス | SMBマウント済みネットワークドライブを `os.walk` で直接巡回 |
| LLM API | 使用しない（Embedding のみ） |
| Embedding モデル | `nomic-embed-text`（`http://localhost:11434/api/embed`、環境変数で変更可） |
| 実行タイミング | Phase 1 起動前に手動実行。以降は週次 cron で差分処理 |
| 処理速度目安 | 1万ファイル・平均3チャンク/ファイルで 30分以内（Embedding律速） |

### 環境変数による設定上書き

`dps_config_loader.py` は以下の環境変数を検知し、`dps_config.json` の値を動的に上書きする。

- **Ollama 関連**:
  - `OLLAMA_HOST`: `ollama_url` のホスト部分を置換（例: `http://remote-gpu:11434`）
  - `OLLAMA_KEEP_ALIVE`: `ollama_keep_alive` を設定
  - `OLLAMA_CONTEXT_LENGTH`: `ollama_context_length` を設定
- **DPS 汎用**:
  - `DPS_[KEY]`: `dps_config.json` 内の任意のキーを上書き（例: `DPS_ALPHA=0.5`）

***

## 巻末：重要用語集

### DPS（Document Priority Score：資料重要度スコア）
メタデータシグナルとセマンティック類似度を組み合わせてファイルの業務重要度を 0.0〜1.0 で表現したスコア。LLM を使わずに高速算出できる点が特徴で、Phase 1 の処理順序を制御する唯一の役割を担う。

### プロトタイプベクトル（Prototype Vectors）
業務的に重要なトピックを代表する短文テキストをあらかじめ Embedding したベクトル群。起動時に1回だけ生成してメモリに保持し、全チャンクのコサイン類似度計算に使い回す。Snell et al.（2017）「Prototypical Networks for Few-shot Learning」の概念を静的スコアリングに適用したものだ。

### 時間減衰（Temporal Decay）
ファイルの最終更新日時からの経過日数に応じて重要度を減衰させる係数。指数減衰（半減期30日）を採用し、業務ファイルが30日で約半分の重要度になることを表現する。Kanhabua & Nørvåg（2010）の Temporal Information Retrieval 研究に基づく。

### 年代スロット（Year Slot）
フォルダパストークンまたは mtime から抽出した年度区分。当年のファイルを最優先（重み1.00）とし、年度が古くなるほど段階的に重みを下げる。`dps_config.json` で業種・会社ごとにカスタマイズ可能だ。

### Semantic Path Score
ファイル名とフォルダパストークンを結合してテキスト化し、Embedding してプロトタイプベクトルとのコサイン類似度を取ったスコア。キーワード辞書に登録されていない略語や複合語（例：`acme_wh_scan_err`）を意味的に捕捉できる。スコアが低い場合はキーワードヒットスコアでフォールバックする。

### 感度分析（Sensitivity Analysis）
重みパラメータを ±20% 摂動させたときに `priority_queue.jsonl` の上位100件の順位がどれだけ変わるかを Spearman の順位相関係数 ρ で検証する分析。ρ > 0.9 であれば重み設計は安定と判断できる。`dps_sensitivity.py` で実行する。
��
