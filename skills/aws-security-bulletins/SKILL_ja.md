---
name: aws-security-bulletins
description: >
  AWSが公開したセキュリティ速報（脆弱性情報やセキュリティに関するアナウンス）を取得・検索・詳細表示します。
  AWSセキュリティ速報の確認、検索、一覧取得、または特定のBulletinの詳細取得を行いたい場合にこのスキルを使用します。
  トリガーキーワード: "security bulletin", "AWS CVE", "AWS vulnerability", "セキュリティ速報",
  "脆弱性情報", "AWS脆弱性", "security advisory".
license: MIT No Attribution
compatibility: Python 3.11以上、uv、およびaws.amazon.comへのインターネットアクセスが必要
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# AWS Security Bulletins

## このスキルを使用するタイミング

以下の場合にこのスキルを使用します:
- AWS Security Bulletins の一覧取得・検索
- AWSの脆弱性情報やCVEの確認
- 特定のAWS Security BulletinのIDまたはURLによる詳細取得
- AWSセキュリティアナウンスの監視

## ワークフロー

まず、ユーザーが **(1) 一覧/検索** を行いたいのか、**(2) 特定のBulletinの詳細** を取得したいのかを判断し、適切なスクリプトコマンドを実行します。

### 1. 一覧取得 / 検索

**1-a. スクリプト引数の決定:**
- `--start-date` / `--end-date`: ISO 8601形式の日付。デフォルトは直近1年間。「今日」「今週」「先月」などの自然言語を適切な日付に変換します。
- `--keyword`: タイトルフィルタリング用のキーワード（OR条件、大文字小文字区別なし）。複数指定可能。
- `--no-date-filter`: 日付フィルタリングを完全に無効化。

ユーザーの意図が曖昧な場合は、スクリプト実行前に確認を行います。

**1-b. スクリプトの実行:**

```bash
uv run --project scripts scripts/fetch_bulletins.py list [--start-date YYYY-MM-DDTHH:MM:SSZ] [--end-date YYYY-MM-DDTHH:MM:SSZ] [--keyword kw1 kw2 ...] [--no-date-filter]
```

**1-c. 出力をMarkdownテーブルとしてフォーマット:**

スクリプトは [list-response-schema.json](references/list-response-schema.json) に準拠したJSONを出力します。以下の形式で表示します:

| # | Bulletin ID | Title | Published | Severity | URL |
|---|-------------|-------|-----------|----------|-----|
| 1 | AWS-2025-032 | Key Commitment Issues… | 2025-12-17 | important | https://… |

**1-d. ユーザーに確認:** 特定のBulletinの詳細を取得するかどうかを確認します。

### 2. Bulletin詳細の取得

**2-a. 入力の確認:** Bulletin ID（例: `AWS-2025-032`, `2026-003-AWS`）または完全なURLが提供されていることを確認します。これらは一覧出力の `url` フィールドから取得できます。

**2-b. サブエージェントとしての実行を推奨:** 呼び出し元のコンテキストウィンドウを圧迫しないよう、可能であればサブエージェントとして実行します。

**2-c. スクリプトの実行:**

```bash
uv run --project scripts scripts/fetch_bulletins.py detail <BULLETIN_ID_OR_URL>
```

スクリプトは [detail-response-schema.json](references/detail-response-schema.json) に準拠したJSONを出力します。`body` フィールドにBulletinの完全なHTMLが含まれます。

**2-d. 要約または回答:** ユーザーに特定の質問がある場合は、body内容に基づいて回答します。特に質問がなければ、影響バージョン、説明、解決策、CVE識別子を含む簡潔な要約を提供します。

## 出力スキーマ

- 一覧レスポンス: [references/list-response-schema.json](references/list-response-schema.json)
- 詳細レスポンス: [references/detail-response-schema.json](references/detail-response-schema.json)
- エラーレスポンス: [references/error-response-schema.json](references/error-response-schema.json)

## スクリプト詳細

- **ランタイム:** Python 3.11+、標準ライブラリのみ、`uv run --project scripts` で実行
- **ロギング:** `logging` モジュールでstderrに出力。`LOG_LEVEL` 環境変数で制御（デフォルト: `WARN`）
- **リトライ:** Exponential backoff、最大3回
- **出力:** JSONをstdoutに出力。エラー時はJSONをstderrに出力し、非ゼロ終了コードで終了。

## 使用例

直近1年のBulletinを一覧取得:
```bash
uv run --project scripts scripts/fetch_bulletins.py list
```

S3関連のBulletinを検索:
```bash
uv run --project scripts scripts/fetch_bulletins.py list --keyword S3 encryption
```

特定の日付範囲でBulletinを取得:
```bash
uv run --project scripts scripts/fetch_bulletins.py list --start-date 2025-01-01T00:00:00Z --end-date 2025-12-31T23:59:59Z
```

日付フィルタなしで全件取得:
```bash
uv run --project scripts scripts/fetch_bulletins.py list --no-date-filter
```

特定のBulletinの詳細を取得:
```bash
uv run --project scripts scripts/fetch_bulletins.py detail AWS-2025-032
uv run --project scripts scripts/fetch_bulletins.py detail https://aws.amazon.com/security/security-bulletins/AWS-2025-032/
```

## 免責事項

このスキルは AWS の非公式エンドポイント (`https://aws.amazon.com/api/dirs/items/search`) に依存しています。この API は公式にドキュメント化されておらず、予告なく変更される可能性があります。その場合、このスキルは動作しなくなる可能性があります。