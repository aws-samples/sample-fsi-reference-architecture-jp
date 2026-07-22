---
name: customer-context-manager
description: >-
  LLM単独では把握できないお客様固有のコンテキストを自動管理する —
  略称、社内システム名、組織構造、キーパーソン、商談履歴、関係メモなど。
  お客様ごとにMarkdownファイルとして整理し、XDG Base Directory Specificationに従って保存する。
  会話中にお客様名が出てきたら自動的にコンテキストを読み込み、
  新しい情報が出てきたら自動的に更新する — 明示的なコマンドは不要。
  お客様名への言及、営業ミーティングの議論、商談や案件への参照、
  担当者についての質問、お客様関連タスクの実行時に使用する。
  お客様情報の登録・更新・検索・確認にも使用する。
  トリガーキーワード: "customer context", "顧客コンテキスト", "お客様情報",
  "顧客情報", "取引先", "account", "customer", "お客様", "略称登録",
  "組織図", "キーパーソン", "商談メモ", "関係者", "コンテキスト更新",
  "context update", "who is", "誰", "どの会社".
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Customer Context Manager

LLM単独では把握できないお客様固有のコンテキストを自動管理する。
会話中にお客様が登場したら関連コンテキストを自動的に読み込み、
新しい情報が判明したら自動的に更新する — ユーザーの明示的な指示は不要。

## このスキルが存在する理由

LLMは、人間が打ち合わせ・メール・社内議論を通じて蓄積するお客様固有の知識を持たない：

- **略称・別名**: お客様固有の略称がある（社内でしか通じないもの）
- **システム名・プロジェクト名**: 「Any Core Banking」のような社内システム名は公開されていない
- **組織構造**: 誰が誰に報告し、誰が意思決定し、誰が予算を持つか
- **関係履歴**: 過去の提案、結果、注意点、好み
- **コミュニケーション上の特性**: 好むチャネル、応答パターン、会議スタイル

このコンテキストがなければ、AIエージェントは汎用的な出力を生成するか、誤った前提で動作する。

## データ保存

設定は [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/) に従う。
コンテキストデータはユーザーが設定可能なディレクトリに保存する。

- **コンテキストデータ**: `~/Documents/customer-context/`（デフォルト、設定ファイルで変更可能）
- **設定**: `$XDG_CONFIG_HOME/customer-context-manager/`（デフォルト: `~/.config/customer-context-manager/`）

### ディレクトリ構造

```
~/Documents/customer-context/
├── customers/
│   ├── <customer-slug>/
│   │   ├── profile.md          # 会社概要、別名、業種
│   │   ├── people.md           # このお客様の担当者（パートナー含む）
│   │   ├── organization.md     # 組織構造、意思決定フロー、変更履歴
│   │   ├── systems.md          # 既知のシステム、技術スタック、制約
│   │   ├── history.md          # 重要な転換点（CRMと重複する活動ログではない）
│   │   ├── terms.md            # お客様固有の用語集
│   │   └── notes.md            # 自由メモ、コミュニケーション上の注意点
│   └── ...
├── people/
│   ├── internal.md             # 社内メンバー（複数のお客様に跨がる）
│   └── partners.md            # パートナー企業（お客様横断の情報）
└── index.md                    # マスターインデックス: slug → 表示名 + 別名 + グループ
```

### 設定

```
$XDG_CONFIG_HOME/customer-context-manager/
└── config.md                   # ユーザー設定とスキーマカスタマイズ
```

## 初回セットアップ

初回起動時（`config.md` が存在しない場合）：

1. XDGパスを解決（環境変数を尊重し、未設定ならデフォルトにフォールバック）
2. ディレクトリ構造を作成
3. `config.md` をデフォルト値で作成：
   ```markdown
   # Customer Context Manager Configuration

   ## Data Directory
   - data_directory: ~/Documents/customer-context

   ## Preferences
   - auto_update: true          # 会話から自動的にコンテキストを更新する
   - auto_read: true            # お客様名が出たら自動的にコンテキストを読み込む
   - confirm_updates: false     # 更新前に確認する（慎重モード用にtrueに設定）
   - language: ja               # コンテキストファイルの主要言語
   - git_enabled: true          # gitで変更を追跡する（更新時に自動コミット）

   ## Schema
   デフォルトテンプレートを使用。カスタマイズはこのディレクトリ内のテンプレートファイルを編集。
   ```
4. `index.md`、`people/internal.md`、`people/partners.md` を空テンプレートで作成
5. セットアップ完了をユーザーに通知

## コア動作

### 自動コンテキスト読み込み

会話中にお客様名・別名・略称が出現した場合：

1. `index.md` でマッチするエントリを検索（別名のファジーマッチ）
2. 該当するお客様ディレクトリのファイルを読み込む
3. 読み込んだコンテキストを暗黙的に応答に活用する — 聞かれない限り生データを表示しない

インデックスに見つからない場合は内部的に記録する。会話の中でエントリ作成に
十分な情報が得られたら、自動的に作成する。

### 自動コンテキスト更新

会話中に新しいお客様情報が出てきた場合（打ち合わせ、ユーザーの発言、
処理中のドキュメントなど）：

1. 新しい事実を特定：名前、役職、システム名、決定事項、好み
2. 更新すべきファイルを判断
3. 即座に書き込む（`confirm_updates: true` の場合は事前に確認）
4. 保存内容を簡潔に報告（1行、冗長にしない）

更新は追記型 — 既存の内容を削除せず新しい情報を追加する。
すべてのエントリに日付を付与し、鮮度を追跡可能にする。

### 何を保存すべきか

迷ったら保存する。ストレージコストは無視できるレベルであり、今は重要でなく
見える情報が後から必要になることがある。一般的なガイドライン：

- **常に保存**: 人名＋役職/部署、システム名、用語、組織変更、重要な意思決定、関係性の力学
- **日付付きで保存**: 提案とその結果、発見された技術的制約、競合情報、コミュニケーション上の好み
- **CRMに任せる**: 詳細な活動ログ、打ち合わせごとのメモ、商談ステージの変更。
  CRM連携スキルが利用可能であれば、ここにデータを複製するのではなくオンデマンドで問い合わせる

ユーザーは特定のエントリに `[!important]` をインラインで付けることができる。
自動的な効果はないが、コンテキストを読む際の視覚的なシグナルとして機能する。

### ソース追跡

情報の出所を記録し、後から検証可能にする。形式：

- **テーブル内**: `Source` 列を追加する。ローカルや口頭のソースにはプレーンテキスト
  （例：`account-plan 2026-05-12`、`meeting 2026-03-19`）を使用する。
  URLがある場合はMarkdownリンクを使用する
  （例：`[activity 2026-01-28](https://crm.example.com/...)`）。
- **散文セクション**: 重要な事実にはMarkdown脚注を使用する：
  ```markdown
  - 契約額: $10M/3年[^1]

  [^1]: account-plan 2026-05-12
  [^2]: [activity 2026-03-19](https://crm.example.com/task/xxx)
  ```

すべての行にソース注釈を付ける必要はない — 後から検証が必要になりうる事実
（財務数値、重要な意思決定、日付、引用）にのみ付与する。
ローカルファイルパスはソースとして有用でないため省略する。

### 人物の分類

お客様の `people.md` に人物を追加する前に、`people/internal.md` や
`people/partners.md` に既に存在しないか確認する。お客様との打ち合わせで
言及された名前が、社内メンバーやパートナーである可能性がある。手順：

1. `people/internal.md` で名前を検索
2. `people/partners.md` で名前を検索
3. 見つかった場合、お客様の `people.md` に重複登録しない — 新しい情報があれば既存エントリを更新
4. どちらにも見つからない場合、お客様の `people.md` にお客様担当者として追加

人物の所属（お客様 vs 社内 vs パートナー）が不明な場合、会話の文脈から
手がかりを得る（例：「うちのチーム」「自社側」、「技術コンサルタント」「営業担当」などの
肩書き）。それでも曖昧な場合はユーザーに確認する。

### 曖昧な人名の扱い

同じお客様内に同姓の人物が存在する場合がある。人物を記録する際：

- 可能であれば部署や文脈情報を含めて区別する
- 記録時点で区別できない場合は、分かっている情報を保存し曖昧さを注記する
  （例：「田中様（部署不明、営業部の田中様とは別人の可能性）」）
- 後から情報が判明して区別が明確になった時点でエントリを更新する

完璧な特定をブロッカーにしない — 部分的な情報でも無いよりは良い。

### お客様の改称・統合

お客様のアイデンティティは時間とともに変化する: 社名変更、合併、分社、吸収など。
**slug と表示名は常に現在の正しい名前に合わせる** — 古い slug を固定したままにしない。
改称は単一のファイル編集ではなく、旧名を指したままの参照が残らないよう、次の追従更新を
自動で伴う1つの操作とする。

お客様を**改称**する場合（slug `<old>` → `<new>`）:

1. **ディレクトリを移動** `customers/<old>/` → `customers/<new>/`（git有効時は `git mv`
   で履歴を保つ）。
2. **`index.md` を更新**: 新しい Slug と表示名にし、**旧名と旧 slug を Aliases に追加**して
   旧名でも引けるようにする。
3. **`profile.md` に変更を記録**: 改称/合併/分社の内容と日付を Basic Information か Notes に
   記す（何が何になったか、理由）。
4. **流入参照を修正**: データディレクトリ内で旧 slug/旧名を検索し、それを指す箇所をすべて
   更新する — 例: `people/partners.md` の Customers 列、他のお客様ファイル内のグループ親子
   参照、（内部コンパニオン有効時は）`internal-config.md` のアカウントグルーピング。
5. **コミット**: 意図が分かるメッセージにする（例: `rename any-bank → any-bank-renamed: company
   renamed 2026-04-01`）。

2社が**統合**する場合（2 → 1）:

- 残す slug = 新しい/正しい社名 とする。
- 消える側のファイル内容を残す側にマージする（履歴・人・systems — 蓄積した情報を失わない）。
- 消える側の slug・表示名・旧 Aliases を残す側の Aliases に集約する。
- 合併と日付を `profile.md` に記録し、旧ディレクトリと index 行を削除する（`git mv`/commit で
  履歴は残す）。

**分社・分割**（1 → 2）の場合は、新しいお客様エントリを作成し、関連する共有コンテキストを
コピーし、両者の Aliases/profile で相互参照して系譜を辿れるようにする。

指針: slug と表示名は常に *現在の正しい* 名前を反映し、Aliases と profile.md が *履歴* を
保持して旧名でも解決できるようにする。

### 手動コマンド

ユーザーは明示的に指示することもできる：

| コマンド | アクション |
|---------|--------|
| `<customer>の情報を見せて` / `show context for <customer>` | お客様の全コンテキストを表示 |
| `<customer>を登録して` / `register <customer>` | 新しいお客様エントリを対話的に作成 |
| `<info>を保存して` / `save <info>` | 特定の情報を明示的に保存 |
| `顧客一覧` / `list customers` | 登録済みお客様の一覧表示 |
| `<customer>の<category>を更新` / `update <category> for <customer>` | 特定のコンテキストファイルを編集 |
| `検索: <term>` / `search <term>` | 全お客様コンテキストを横断検索 |

## ファイルテンプレート

コンテキストファイルの期待される密度と品質の完全な例は
[references/sample-context.md](references/sample-context.md) を参照。
以下のテンプレートは最低限の構造を示す — サンプルで示されている豊かさを目指す。

### index.md

```markdown
# Customer Index

| Slug | Display Name | Aliases | Industry | Group | Status |
|------|-------------|---------|----------|-------|--------|
| any-bank | Any Bank | AB | Banking | Any Group | Active |
| any-securities | Any Securities | AS | Securities | Any Group | Active |
| any-insurance | Any Insurance | AI | Insurance | - | Active |
```

Group列は企業グループの関係性（親会社、系列、持株会社の関連）を表す。
単独のお客様には `-` を使用する。

**Aliases は名前解決の入口である。** 会話中（あるいは社内ツール上）でこのお客様を指して
使われ得る呼称を *すべて* ここに入れる。どの名前が出てきても引けるようにするため:

- 略称・通称（例: `AB`）
- 正式な法人名と短縮形（例: `株式会社` / `Inc.` の有無）
- 日本語名・英語名
- **改称後も残す旧称**（旧名でも引けるように）
- グループ名・ブランド名としての呼称
- 現実と異なる社内CRM上の登録名（内部コンパニオンスキルがここに書き戻す）

既知のお客様であるはずの名前で解決に失敗したら、その名前を Aliases に追加し、次回の
照合が成功するようにする。

### customers/<slug>/profile.md

```markdown
# <Display Name>

## Basic Information
- Formal name: 
- Common aliases: 
- Industry: 
- Size: 
- Headquarters: 
- Website: 

## Relationship Summary
- First engagement: 
- Current status: 
- Primary contact: 

## Revenue
<!-- 営業側の財務情報：契約、取引規模、利用額 -->

## Strategic Context
<!-- お客様のビジネス優先事項と自社エンゲージメントとの関係 -->

## Notes
```

### customers/<slug>/people.md

```markdown
# People — <Display Name>

## Customer Contacts

| Name | Department | Title | Role in Decisions | Email | Notes |
|------|-----------|-------|-------------------|-------|-------|

## Partner Contacts

このお客様の特定プロジェクトにアサインされているパートナー。

| Name | Company | Role | Project/Context | Email | Notes |
|------|---------|------|-----------------|-------|-------|
```

### customers/<slug>/organization.md

```markdown
# Organization — <Display Name>

## Current Structure
<!-- 自社のエンゲージメントに関連する組織階層を記述 -->

## Decision-Making Flow
<!-- 誰が何を承認するか：技術判断、予算、契約 -->

## Key Departments

## Change History
<!-- 組織再編を追跡する。新しいものが上。 -->

### YYYY-MM-DD: <変更内容>
- Old: <旧構造>
- New: <新構造>
- Impact: <エンゲージメントへの影響>
```

### customers/<slug>/systems.md

```markdown
# Systems & Technology — <Display Name>

## Known Systems

| System Name | Category | Technology | Notes |
|-------------|----------|-----------|-------|

## Technical Constraints
<!-- 規制要件、セキュリティポリシー、ネットワーク制約 -->

## Technology Preferences
```

### customers/<slug>/history.md

```markdown
# History — <Display Name>

重要な転換点のみ記録する — 定例会議のログではない。
詳細な活動履歴はCRMが利用可能であればそちらを参照する。

## Key Events

### YYYY-MM-DD: <Event Title>
- What happened: 
- Significance: 
- Impact on relationship: 

## Past Proposals

| Date | Topic | Outcome | Reason |
|------|-------|---------|--------|
```

### customers/<slug>/terms.md

```markdown
# Terminology — <Display Name>

## Glossary

| Term | Meaning | Context | Date Added |
|------|---------|---------|------------|
```

### customers/<slug>/notes.md

```markdown
# Notes — <Display Name>

## Communication Preferences
- Preferred channel: 
- Response patterns: 
- Meeting preferences: 

## Competitive Landscape
<!-- 他ベンダー、競合ソリューション -->

## Sensitivities
<!-- 慎重に扱うべきトピック、過去のネガティブな経験 -->

## Free Notes
```

### people/internal.md

```markdown
# Internal Team Members

複数のお客様対応に関わる可能性のある社内メンバーを管理する。

| Name | Role | Expertise | Notes |
|------|------|-----------|-------|
```

### people/partners.md

```markdown
# Partner Companies

お客様横断のパートナー情報。プロジェクト固有のアサインは各お客様のpeople.mdを参照。

| Company | Relationship | Domains | Key Contacts | Customers |
|---------|-------------|---------|--------------|-----------|
```

## コンテキスト読み込み優先度

会話に応じて読み込むファイルを優先度で判断する：

1. **常に読み込む**: `index.md`（軽量、名前解決に必要）
2. **お客様名が出た時**: `profile.md`, `terms.md`（アイデンティティと語彙）
   - お客様がグループに属する場合（index.mdのGroup列）、親会社の`terms.md`も
     読み込み、グループ横断の用語を把握する
3. **人について議論する時**: `people.md`, `people/internal.md`
4. **アーキテクチャ・技術の議論時**: `systems.md`
5. **エンゲージメント計画時**: `history.md`, `organization.md`, `notes.md`
6. **レポートや提案書作成時**: そのお客様の全ファイル

## Slug生成

お客様のslugは表示名から生成する：
- 小文字
- スペースと特殊文字をハイフンに置換
- 連続ハイフンを除去
- 日本語名はローマ字表記を使用（例：`any-bank`）
- 短く認識しやすいslugにする

## 検索

お客様横断検索：
- `customers/` と `people/` 配下の全Markdownファイルを検索
- ファイルパスと周辺コンテキスト付きで結果を返す
- 日本語テキストの完全一致・ファジーマッチの両方をサポート

## 他スキルとの連携

このスキルは他のスキルが利用できるコンテキストを提供する。他のスキルが
お客様関連の作業（レポート、提案書、議事録）を処理する際、このスキルの
コンテキストを自動的に読み込み、正確な名前・用語・背景情報を提供する。

このスキルは特定のCRMや外部ツールに依存しない。ローカルのMarkdownファイルのみで
動作する。CRM連携が必要な場合は、別のコンパニオンスキルとして実装する。

## ファイル書き込みスコープ

このスキルが書き込む場所：
- `$XDG_CONFIG_HOME/customer-context-manager/`（設定）
- 設定ファイルで指定されたデータディレクトリ（デフォルト: `~/Documents/customer-context/`）

自身のSKILL.mdやこれら以外の場所のファイルは変更しない。

## Gitバージョン管理

`git_enabled: true`（デフォルト）の場合、データディレクトリをgitリポジトリとして管理する：

### セットアップ
- 初回セットアップ時、データディレクトリがリポジトリでなければ `git init` を実行
- 必要に応じて `.gitignore` を作成（デフォルトは空 — すべてを追跡）

### 自動コミット
- コンテキスト更新（ファイル作成・変更）のたびに、変更ファイルをステージしてコミット
- コミットメッセージ形式: `update <customer-slug>/<file>: <簡潔な説明>`
- 例：
  - `update any-bank/people: add Tanaka-san (Digital Banking)`
  - `update any-bank/terms: add CORE-Next terminology`
  - `update index: register new customer Any Insurance`
- 同一会話内の複数変更は実用的な範囲で1コミットにまとめる

### メリット
- コンテキスト変更の完全な履歴（タイムスタンプ付き）
- 差分確認と誤った更新の取り消しが可能
- プライベートリモートへのpushでバックアップも可能

### 無効化
config.mdで `git_enabled: false` に設定すると無効化。git操作は一切行われない。
