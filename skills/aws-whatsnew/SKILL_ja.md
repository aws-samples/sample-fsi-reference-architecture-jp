---
name: aws-whatsnew
description: AWS What's New の公式 API からアナウンスを取得します。AWS の最新発表、新機能、サービスアップデートについて質問された場合に使用します。日付範囲でのフィルタリングをサポートし、見出し、URL、サービス名、カテゴリを含む構造化 JSON を返します。
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# AWS What's New

日付フィルタリング機能付きで AWS What's New アナウンスを取得します。

## 使用方法

スクリプトを実行:

```bash
uv run --project scripts scripts/aws_whatsnew.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--size 1-100]
```

## パラメータ

- `--start-date`: 開始日 (デフォルト: UTC での今日)
- `--end-date`: 終了日 (デフォルト: UTC での今日)
- `--size`: API リクエストあたりの件数、1-100 (デフォルト: 100)

## 出力

各項目に以下を含む JSON 配列:

- `postDateTime`: アナウンス日
- `headline`: アナウンスタイトル
- `headlineUrl`: URL パス (`https://aws.amazon.com` をプレフィックスとして付加)
- `service`: AWS サービス名 (例: `amazon-connect`)
- `category`: カテゴリ名 (例: `security-identity-and-compliance`)

## レスポンススキーマ

出力形式の JSON Schema 定義は [references/response-schema.json](references/response-schema.json) を参照してください。

## 例

```bash
# 今日のアナウンスを取得
uv run --project scripts scripts/aws_whatsnew.py

# 特定の日付範囲のアナウンスを取得
uv run --project scripts scripts/aws_whatsnew.py --start-date 2026-02-01 --end-date 2026-02-11
```

## 免責事項

このスキルは AWS の非公式エンドポイント (`https://aws.amazon.com/api/dirs/items/search`) に依存しています。この API は公式にドキュメント化されておらず、予告なく変更される可能性があります。その場合、このスキルは動作しなくなる可能性があります。