---
name: fisc-to-aws-security-agent
description: FISC「金融機関等コンピュータシステムの安全対策基準・解説書」(安対基準) のPDFから、AWS Security Agent の Custom セキュリティ要件パックに取り込むためのソースドキュメント(Markdown)を決定論的に生成する。36MB級のPDFをテキスト化し、基準項目を抽出、ワークロード適合の技術要件を厳選してテーマ別の複数パック(各20項目以下・各2MB以下)に分割し、各項目を name/description/applicability/compliance/remediation の5フィールド構造で記述する。ユーザーが「FISC安対基準をSecurity Agentに取り込みたい」「FISCのカスタム要件パックを作りたい」「安対基準PDFをSecurity Agent用に変換して」などと依頼したときに使用する。誰が実行しても同じ入力から同じ出力になる(再現可能)。
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0.0"
---

# FISC 安対基準 → AWS Security Agent Custom 要件 変換 Skill

> 英語版 / English: [SKILL.md](SKILL.md)
> 本ファイル `SKILL_ja.md` は英語版 `SKILL.md` と同一内容の日本語ミラーです。基盤モデルの
> スキル選択性のため、正となる定義は英語の `SKILL.md` です。日本国内の利用者がカスタマイズ
> して使う場合は、`SKILL_ja.md` を `SKILL.md` にリネームして利用を続けられます。
> 両ファイルの作成・更新はコーディングエージェント(Kiro)が行い、人手では編集しません。

FISC 安対基準の PDF を入力に、AWS Security Agent の **Custom セキュリティ要件パック**へ
アップロードできるソースドキュメント（Markdown）を生成します。

このSkillの設計目標は **「誰がやっても同じ結果になる（決定論的・再現可能）」** ことです。
分類は明示的な定義ファイル、フィールド生成はテンプレートで行い、LLM の即興判断に依存しません。

---

## 前提と制約（必ず守る）

- **入力PDFは利用者が用意する。** 本Skillはリポジトリに著作物PDFを同梱しません。
- **Security Agent はワークロード(アプリ/コード/設計)レベルで評価する。** よって FISC のうち
  設備基準(物理設備)・監査基準(監査プロセス)・純粋な組織統制/人事教育は既定で**除外**します
  （方針B: ワークロード適合の技術要件を厳選）。中心は実務基準＋統制基準の技術項目です。
- **フィールド文字数上限**（Security Agent 仕様）: name 80 / description 500 /
  applicability 10,000 / compliance criteria 10,000 / remediation guidance 10,000（文字）。
- **1パックあたりの項目数は 20 以下**、**1ファイルは 2MB 以下**（アップロード制限）。
- 生成物は下書きです。**取り込み後、Security Agent 上で内容を確認・調整**してください。
- 詳細仕様・パック定義・除外方針・カスタマイズ手順は必ず `reference.md` を参照してください。

---

## ワークフロー

```
FISC PDF
  → 1. extract_pdf : 全文テキスト化(ページマーカー付き)
  → 2. build_items : 基準項目を構造抽出(統/実/設/監 + 項番, title/summary/body/page)
  → 3. classify    : pack_mapping.json に従い 6 テーマパックへ決定論的に分類(適合外は除外)
  → 4. generate    : 各項目を 5 フィールド構造の Markdown に変換(1項目=1セクション)
  → 5. validate    : 文字数・項目数(<=20)・ファイルサイズ(<=2MB)を機械検証
  → output/*.md    → Security Agent の Custom pack へアップロード
```

## 使い方

### 一括実行（推奨）

```bash
python3 ~/.kiro/skills/fisc-to-aws-security-agent/scripts/run_all.py \
    --pdf "<FISC安対基準PDFのパス>" \
    --outdir ./output
```

- `output/NN_<pack_id>.md` が各パック分生成され、`output/manifest.json` に一覧が出ます。
- `--max-items` で1パック上限(既定20)、`--workdir` で中間ファイル出力先を変更できます。
- 最後に検証が走り、`✅ 検証OK` が出れば全制約を満たしています（NGなら終了コード1）。

### 個別ステップ実行

問題切り分けや部分再実行が必要なときは各スクリプトを個別に実行します（`reference.md` 参照）。

### 出力フォーマットの選択（アップロード用 / 手動登録用）

`generate_packs.py` は `--format` で2種類の出力を切り替えられます。

- `--format upload`（既定）: 1パック=1ファイルを Security Agent に**アップロード**して要件を自動生成させる用途。
- `--format manual`: **コンソールで1項目ずつ手動登録**する用途。各項目の5フィールド
  （name / description / applicability / compliance / remediation）を、そのままコピー&ペーストできる
  `text` コードブロックに分割し、各フィールドの**文字数と上限**、**FISC区分・出典ページ**を併記します。

> アップロードでは Security Agent 側の自動再解釈により、項目の分割・統合、英語化、説明文の切り詰め、
> FISC番号(トレーサビリティ)の喪失が起こり得ます。**FISC原文への忠実性・監査証跡を優先する場合は
> `--format manual` で手動登録**してください。

手動登録用の生成例（PDFなしで中間生成物 `classified.json` から再生成）:

```bash
python3 ~/.kiro/skills/fisc-to-aws-security-agent/scripts/generate_packs.py \
    --classified ./output/_work/classified.json \
    --config ~/.kiro/skills/fisc-to-aws-security-agent/config/pack_mapping.json \
    --outdir ./output_manual \
    --format manual
```

### 是正ガイダンスへの AWS対応方法案の併記

各要件の**是正ガイダンス(remediation)** には、FISC解説の原文根拠に加えて、AWS が提示する
**対応方法案（「お客様が統制すべき内容」＋「補足情報」）** を併記します（AWS作成の
「FISC安全対策基準対応リファレンス」由来。**「AWSの対応状況」列は使用しません**）。

- AWS対応データは SKILL 同梱の設定ファイル **`config/aws_remediation_v<版>.json`** に格納します。
  この設定には **AWS作成の列のみ**を保持し、**FISC安対基準の本文・解説は一切含めません**。
- `generate_packs.py` は `config/aws_remediation_v*.json` のうち**版番号が最大のもの**を自動選択します。
- 各項目コードに対し、**厳密一致**（例 `実14-1`）と**ベースコード**（`-N` を除いた `実14`）の両方で
  AWS行を引き当て、重複を排除して併記します。
- 無効化/固定したい場合: `--no-remediation`（併記しない）、`--remediation-config <path>`（版を固定）。

**設定ファイルの生成（AWS対応PDFから）**:

```bash
python3 ~/.kiro/skills/fisc-to-aws-security-agent/scripts/build_remediation_config.py \
    --pdf "<AWS作成 FISC対応リファレンス.pdf>" \
    --version 13 \
    --out ~/.kiro/skills/fisc-to-aws-security-agent/config/aws_remediation_v13.json
```

### 第14版が公開されたときの差し替え手順

第14版対応の AWS対応リファレンスPDFが公開されたら、以下だけで自動的に切り替わります
（FISC安対基準の本文PDFは同梱・保存しないこと）。

1. `build_remediation_config.py` を**第14版PDF**に対して実行し、`--version 14 --out config/aws_remediation_v14.json` で生成する。
2. 生成した `config/aws_remediation_v14.json` を SKILL の `config/` に置く。
3. 以降 `generate_packs.py` は**版番号が最大の v14 を自動選択**する（旧 v13 は削除しても残置してもよい）。
4. `--format manual` 等で再生成すれば、是正ガイダンスが第14版の AWS対応方法案に更新される。

## Security Agent への取り込み手順（利用者が実施）

### A. アップロードで取り込む場合（`--format upload`）

1. AWS コンソールで **AWS Security Agent → Security requirements** を開く。
2. **Custom security requirements packs** タブで、パックごとに **Create security requirements pack** で
   パックを作成（推奨: ファイル名 `FISC-01…` 等に対応した名前）。
3. 対象パックで **Choose files** から該当 `NN_*.md` を1つアップロードし **Generate requirements**。
4. Security Agent がドキュメントから要件を生成する。生成後、**内容を確認・編集**して有効化する。
5. 6パックそれぞれについて 2〜4 を繰り返す。

> 注意: 既存パックに新規ドキュメントをアップロードすると、そのパックの要件は**全て再生成・置換**されます。

### B. 手動で1項目ずつ登録する場合（`--format manual` / 推奨: FISC忠実・監査証跡重視）

1. `--format manual` で `output_manual/NN_*.md` を生成する（前節の生成例を参照）。
2. AWS コンソールで **AWS Security Agent → Security requirements → Custom security requirements packs** を開き、
   パックを **Create security requirements pack** で作成する。
3. パック内で **Add requirement**（要件の手動追加）を選び、`output_manual` の各項目の
   5つの `text` コードブロック（①name〜⑤remediation）を、対応するフィールドへ順にコピー&ペーストする。
4. 各ブロックには**現在の文字数と上限**が併記されているので、上限内であることを確認して保存・有効化する。
5. 項目の見出しに **FISC区分・出典ページ**を記載しているので、登録後の要件とFISC条項の対応（トレーサビリティ）を
   台帳等に控えておく。
6. 全項目・全6パックについて 3〜5 を繰り返す。

> 手動登録では Security Agent による自動再解釈が入らないため、FISC番号・原文根拠・是正ガイダンスが
> そのまま保持されます。

## カスタマイズ

- **対象項目の増減/パック再編**: `config/pack_mapping.json` の各パック `include`（FISC項番の配列）を編集。
  同一項番を複数パックに入れると検証で弾かれます（決定論性のため）。
- **FISC 全項目を網羅したい（方針A）**: `selection_mode` を `keyword` にすると include 外の項目も
  キーワードで自動分類されます（ただし設備/監査/組織項目が混ざり評価不能項目が増える点に注意）。
- 変更後は `run_all.py` を再実行すれば、常に同じ入力から同じ結果を再生成できます。

## セキュリティ（脅威モデル対応）

本Skillは STRIDE 脅威モデル評価の指摘に対応し、以下の対策を実装しています。

**整合性・改ざん検知**
- 各ステージの中間成果物(`fisc_full.txt`/`items.json`/`classified.json`)と config の
  SHA-256 を `run_all.py` が記録し、次ステージが読む直前に再検証（ステージ間改ざん検知）。
- `validate.py` は **実際の `output/*.md` を classified/config から再生成して突合**し、
  さらに `manifest.json` の SHA-256 と照合する（生成後の.md編集・陳腐化を検知）。
- `generate_packs.py` は各 `.md` の SHA-256 を `manifest.json` に記録。
  **アップロード直前に manifest の各SHA-256と実ファイルの一致を必ず確認**してください。

**入力の真正性**
- `--pdf-sha256 <hex>` を指定すると、解析前に入力PDFのSHA-256を検証し、不一致なら中断
  （FISC PDF / AWS対応リファレンスPDF 双方に対応。`extract_pdf.py`・`build_remediation_config.py`）。
- 生成された `aws_remediation_v<版>.json` には解析元PDFの `source_pdf_sha256` を記録。

**実行環境の堅牢化**
- 全成果物は `umask 0077` + `chmod 0600`（所有者限定）。
- 入出力パスは `realpath` 正規化し、出力先が `scripts/`・`config/` を上書きしないことを保証
  （パストラバーサル対策）。
- `pdftotext` フォールバックは `shutil.which` で解決し、許可システムディレクトリ配下の
  絶対パスのみ実行（PATH汚染対策）。`--require-pymupdf` でフォールバック自体を禁止可。
- PyMuPDF フォールバック時は stderr に明示警告し、抽出方式を `fisc_full.txt.meta.json` に記録。
- `PyMuPDF` は `scripts/requirements.txt` にピン留め（`pip install -r scripts/requirements.txt`）。
- 共有ロジックを `fisc_lib.py`（import時副作用なし）へ集約し、`validate.py` の import 経由での
  意図せぬコード実行経路を排除。
- PDF由来テキストは Markdown/コードフェンス注入を無害化（正当な和文には影響なし）。

**否認防止・監査**
- `run_all.py` は実行ごとに `run_manifest.json`（run_id・時刻・実行者・引数・入力PDF/config/
  中間/出力の各SHA-256）を出力し、`run_log.jsonl` に追記（append-only）。

**運用側で必須の対策（コード外・利用者が実施）**
- AWS Security Agent へのアップロードに使う **IAM プリンシパルに MFA を必須化**し、
  Security Agent の必要アクション/リソースARNのみに絞った**最小権限ポリシー**を適用（認証情報窃取対策）。
- `scripts/` と `config/`（`pack_mapping.json`・`aws_remediation_v*.json`）を
  **バージョン管理下に置き、コミット権限を制限**。改ざんは `run_manifest` のハッシュで検知可能。
- 入力PDFは信頼できる入手元のSHA-256を用いて `--pdf-sha256` で検証。
- remediation設定を固定したい場合は `--remediation-config <path>` で明示指定、または
  `--remediation-sha256 <hex>` で期待ハッシュを固定（不一致で中断。高バージョン設定の注入対策）。
- 生成物は「レビュー前ドラフト」。アップロード前に内容と manifest ハッシュを人手確認する。

## ガードレール

- FISC 原文の要件文・解説を改変せず、フィールドへ配置します（曲解・創作をしない）。
- 文字数上限超過分は末尾を明示的に切り詰め（`…(以下略。出典参照)`）、出典を必ず併記します。
- **FISC安対基準の本文・解説PDFは SKILL に同梱・保存しません**（利用者が都度用意）。
- AWS対応方法案の設定ファイルは **AWS作成の「お客様が統制すべき内容」「補足情報」列のみ**を保持し、
  FISC本文は含めません（AWSの対応状況列は使用しません）。
- 生成物は「レビュー前ドラフト」。Security Agent 取り込み後の人手確認を前提とします。
