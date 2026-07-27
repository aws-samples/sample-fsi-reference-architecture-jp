---
name: boj-statistics
description: >-
  日本銀行（BOJ）の公開APIから時系列統計データを取得・検索・分析するスキル。
  金利、マーケット、外国為替、マネタリーベース、短観、物価指数、国際収支、
  資金循環など全てのBOJデータベースに対応する。日本のマクロ経済・金融統計の
  取得、BOJデータ系列の検索、為替レートの確認、短観DI値の取得、日本銀行が
  公表する時系列データの探索が必要な場合に使用する。
  トリガーキーワード: BOJ, Bank of Japan, 日銀, 日本銀行, 時系列統計, Tankan,
  短観, 為替, 金利, マネタリーベース, マネーストック, 国際収支, 物価指数,
  資金循環, 日銀統計, 統計データ, FM08, CO, BP01.
license: MIT No Attribution
compatibility: Python 3.11以上およびuvが必要。外部Pythonパッケージは不要（標準ライブラリのみ使用）。
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# BOJ Statistics スキル

日本銀行の時系列統計データ検索サイトAPIを利用して統計データを取得・分析する。

## ワークフロー概要

1. ユーザーの意図を判定する: **データベース探索**、**系列検索**、**データ取得**、**最新値取得** のいずれか。
2. 対象のDB名を特定する — [references/db_list.md](references/db_list.md) を参照すればコマンド実行なしにDB名を把握できる。例えば、為替レートは `FM08`、短観は `CO`、国際収支は `BP01` である。
3. `scripts/boj_statistics_cli.py` を `uv run --project scripts` で適切なサブコマンドで実行する。
4. 結果をテーブル、要約、または生データで提示する。

## 利用可能なサブコマンド

| コマンド | 用途 |
|---------|------|
| `list-db` | 利用可能なBOJデータベース一覧を表示 |
| `get-metadata` | 指定DBの系列メタデータを取得 |
| `search-series` | キーワードでDB内の系列を検索 |
| `get-data` | 系列コード指定でデータ取得（コードAPI） |
| `get-layer` | 階層指定でデータ取得（階層API） |
| `latest` | 指定系列の最新データポイントを取得 |

## 1 — データベース一覧の確認

```bash
uv run --project scripts scripts/boj_statistics_cli.py list-db [--format json|csv|tsv|table] [--lang jp|en]
```

BOJの全データベース名と説明を返す。

## 2 — データベースのメタデータ取得

```bash
uv run --project scripts scripts/boj_statistics_cli.py get-metadata --db <DB名> [--format json|csv|tsv|table] [--lang jp|en]
```

指定DBの全系列コード、名称、期種、収録期間を返す。

## 3 — キーワードによる系列検索

```bash
uv run --project scripts scripts/boj_statistics_cli.py search-series --db <DB名> --keywords <キーワード1> [<キーワード2> ...] [--format json|csv|tsv|table] [--lang jp|en]
```

指定DB内の系列名称に対してOR検索（大文字小文字区別なし）を行う。ユーザーが欲しいデータを説明しているが系列コードを知らない場合に有用である。

`--db all` を指定すると全50データベースを横断検索する。どのDBにデータがあるか分からない場合に有用である。レート制限のため約2分かかるが、`list-db` を先に確認する手順を省略できる。

```bash
uv run --project scripts scripts/boj_statistics_cli.py search-series --db all --keywords マネタリーベース --format table --max-series-size 10
```

## 4 — 系列コード指定でのデータ取得

```bash
uv run --project scripts scripts/boj_statistics_cli.py get-data --db <DB名> --code <コード1>[,<コード2>,...] [--start <YYYYMM>] [--end <YYYYMM>] [--format json|csv|tsv|table] [--lang jp|en]
```

実際のデータ値を取得する。ページネーションは自動処理される。コードはカンマ区切りで複数指定可能である。
1回のリクエスト内の全系列は同じ期種である必要がある。期種が異なる場合は別々に呼び出す。

日付形式は系列の期種に依存する（[references/api_spec.md](references/api_spec.md) § Frequency Codes 参照）:
- 暦年・年度: `YYYY`（例: `2024`）
- 半期・四半期: `YYYYHH` / `YYYYQQ`（例: `202401`）
- 月次・週次・日次: `YYYYMM`（例: `202503`）

## 5 — 階層指定でのデータ取得

```bash
uv run --project scripts scripts/boj_statistics_cli.py get-layer --db <DB名> --layer <階層情報> --frequency <期種> [--start <YYYYMM>] [--end <YYYYMM>] [--format json|csv|tsv|table] [--lang jp|en]
```

階層情報の例: `1,1,1`（特定パス）、`*`（全て）。最大5階層まで指定可能である。

`--frequency` パラメータは必須であり、`CY`, `FY`, `CH`, `FH`, `Q`, `M`, `W`, `D` のいずれかを指定する。
各コードの意味は [references/api_spec.md](references/api_spec.md) § Frequency Codes を参照。
DBによって利用可能な期種が異なるため、事前に `get-metadata` で確認することを推奨する。

## 6 — 最新データポイントの取得

```bash
uv run --project scripts scripts/boj_statistics_cli.py latest --db <DB名> --code <コード1>[,<コード2>,...] [--format json|csv|tsv|table] [--lang jp|en]
```

各系列の最新の観測値のみを返す。簡易的な確認に有用である。

## 共通オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--format` | 出力形式: json, csv, tsv, table | json |
| `--lang` | 言語: jp, en | jp |
| `--output` | ファイル出力先（指定しない場合は標準出力） | stdout |
| `--max-series-size` | 出力する系列数の上限 | 無制限 |
| `--max-item-length` | 系列あたりのデータポイント数上限 | 無制限 |
| `--max-pages` | ページネーション最大リクエスト数 | 20 |

ページネーションは自動処理される。スクリプトはレスポンスの `NEXTPOSITION` トークンを追跡して連続リクエストを行う。
APIの制限値（1リクエストあたり250系列 / 60,000データポイント）の詳細は [references/api_spec.md](references/api_spec.md) § Pagination を参照。

## 典型的なワークフロー

1. ユーザーが探索したい場合: `list-db` → `get-metadata` → `search-series` の順で実行
2. ユーザーがどのDBか分からない場合: `search-series --db all --keywords <キーワード>` で全DB横断検索
3. ユーザーが系列を知っている場合: `get-data` または `latest` を直接実行
4. ユーザーが階層的なデータを求める場合: `get-layer` を実行
5. 大量データの場合は `--max-series-size` と `--max-item-length` で出力サイズを制御

## ユースケース例

### 為替レートの推移を取得
```bash
uv run --project scripts scripts/boj_statistics_cli.py search-series --db FM08 --keywords ドル 円
uv run --project scripts scripts/boj_statistics_cli.py get-data --db FM08 --code FXERD01 --start 202401 --end 202412 --format table
```

### 短観の業況判断DIを取得
```bash
uv run --project scripts scripts/boj_statistics_cli.py search-series --db CO --keywords 業況 大企業 製造業
uv run --project scripts scripts/boj_statistics_cli.py get-data --db CO --code TK99F1000601GCQ01000 --start 202401 --end 202504 --format table
```

### 特定キーワードで統計系列を探索
```bash
uv run --project scripts scripts/boj_statistics_cli.py search-series --db BP01 --keywords 経常収支 --format table
```

## 注意事項

- 系列コードにDB名プレフィックスは含めない。`FXERD01` を使い、`FM08'FXERD01` は使わない。
- 1回の `get-data` リクエスト内の全系列は同じ期種である必要がある。
- 週次・日次の日付パラメータは月次形式（YYYYMM）で指定する。
- APIは高頻度アクセスを遮断する可能性がある。スクリプトは自動的にレート制限を行う。
- メタデータの結果には系列コードが空の階層ヘッダ行が含まれる。これは構造情報であり、データではない。

## エラーハンドリング

エラーはstderrにJSON形式で出力される。`error`, `message`, `status_code`, `message_id`, `api_message` フィールドを含む。
エラーコードの詳細は [references/api_spec.md](references/api_spec.md) を参照。

## スクリプトリファレンス

- **スクリプト**: `scripts/boj_statistics_cli.py`（Python 3.11+、`uv run --project scripts` で実行）
- **パッケージ**: `scripts/boj_statistics/`（クライアントライブラリ）
- **依存関係**: なし（Python標準ライブラリのみ）
- **ログ**: 環境変数 `LOG_LEVEL` で制御（DEBUG, INFO, WARN, ERROR）。デフォルト: WARN。
- **サンプルプロンプト**: 実際のトリガー例と出力は [references/sample-trigger.md](references/sample-trigger.md) を参照。
