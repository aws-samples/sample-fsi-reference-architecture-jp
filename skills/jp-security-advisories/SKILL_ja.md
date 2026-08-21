---
name: jp-security-advisories
description: >
  JPCERT/CC（注意喚起 / Weekly Report）および MyJVN API（IPA 注意警戒情報、
  JVN iPedia 脆弱性データベースの構造化APIサービス）から、日本国内のセキュリティ
  アドバイザリおよび脆弱性情報を取得・検索するスキルです。利用者が国内セキュリティ
  動向の確認、注意喚起の一覧、特定アドバイザリの詳細取得を行いたいときに使用します。
  トリガー語：「JPCERT」「JPCERT/CC」「IPA セキュリティ」「MyJVN」「JVN」「JVN iPedia」
  「注意喚起」「重要なセキュリティ情報」「セキュリティアドバイザリ」「脆弱性情報」
  「国内セキュリティ動向」「CVE 日本語」。
license: MIT No Attribution
compatibility: Python 3.11+、uv、jpcert.or.jp / jvndb.jvn.jp へのインターネット接続が必要。
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Japan Security Advisories（国内セキュリティアドバイザリ）

JPCERT/CC と MyJVN API の各エンドポイントが公開するセキュリティアドバイザリを
横断的に検索・取得するスキルです。

## 利用シーン

利用者が次のような操作を求めるときに使用します。

- **JPCERT/CC** の注意喚起、Weekly Report、TSUBAME レポート、JPCERT/CC Eyes
  ブログを一覧・検索する
- **IPA 注意警戒情報** を MyJVN API（`getAlertList`）経由で一覧・検索する
- **JVN iPedia 脆弱性データベース** を MyJVN API（`getVulnOverviewList`）で
  検索する。CPE、キーワード、CVSS 深刻度、複数の日付軸でサーバ側フィルタが可能
- JVN iPedia エントリの構造化詳細（`getVulnDetailInfo`）を取得する。影響を
  受ける製品、CVSS スコア、関連 CVE、対策情報を含む
- JPCERT/CC アドバイザリの本文を取得する（HTML パース。JPCERT は構造化API
  を提供していないため）

本スキルは `aws-security-bulletins`（AWS 側の脆弱性情報）と相補的です。

## 情報源

| `--sources` 値 | バックエンド | カバレッジ |
|---|---|---|
| `jpcert` | RSS（`https://www.jpcert.or.jp/rss/jpcert.rdf`）+ HTML | JPCERT/CC 注意喚起、緊急報告、直近 Weekly Report の脆弱性情報 |
| `jpcert-all` | RSS（`https://www.jpcert.or.jp/rss/jpcert-all.rdf`）+ HTML | `jpcert` + お知らせ + 新規 JVN |
| `myjvn-alert` | **MyJVN API** `getAlertList`（Atom XML / JSON） | IPA 注意警戒情報。関連参照リンクが構造化済み |
| `myjvn-vuln` | **MyJVN API** `getVulnOverviewList` + `getVulnDetailInfo` | JVN iPedia 脆弱性データベース |

`jpcert` は JPCERT/CC が構造化 API を提供していないため HTML パースが必要です。
`myjvn-alert` と `myjvn-vuln` は MyJVN API のみで完結し、XSD で型定義された
XML が返却されます。

`--sources` の既定値: `jpcert myjvn-alert myjvn-vuln`。

エンドポイント詳細・パラメータ対応・既知制約は
[references/sources.md](references/sources.md) を参照してください。

## ワークフロー

最初に **(1) 一覧／検索** か **(2) 個別アドバイザリの詳細** かを判別し、
該当のサブコマンドを実行します。

### 1. 一覧／検索

#### 1-a. スクリプト引数の決定

| 引数 | 説明 | 既定値 |
|---|---|---|
| `--sources` | `jpcert`, `jpcert-all`, `myjvn-alert`, `myjvn-vuln`, `all` のいずれか（複数可） | `jpcert myjvn-alert myjvn-vuln` |
| `--start-date` | ISO 形式 `YYYY-MM-DD`（含む） | 90 日前 |
| `--end-date` | ISO 形式 `YYYY-MM-DD`（含む） | 当日 |
| `--no-date-filter` | 日付フィルタを無効化 | off |
| `--date-mode` | `myjvn-vuln` 用：`public` / `published` / `first-published`（どの日付軸でフィルタするか） | `published` |
| `--keywords` | スペース区切りキーワード（OR、大文字小文字無視）。`myjvn-vuln` はサーバ側、それ以外はクライアント側でフィルタ | （なし） |
| `--category` | カテゴリで絞り込み（[references/sources.md](references/sources.md) 参照） | （なし） |
| `--cve` | CVE 番号（複数可、OR） | （なし） |
| `--severity` | `myjvn-vuln` 用：`none` / `low` / `medium` / `high` / `critical` | （なし） |
| `--cpe` | `myjvn-vuln` 用：CPE 識別子（例 `cpe:/a:apache:tomcat`） | （なし） |
| `--limit` | 返却件数の上限 | 無制限 |
| `--format` | `json` / `csv` / `markdown` | `json` |
| `--cache-dir` | このディレクトリを指定したときのみ、ETag/Last-Modified による HTTP キャッシュを有効化します。**未指定時はローカルにファイルを一切書きません。** | （無効） |

意図が曖昧な場合（ソース・期間・キーワードのいずれも指定なし）は、既定値で
進めるかを利用者に確認してから実行します。

#### 1-b. サブコマンド

```bash
uv run --project scripts scripts/fetch_advisories.py list-sources
uv run --project scripts scripts/fetch_advisories.py list [...]
uv run --project scripts scripts/fetch_advisories.py detail [...]
```

`list-sources` は利用可能なソース、バックエンドのエンドポイント、ソース別
カテゴリ値を表として出力します。

#### 1-c. スクリプト実行

```bash
uv run --project scripts scripts/fetch_advisories.py list \
  [--sources <s1> <s2> ...] \
  [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--no-date-filter] \
  [--date-mode public|published|first-published] \
  [--keywords <kw1> <kw2> ...] \
  [--category <cat>] \
  [--cve <CVE-YYYY-NNNN> ...] \
  [--severity none|low|medium|high|critical] \
  [--cpe <cpe-string>] \
  [--limit N] \
  [--format json|csv|markdown]
```

出力 JSON は [references/list-response-schema.json](references/list-response-schema.json)
に準拠します。

#### 1-d. 出力の整形

JSON で受け取った場合、利用者には Markdown 表で提示します。

| # | ソース | カテゴリ | 日付 | タイトル | CVE | 深刻度 | URL |

`--format markdown` を指定した場合はスクリプト自体が Markdown 表を出力します。

#### 1-e. フォローアップ

利用者に、特定アドバイザリの詳細を取得するか確認します。

### 2. アドバイザリ詳細の取得

#### 2-a. 入力の確認

URL、または可能な場合は ID：

- JPCERT URL（`https://www.jpcert.or.jp/at/.../...`）
- JVN iPedia URL または ID（`JVNDB-YYYY-NNNNNN`）— `getVulnDetailInfo` を使用
- IPA セキュリティアラートの URL — `myjvn-alert` の一覧出力に含まれる
  関連参照リンクで構造化済みのため、別途 detail 呼び出しは不要です

#### 2-b. detail はサブエージェントでの実行を推奨

詳細レスポンスはサイズが大きい場合があります（特に影響を受ける製品が多い
`myjvn-vuln` エントリ）。呼び出し元エージェントのコンテキストを消費しないよう、
サブエージェントで実行してください。

#### 2-c. スクリプト実行

```bash
uv run --project scripts scripts/fetch_advisories.py detail \
  --source <jpcert|myjvn-vuln> \
  <URL_OR_ID> \
  [--format json|markdown]
```

出力 JSON は [references/detail-response-schema.json](references/detail-response-schema.json)
に準拠します。

`myjvn-vuln` の場合、レスポンスは完全に構造化されています（HTML パース不要）。
タイトル、概要、影響を受ける製品（vendor / product / CPE）、評価者ごとの
CVSS スコア、関連アドバイザリ、対策情報がすべて VULDEF 3.2 XML から抽出されます。

`jpcert` の場合、ページを取得してベストエフォートで既知見出し（概要 / 対象 /
対策 / 軽減策 / 参考情報）に分割します。見出しパターンに一致しないとき
`sections` は空で、その場合は `body_text` を使用してください。

#### 2-d. 要約または回答

利用者の具体的な質問がある場合は、構造化フィールド（`affected`, `cvss`,
`references`, `mitigation`）または `body_text` から回答します。そうでなければ、
影響を受ける製品／バージョン、概要、CVSS、対策、CVE 番号を含む簡潔な
サマリを返します。

## 出力スキーマ

- 一覧レスポンス: [references/list-response-schema.json](references/list-response-schema.json)
- 詳細レスポンス: [references/detail-response-schema.json](references/detail-response-schema.json)
- エラーレスポンス: [references/error-response-schema.json](references/error-response-schema.json)

## 情報源リファレンス

[references/sources.md](references/sources.md) には以下を記載します。

- 各ソースのエンドポイントとバックエンド（RSS+HTML / MyJVN API）
- MyJVN API パラメータ対応
- ソース別カテゴリ値
- 各機関の利用規約 URL

## キャッシュの挙動（金融機関環境向けの設計）

スクリプトは既定でローカルにファイルを **一切書き込みません**。
キャッシュを使う場合のみ `--cache-dir <path>` を明示します。

- 各レスポンスは `{sha256(url)}.body` と `{sha256(url)}.meta.json` の
  ペアで保存
- 2 回目以降の実行では `If-None-Match` / `If-Modified-Since` を付与し、
  サーバが `304 Not Modified` を返した場合はキャッシュを使用
- キャッシュ書き込みでエラーが発生しても、ネットワーク取得結果が
  優先され処理は継続

外部スクリプトによるローカル書き込みを許容しない金融機関環境を
想定し、上記を既定挙動としています。

## スクリプト仕様

- **ランタイム**: Python 3.11+、標準ライブラリのみ。`uv run --project scripts` で実行
- **ログ**: `logging` モジュールで stderr に出力。`LOG_LEVEL` 環境変数で制御（既定 `WARN`）
- **リトライ**: HTTP リクエストごとに最大 3 回、指数バックオフ
- **出力**: stdout に JSON。エラー時は stderr に JSON、非 0 終了
- **ネットワーク**: `jpcert.or.jp` / `blogs.jpcert.or.jp` / `jvndb.jvn.jp`

## 実行例

直近 90 日を既定ソースから取得:
```bash
uv run --project scripts scripts/fetch_advisories.py list
```

直近30日の JVN iPedia エントリのうち CVSS 深刻度 high 以上を取得:
```bash
uv run --project scripts scripts/fetch_advisories.py list \
  --sources myjvn-vuln --severity high \
  --start-date $(date -v-30d +%Y-%m-%d)
```

特定 CVE を含むアドバイザリを検索:
```bash
uv run --project scripts scripts/fetch_advisories.py list \
  --sources all --cve CVE-2026-0265 CVE-2025-20333
```

JVN iPedia エントリの構造化詳細を取得:
```bash
uv run --project scripts scripts/fetch_advisories.py detail \
  --source myjvn-vuln JVNDB-2026-018267
```

JPCERT/CC アドバイザリの本文を取得:
```bash
uv run --project scripts scripts/fetch_advisories.py detail \
  --source jpcert https://www.jpcert.or.jp/at/2026/at260015.html
```

## Disclaimer

各情報源は、それぞれの公開組織に帰属します。

- **JPCERT/CC** — Japan Computer Emergency Response Team Coordination Center
- **IPA** — 独立行政法人 情報処理推進機構（MyJVN API 経由）
- **JVN iPedia** — IPA／JPCERT/CC により運営（MyJVN API 経由）

公開されている HTML および API レスポンスは、各アドバイザリの**正本（一次情報）**
です。本スキルは検索・要約の利便性を提供するものであり、影響評価や対策実施に
あたっては必ず原典のページまたは API レスポンスを参照してください。再配布等
に関しては各機関の利用規約が適用されます。利用規約 URL は
[references/sources.md](references/sources.md) と [NOTICES.md](NOTICES.md) に
記載しています。

**MyJVN API の帰属表示について**: IPA より、MyJVN API を利用して取得した
情報を表示するアプリケーションには、**MyJVN API により提供されたものである旨**を
表示するよう協力依頼がなされています。本スキルが `myjvn-alert` または
`myjvn-vuln` ソースから取得した情報を利用者に提示する際は、この旨の表示に
ご協力ください。各アイテムの `source` フィールドにより、当該データが MyJVN
API 由来かどうかを判別できます。
