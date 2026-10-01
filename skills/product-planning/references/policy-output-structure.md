
# 商品企画ワークショップ: 成果物の出力構造

商品企画ワークショップ(`product-planning` スキルの Mode A 本番 および Mode B Dry Run)の成果物は、このファイルで定義する規約に従って出力します。

> **パス規約**: このファイルで言及する `product-planning/...` および `dry-run-scenarios/...` のパスは、すべて **ユーザーのワーキングディレクトリ(kiro-cli 実行時のカレントディレクトリ)直下** を基点とします。スキルディレクトリ配下ではありません。詳しくは SKILL.md 冒頭の「パス規約」セクションを参照してください。

## 1. ディレクトリ階層

成果物は **企画ごとのサブフォルダ** に格納します。複数の企画を試したときに混ざらず、どの企画のどのフェーズかを一目で判別できるようにするためです。シナリオ(Dry Run の入力)と成果物(Dry Run / 本番の出力)は対称の階層を持ちます。

```
dry-run-scenarios/                   … Dry Run 用シナリオ(入力)
├── marketing/
│   └── {project-slug-A}/
│       ├── persona.md
│       └── data/                    … 任意
└── working-backwards/
    └── {project-slug-B}/
        └── persona.md

product-planning/                    … 成果物(Dry Run / 本番 共通の出力先)
├── marketing/
│   ├── {project-slug-A}/            … Dry Run 実行時はシナリオ名と同じ
│   │   ├── 01_environment.md
│   │   ├── 02_strategy.md
│   │   └── ...
│   └── {project-slug-C}/            … 本番ワークショップで新規作成された企画
└── working-backwards/
    └── {project-slug-B}/
        ├── 01_pr_faq.md
        ├── 02_pr_faq.md
        ├── 03_pr_faq.md
        └── ...
```

**禁止事項**: `product-planning/marketing/environment.md` のようにモード直下にフェーズ成果物を置いてはいけません。必ず `{project-slug}/` を挟みます。`dry-run-scenarios/` 側も同様で、モード直下に `persona.md` を置いてはいけません。

## 2. 企画スラッグ(project-slug)の決定

### フォーマット

- 英数字 + ハイフンの kebab-case(例: `smart-insurance`, `kids-fintech-app`, `home-iot-for-seniors`)
- 小文字のみ、先頭と末尾はハイフン禁止
- 3〜40 文字程度を目安とします

### 決定フロー

本番ワークショップ(`product-planning` スキルの Mode A)では、モード選択後・Step 1 プロンプト読み込み前に必ず以下を実施します。

1. 対象モードの既存企画ディレクトリを一覧します(例: `product-planning/marketing/` 配下のサブディレクトリ)
2. 既存企画がある場合、参加者に「既存の企画を継続しますか? それとも新規企画ですか?」と確認します
   - 継続の場合: 該当ディレクトリを選んでもらい、そのスラッグをそのまま使います
   - 新規の場合: 次のステップへ進みます
3. 新規企画の場合、参加者に企画のテーマ(英語の短い名前)をヒアリングします
   - 参加者が日本語で答えた場合は AI がスラッグ候補を 2〜3 個提示し、選んでもらいます
   - 受け取った文字列は正規化します: 空白をハイフンに、小文字化、特殊文字を除去
4. 確定後、`product-planning/{mode}/{project-slug}/` ディレクトリを作成して作業を開始します

Dry Run(`product-planning` スキルの Mode B)では、`dry-run-scenarios/{mode}/{scenario-name}/` に配置されたシナリオを選び、そのシナリオ名をそのまま project-slug として使います(例: `dry-run-scenarios/marketing/ai-insurance-direct/` → 成果物は `product-planning/marketing/ai-insurance-direct/` 配下)。モードは **シナリオが配置されたディレクトリ** で決まるので、Dry Run 起動時にモードを選んでから、そのモード配下のシナリオ一覧を提示します。

## 3. ファイル命名規則

各ファイル名には **ステップ番号の接頭語** を付けます。これによりファイラー上でフェーズ順に並び、開くべきファイルが自明になります。

### マーケティング起点モード(`product-planning/marketing/{project-slug}/`)

| ステップ  | 種別                           | ファイル名                              |
| --------- | ------------------------------ | --------------------------------------- |
| Step 1    | 計画ファイル                   | `01_environment_plan.md`                |
| Step 1    | 成果物(ハブ / 単一ファイル)  | `01_environment.md`                     |
| Step 1    | 分割ファイル(PEST)           | `01_environment_pest.md`                |
| Step 1    | 分割ファイル(5 Forces)       | `01_environment_5forces.md`             |
| Step 1    | 分割ファイル(3C)             | `01_environment_3c.md`                  |
| Step 1    | 分割ファイル(Value Chain)    | `01_environment_valuechain.md`          |
| Step 2    | 計画ファイル                   | `02_strategy_plan.md`                   |
| Step 2    | 成果物(ハブ / 単一ファイル)  | `02_strategy.md`                        |
| Step 2    | 分割ファイル(クロス SWOT)    | `02_strategy_cross_swot.md`             |
| Step 2    | 分割ファイル(商品コンセプト) | `02_strategy_concept.md`                |
| Step 2    | 分割ファイル(STP)            | `02_strategy_stp.md`                    |
| Step 3    | 計画ファイル                   | `03_concept_plan.md`                    |
| Step 3    | 成果物(ハブ / 単一ファイル)  | `03_concept.md`                         |
| Step 3    | 分割ファイル                   | `03_concept_sheet.md` など              |
| Step 4    | 計画ファイル                   | `04_plan_plan.md`                       |
| Step 4    | 成果物(ハブ / 単一ファイル)  | `04_plan.md`                            |
| Step 4    | 分割ファイル                   | `04_plan_4p4c.md` / `04_plan_promotion.md` / `04_plan_execution.md` など |
| 全体      | 問題・リスクレポート(Dry Run / Mode B 時のみ生成) | `issues.md`                             |

### Working Backwards モード(`product-planning/working-backwards/{project-slug}/`)

| ステップ | 種別                                     | ファイル名                          |
| -------- | ---------------------------------------- | ----------------------------------- |
| Step 1   | 計画ファイル                             | `01_pr_faq_plan.md`                 |
| Step 1   | 成果物(初稿)                           | `01_pr_faq.md`                      |
| Step 2   | 計画ファイル                             | `02_review_plan.md`                 |
| Step 2   | 成果物(改訂版、新規ファイル)           | `02_pr_faq.md`                      |
| Step 2   | 補足資料(顧客体験)                     | `02_review_customer_experience.md`  |
| Step 2   | 補足資料(実現性)                       | `02_review_solution.md`             |
| Step 2   | 補足資料(ビジネスモデル)               | `02_review_business_model.md`       |
| Step 3   | 計画ファイル                             | `03_final_review_plan.md`           |
| Step 3   | 成果物(最終版、新規ファイル)           | `03_pr_faq.md`                      |
| Step 3   | エグゼクティブサマリ                     | `03_executive_summary.md`           |
| 全体     | 問題・リスクレポート(Dry Run / Mode B 時のみ生成) | `issues.md`                         |

Working Backwards の PR/FAQ は **各フェーズごとに新規ファイル** を作成する方針です。

- Step 1 で `01_pr_faq.md`(初稿)を作成します
- Step 2 で `01_pr_faq.md` をベースに深掘り結果を反映し `02_pr_faq.md`(改訂版)を**新規作成**します
- Step 3 で `02_pr_faq.md` をベースに最終レビュー結果を反映し `03_pr_faq.md`(最終版)を**新規作成**します

前フェーズのファイルは上書きせず保持します。これにより、企画がどのように進化したかを後から 3 ファイルの差分で振り返れます。

## 4. 相互参照の書き方

別ステップの成果物を参照するときは、同じ `{project-slug}/` 配下の相対パスで記載します。

- 良い例: `02_strategy.md` から `[環境分析](./01_environment.md)` を参照
- 悪い例: `../environment.md` のように `{project-slug}/` の外へ出てしまうパス
- 悪い例: ワーキングディレクトリ(CWD)からの絶対パスを埋め込む

## 5. 参加者への案内

参加者には、セッション開始時に新しい出力構造を明示します。

```
📁 このワークショップの成果物は以下に出力します:
   product-planning/{mode}/{project-slug}/
   ├── 01_xxx.md  … Step 1 の成果物
   ├── 02_xxx.md  … Step 2 の成果物
   └── ...
```

番号接頭語により、ファイラーやエクスプローラーで並べたときにフェーズ順に並びます。
