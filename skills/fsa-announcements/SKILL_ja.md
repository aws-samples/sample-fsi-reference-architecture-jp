---
name: fsa-announcements
description: >
  日本の金融庁（FSA）が公開する新着情報を、公式 RSS フィード（直近 15 件程度）
  と過年度アーカイブページ recent{YYYY}.html（2021 年まで遡及可能）の組み合わせ
  で取得し、期間とカテゴリで絞り込むスキルです。対象カテゴリは「報道発表」
  「記者会見」「審議会等」「国際関係」「イベント」「刊行物」「採用」「調達」
  「その他」の 9 種類です。金融機関に関わる規制動向、審議会の答申、監督指針改正案、
  その他金融行政発表の追跡に利用します。
  トリガー語：「金融庁」「FSA」「報道発表」「監督指針」「審議会」「金融庁 新着」
  「金融庁 ニュース」「金融行政方針」。
license: MIT No Attribution
compatibility: >
  Python 3.11+ と uv、www.fsa.go.jp へのインターネット接続が必要です。
  Python 外部パッケージは使用しません（標準ライブラリのみ）。
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# 金融庁 新着情報取得スキル（FSA Announcements）

金融庁が公表する新着情報を、公式 RSS フィードと年度別アーカイブページ
`recent{YYYY}.html` の双方から取得し、期間とカテゴリで絞り込むスキルです。

## このスキルを使うとき

- 直近の **報道発表**（金融行政の方針発表・監督指針改正案など）を確認
  したいとき
- 任意の期間（2021 年から本日まで）の発表をカテゴリ別にリスト化
  したいとき
- **審議会等** の答申・報告を期間で抽出したいとき
- 別経路で見かけた発表が金融庁の正式リストにいつ・どのカテゴリで
  掲載されたかを照合したいとき

`boj-statistics`（日本銀行の時系列統計）および `jp-security-advisories`
（JPCERT/MyJVN による国内セキュリティ情報）と相補的に利用できます。

## 情報源

| ソース | バックエンド | カバレッジ |
|---|---|---|
| 新着 RSS | `https://www.fsa.go.jp/fsaNewsListAll_rss2.xml` | 全カテゴリ混在の最新 15 件程度。RFC 822 RSS 2.0 形式ですが、`pubDate` のタイムゾーンが非標準の `JST` 略称になっており、本スキルで補正済みです。|
| `recent{YYYY}.html` | `https://www.fsa.go.jp/recent/recent{YYYY}.html` | 西暦年単位の HTML アーカイブ。月別の `<ul>` で構成されており、2021 年までは遡及可能。1 年で約 1,100 件以上の発表が掲載されています。|

RSS は件数が少ない代わりに常に最新が反映されます。recent ページは件数
が多く、カテゴリラベルが構造化されている（公式の `<span>` ラベル）ため
権威性に勝ります。両方を組み合わせるときは URL 単位で重複排除し、
recent ページのエントリ（カテゴリが確実）を優先します。

エンドポイントの仕様や既知の制限は
[references/sources.md](references/sources.md) を参照してください。

## ワークフロー

### 1. 引数を決める

| 引数 | 説明 | 既定値 |
|---|---|---|
| `--start-date` | 取得対象期間の開始日（`YYYY-MM-DD`、JST 暦）。**必須**。| — |
| `--end-date` | 終了日（`YYYY-MM-DD`、両端を含む）。| 本日（JST）|
| `--source` | `rss` / `recent` / `both` のいずれか | `both` |
| `--category` | カテゴリ絞り込み（複数指定可）。`報道発表` / `記者会見` / `審議会等` / `国際関係` / `イベント` / `刊行物` / `採用` / `調達` / `その他` | （指定なし → 全カテゴリ） |
| `--cache-dir` | このディレクトリを指定したときのみ、ETag/Last-Modified による HTTP キャッシュを有効化します。**未指定時はローカルにファイルを一切書きません。** | （無効） |
| `--diagnose` | 各ソースの取得件数を stderr に出力（FSA 側 HTML 構造変化の早期検知に有用） | OFF |
| `--log-level` | `DEBUG` / `INFO` / `WARNING` / `ERROR`（`FSA_LOG_LEVEL` 環境変数でも指定可） | `WARNING` |

利用者の意図が曖昧（期間も指定もない）な場合は、期間の確認を取って
から実行してください。

### 2. 実行

```bash
uv run --project scripts scripts/fetch_announcements.py \
  --start-date <YYYY-MM-DD> [--end-date <YYYY-MM-DD>] \
  [--source rss|recent|both] \
  [--category 報道発表 ...] \
  [--cache-dir <PATH>] [--diagnose]
```

JSON 配列を標準出力に書き出します（1 オブジェクト = 1 件、`published`
降順）。スキーマは [references/fields.md](references/fields.md) を参照
してください。

### 3. 整理して回答

- 利用者が一覧を求めている場合は JSON をそのまま提示
- 要約を求めている場合はカテゴリ・日付別に整理し、利用者の関心に
  関わる項目（例：報道発表内の監督指針改正案など）を強調しつつ
  FSA の URL を併記

### 4. 大きい範囲はサブエージェントで実行

複数年に跨る取得は数千件規模になります。親エージェントの context を
圧迫しないよう、サブエージェントで実行してください。

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

## スクリプト詳細

- **ランタイム**：Python 3.11+、標準ライブラリのみ、`uv run --project scripts` で起動
- **ロギング**：`logging` モジュールで stderr に出力（`--log-level` または `FSA_LOG_LEVEL`）
- **リトライ**：指数バックオフ、HTTP 1 リクエストあたり最大 3 回
- **出力**：標準出力に JSON、エラーは stderr に出力し終了コード非 0
- **ネットワーク**：`www.fsa.go.jp`

## 利用例

直近 1 週間（カテゴリ無指定）：
```bash
uv run --project scripts scripts/fetch_announcements.py --start-date 2026-06-01
```

四半期分の報道発表のみ：
```bash
uv run --project scripts scripts/fetch_announcements.py \
  --start-date 2026-04-01 --end-date 2026-06-30 \
  --category 報道発表
```

年度（4 月～翌 3 月）通しの報道発表＋審議会等：
```bash
uv run --project scripts scripts/fetch_announcements.py \
  --start-date 2025-04-01 --end-date 2026-03-31 \
  --category 報道発表 --category 審議会等
```

ローカルキャッシュを許可する場合：
```bash
uv run --project scripts scripts/fetch_announcements.py \
  --start-date 2026-06-01 \
  --cache-dir ~/.cache/aws-jp-fsi/fsa-announcements
```

## Disclaimer

本スキルが返す全ての項目は、金融庁が公表しているものです。**金融庁
公式ページが正本** であり、規制対応・業務判断にあたっては必ず原典を
参照してください。本スキルは利便性のためにコンテンツを取得・整形して
返すのみで、内容の正確性を検証・保証するものではなく、上流フィード
の更新でタイトルが書き換わる場合もあります。

**出典表示（PDL 1.0）**：金融庁コンテンツは
[公共データ利用規約（PDL）1.0](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0)
（CC BY 4.0 互換）でライセンスされており、**出典表示が必須** です。
本スキルが返す項目を提示するときは URL を併記し、
「出典：金融庁ウェブサイト」とクレジットしてください。要約・編集
した場合は、その旨も明記する必要があります（[NOTICES.md](NOTICES.md)
を参照）。
