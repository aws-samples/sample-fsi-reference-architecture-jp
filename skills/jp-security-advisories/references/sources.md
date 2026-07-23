# 情報源リファレンス

本スキルが参照する公開エンドポイントと、ソースごとに使用可能なカテゴリ値、
利用規約 URL の一覧です。

## ソース一覧

| `--sources` 値 | 名称 | バックエンド | エンドポイント | 形式 |
|---|---|---|---|---|
| `jpcert` | JPCERT/CC RSS | RSS + HTML | `https://www.jpcert.or.jp/rss/jpcert.rdf` | RSS 1.0 (RDF) → 詳細は HTML パース |
| `jpcert-all` | JPCERT/CC 統合 RSS | RSS + HTML | `https://www.jpcert.or.jp/rss/jpcert-all.rdf` | RSS 1.0 (RDF) → 詳細は HTML パース |
| `myjvn-alert` | IPA 注意警戒情報（MyJVN API） | API | `https://jvndb.jvn.jp/myjvn?method=getAlertList&feed=hnd` | Atom 1.0 + mod_sec 3.0（XSD あり、JSON 出力可） |
| `myjvn-vuln` | JVN iPedia 脆弱性データベース（MyJVN API） | API | `https://jvndb.jvn.jp/myjvn?method=getVulnOverviewList&feed=hnd` および `method=getVulnDetailInfo` | JVNRSS 3.2（一覧）、VULDEF 3.2（詳細）（XSD あり） |

## バックエンドの選定理由

`myjvn-alert` および `myjvn-vuln` は MyJVN API のみで完結します。HTML パースに
依存しないことで以下のメリットがあります：

- サイト構造変更による破綻に対して堅牢（XSD で型定義済）
- 文字エンコーディング問題が発生しない（UTF-8 固定）
- サーバ側で CPE / キーワード / CVSS / 期間でフィルタ可能
- ページング対応（`startItem` / `maxCountItem`）
- 影響を受ける製品、CVSS スコア、CVE などが構造化フィールドで取得可能

`jpcert` は JPCERT/CC が構造化 API を提供していないため、RSS による一覧取得と
HTML による本文取得の組み合わせを継続使用します。

## カテゴリ値

`--category` で指定できる値はソースごとに異なります。

### `jpcert` / `jpcert-all`

JPCERT は単一フィードに複数種別を混在させて配信します。本スキルは `<link>` の
URL パターンから種別を推定します。

| カテゴリ値 | URL パターン | 内容 |
|---|---|---|
| `alert` | `/at/` を含む | 注意喚起・緊急報告 |
| `weekly-report` | `/wr/` を含む | Weekly Report |
| `tsubame` | `/tsubame/` を含む | TSUBAME レポート |
| `news` | `/newsflash/` を含む | お知らせ・ニュースフラッシュ |
| `blog` | `blogs.jpcert.or.jp` ホスト | JPCERT/CC Eyes ブログ |
| `other` | 上記以外 | その他（採用情報など） |

### `myjvn-alert`

MyJVN API は Atom の `<category term=...>` でセキュリティ深刻度を返します。
本スキルは以下の値で正規化します。

| カテゴリ値 | API での `term` 例 | 内容 |
|---|---|---|
| `critical` | `Critical`, `緊急` | 緊急 |
| `important` | `Important`, `重要` | 重要 |
| `low` | `Low`, `注意` | 注意 |
| `info` | `Information`, `参考` | 情報・参考 |

### `myjvn-vuln`

| カテゴリ値 | 判定基準 |
|---|---|
| `critical` | CVSS Critical |
| `high` | CVSS High |
| `medium` | CVSS Medium |
| `low` | CVSS Low |
| `none` | CVSS None |

`--severity` でも同等のフィルタが可能です（`--severity` はサーバ側、
`--category` はクライアント側）。

## MyJVN API パラメータ対応

スキルの引数 → MyJVN API パラメータ：

### `myjvn-alert`（getAlertList）

| スキル引数 | API パラメータ | 備考 |
|---|---|---|
| `--start-date YYYY-MM-DD` ／ `--end-date YYYY-MM-DD` | `datePublished=YYYY` または `dateFirstPublished=YYYY` | API は年単位のみ。年範囲をクライアント側で日単位に絞り込み |
| `--limit N` | `maxCountItem=min(N, 50)` | API 制限：1ページ最大 50。N>50 はページング |
| `--keywords` | （未対応） | クライアント側でフィルタ |
| `--category` | （未対応） | クライアント側でフィルタ |
| `--cve` | （未対応） | クライアント側でフィルタ |

### `myjvn-vuln`（getVulnOverviewList）

| スキル引数 | API パラメータ |
|---|---|
| `--start-date` / `--end-date` + `--date-mode public` | `datePublicStartY/M/D` ＋ `datePublicEndY/M/D` |
| `--start-date` / `--end-date` + `--date-mode published`（既定） | `datePublishedStartY/M/D` ＋ `datePublishedEndY/M/D` |
| `--start-date` / `--end-date` + `--date-mode first-published` | `dateFirstPublishedStartY/M/D` ＋ `dateFirstPublishedEndY/M/D` |
| `--keywords kw` | `keyword=<kw>`（複数キーワードの場合は別リクエストを発行し OR マージ） |
| `--severity` | `severity=n\|l\|m\|h\|c` |
| `--cpe` | `cpeName=cpe:/a:vendor:product` |
| `--limit N` | `maxCountItem=min(N, 50)` ／ ページングは `startItem` |

### `myjvn-vuln`（getVulnDetailInfo）

| スキル引数 | API パラメータ |
|---|---|
| `<URL_OR_ID>` | `vulnId=JVNDB-YYYY-NNNNNN` |

## 既知の制約

- JPCERT/CC は注意喚起単独 / Weekly Report 単独 / JVN 単独のフィードを提供して
  いません。本スキルは URL パターンによる種別推定でフィルタを実現しています。
  サイト構造変更時に破綻する可能性があります。
- `getAlertList` の日付フィルタは**年単位のみ**です。日単位の絞り込みは
  クライアント側で行います。
- `getVulnDetailInfo` の `maxCountItem` 上限は 10 です。複数 ID 取得時は
  ページング処理を行います。
- `getVulnOverviewList` の `maxCountItem` 上限は 50 です。
- MyJVN API のレスポンス XML は、`status:Status/@retCd` が 1 の場合エラーです
  （`errCd` / `errMsg` を確認）。
- MyJVN API は高頻度アクセスを避けるべきです。`--cache-dir <path>` を指定して
  キャッシュを有効化した場合に限り、ETag / Last-Modified を尊重し、同一クエリは
  可能な限りキャッシュから返します。`--cache-dir` 未指定の既定動作では、毎回
  新規にフェッチします（ローカルへの書き込みは一切発生しません）。

## 各機関の利用規約

| 機関 | 利用規約 URL |
|---|---|
| JPCERT/CC | https://www.jpcert.or.jp/policy.html |
| MyJVN API（利用上の規約） | https://jvndb.jvn.jp/apis/termsofuse.html |
| MyJVN API（FAQ） | https://jvndb.jvn.jp/apis/myjvnapi_faq.html |
| JVN | https://jvn.jp/nav/jvnhelp.html |
| JVN iPedia | https://jvndb.jvn.jp/nav/help.html |

**MyJVN API の帰属表示について**: IPA より、本サービスを利用して開発した
アプリケーションによって表示される情報には、**MyJVN API により提供された
ものである旨を表示**するよう協力依頼がなされています
（[MyJVN API トップページ](https://jvndb.jvn.jp/apis/index.html)）。
詳細は [NOTICES.md](../NOTICES.md) を参照してください。

実装では、各機関のサーバ負荷に配慮し以下を遵守します。

- HTTP `If-None-Match` / `If-Modified-Since` を用いた条件付きリクエスト
- リトライは指数バックオフ、最大 3 回
- `User-Agent` に本リポジトリの URL を含める
