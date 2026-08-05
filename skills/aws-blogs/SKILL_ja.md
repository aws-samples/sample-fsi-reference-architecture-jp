---
name: aws-blogs
description: >-
  AWSブログ記事（サービスガイド、顧客事例、イベントレポート、新機能発表など）を
  公開APIから検索・取得するスキル。英語(en_US)と日本語(ja_JP)のブログは翻訳では
  なく独立したコンテンツである。AWSブログの閲覧・検索・本文取得が必要な場合に
  使用する。トリガーキーワード: AWS blog, AWS ブログ, ブログ検索, ブログ記事,
  blog search, blog article, customer story, 事例, new launch, what's new.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# AWS Blogs スキル

公開ディレクトリAPIを利用してAWSブログ記事を取得・表示する。

## ワークフロー概要

1. ユーザーの意図を判定する: **一覧/検索** か **詳細取得** か（または両方を順次実行）。
2. 対象言語（`en_US` または `ja_JP`）を確認する — ロケールによって記事内容が異なる。
3. `scripts/fetch_blogs.py` を適切なサブコマンドで実行する。
4. 結果をMarkdownテーブル（一覧）または要約（詳細）で提示する。

## 1 — ブログ記事の一覧/検索

### 1-a パラメータの確認

| パラメータ | 決定方法 |
|---|---|
| `--locale` | 不明な場合はユーザーに確認する。`en_US` と `ja_JP` は別の記事セットである。 |
| `--start-date` | 自然言語（「今週」「先月」など）を `YYYY-MM-DD` に変換する。デフォルト: 30日前。 |
| `--end-date` | 同上。デフォルト: 本日。 |
| `--no-date-filter` | 指定すると日付フィルタを無効化し、取得可能な全記事を取得する。`--start-date` と `--end-date` は無視される。 |
| `--keywords` | 任意。複数キーワードはOR条件でタイトルと要約に対して大文字小文字を区別せずマッチする。 |

### 1-b 実行

```bash
uv run --project scripts scripts/fetch_blogs.py list \
  --locale <en_US|ja_JP> \
  --start-date <YYYY-MM-DD> \
  --end-date <YYYY-MM-DD> \
  [--no-date-filter] \
  [--keywords <kw1> <kw2> ...]
```

スクリプトはAPIのページングを自動的に処理し、JSON配列を標準出力に出力する。
`--no-date-filter` を指定すると `--start-date` と `--end-date` は無視され、取得可能な全記事を取得する。
出力スキーマは [list_response_schema.json](references/list_response_schema.json) を参照。

### 1-c 結果の提示

JSON配列をMarkdownテーブルに変換する:

```
| # | タイトル | 日付 | URL |
|---|---------|------|-----|
| 1 | ...     | ...  | ... |
```

結果が少数（10件以下）の場合は要約(excerpt)も含める。多数の場合はコンテキスト節約のため省略する。

### 1-d フォローアップ

一覧の中から詳細を読みたい記事があるかユーザーに確認する（→ ステップ2へ）。

## 2 — ブログ記事の詳細取得

### 2-a 入力の確認

以下のいずれかの識別子が1つ以上必要である:
- 完全なURL（`https://aws.amazon.com/blogs/...` または `https://aws.amazon.com/jp/blogs/...`）
- API ID（`blog-posts-v2#<uuid>`）

いずれの場合も `--locale` が必須である。

### 2-b 実行（サブエージェント推奨）

呼び出し元のコンテキストを圧迫しないよう、可能な限りサブエージェントで実行する。

```bash
uv run --project scripts scripts/fetch_blogs.py detail \
  --locale <en_US|ja_JP> \
  <url_or_id_1> [<url_or_id_2> ...]
```

出力はJSON配列として標準出力に出力される。
出力スキーマは [detail_response_schema.json](references/detail_response_schema.json) を参照。

### 2-c 結果の提示

- ユーザーから具体的な質問がある場合は、コンテンツに基づいて回答する。
- 特に質問がない場合は、記事の内容を要約して呼び出し元に返す。

## エラー処理

致命的エラーはJSON形式で標準エラー出力に書き込まれる。
スキーマは [error_response_schema.json](references/error_response_schema.json) を参照。

## スクリプトリファレンス

- **スクリプト**: `scripts/fetch_blogs.py`（Python 3.11+、`uv run --project scripts` で実行）
- **依存関係**: なし（Python標準ライブラリのみ）
- **ログ**: 環境変数 `LOG_LEVEL`（`DEBUG`, `INFO`, `WARN`, `ERROR`）で制御する。デフォルト: `WARN`。
- **リトライ**: ネットワークエラー時にexponential backoffで最大3回リトライする。

## 免責事項

このスキルは AWS の非公式エンドポイント (`https://aws.amazon.com/api/dirs/items/search`) に依存しています。この API は公式にドキュメント化されておらず、予告なく変更される可能性があります。その場合、このスキルは動作しなくなる可能性があります。