# reference.md — FISC → Security Agent 変換の詳細仕様

本Skillの設計根拠・仕様・運用ルールをまとめます。SKILL.md と併せて参照してください。

---

## 1. AWS Security Agent Custom セキュリティ要件の仕様

出典: AWS Security Agent ユーザーガイド
（security-requirements.html / import-security-requirements.html / prepare-import-documents.html）

### フィールドと文字数上限

| フィールド | 役割 | 上限(文字) |
|---|---|---|
| Security requirement name | 制御を識別する短い名前 | 80 |
| Description | 何をチェックするかの要約 | 500 |
| Applicability | 適用対象／NOT_APPLICABLE 条件 | 10,000 |
| Compliance criteria | 準拠/非準拠の判定基準・技術的指標 | 10,000 |
| Remediation guidance (任意) | 是正方法・設定例・社内文書リンク | 10,000 |

### アップロード生成の仕様

- 対応形式: **DOC / DOCX / MD / PDF / TXT**。本Skillは **MD** を出力。
- ドキュメントをアップロードすると Security Agent が内容を読み取り、applicability /
  compliance criteria / remediation を含む要件を**自動生成**する。
- 生成される要件数は**コンテンツ依存**。本Skillは「1項目=1セクション」で明確に区切ることで、
  概ね FISC 項目単位の要件生成を促す。
- **既存パックへの再アップロードは全要件を再生成・置換**する（手動追加分も消える）。
- Security Agent は要件を**ワークロード(個々のアプリ/システム)レベル**で生成・評価する。
  組織全体のガバナンス（マルチアカウント戦略、root管理、アカウント単位のログ設定等）は対象外。

### アップロード上限（運用上の制約）

- 1ファイル **2MB** 以下。1パックあたり要件 **20 個**を上限の目安とする。

---

## 2. FISC 安対基準(第13版) の構造

- PDF 717ページ。本文ページ番号 = PDFページ番号 − 3。
- 基準項目の識別子: `統|実|設|監` + 主番号（任意で `-枝番`）。例: `統1-1`, `実14-2`, `設83-1`, `監1-1`。
- 各項目のタイトルは必ず「〜こと。」で終わる（抽出アンカーに利用）。
- 項目本体の構成: **タイトル（基準文）** → **趣旨段落（summary）** → **番号付き解説（body: 1. 2. 3.…）**。
- 4 基準の項目数（第13版, 本Skill抽出値）: 統制 35 / 実務 152 / 設備 134 / 監査 2 = 計 323。

### ページ内ノイズ（除去対象）

ページ境界に繰り返し現れる定型行（「公益財団法人金融情報システムセンター」「（第13版）」
「-92-」等のページ番号、「適用区分」「共/セ/本/提/ダ」「基礎」「◎」等の表ヘッダ）は
`build_items.py` の `NOISE_PATTERNS` で除去する。

---

## 3. パック分類（方針B: ワークロード適合・厳選）

`config/pack_mapping.json` が唯一の分類定義。`selection_mode: include_list` では
各パックの `include`（FISC項番の配列）に列挙された項目のみを採用し、それ以外は除外する。
この明示定義により **誰が実行しても同じ分類結果** になる。

| パック | テーマ | 収録数(第13版) |
|---|---|---|
| FISC-01 | アクセス制御・認証・認可 | 17 |
| FISC-02 | データ保護・暗号化 | 14 |
| FISC-03 | ネットワーク・通信セキュリティ | 11 |
| FISC-04 | ログ・監視・脆弱性/不正プログラム管理 | 17 |
| FISC-05 | 可用性・バックアップ・インシデント対応(BCP/DR) | 15 |
| FISC-06 | セキュア開発・変更管理・AI | 10 |
| （採用合計） | | **84** |

### 除外方針

以下は Security Agent のワークロードレビューで機能しにくいため既定で除外（239項目）:
- **設備基準**（建物・電源・空調・耐震・入退室・回線設備 等の物理設備）
- **監査基準**（内部監査プロセス）
- **統制基準/実務基準のうち非技術項目**（方針・体制・人事・教育・外部委託事務・
  帳票/カード/ATM/店舗運用・純粋な運用手続き 等）

FISC 全項目を網羅したい場合は SKILL.md「カスタマイズ」参照（`selection_mode: keyword`）。

---

## 4. フィールド生成ルール（決定論的・`generate_packs.py`）

LLM を使わず、FISC 原文からテンプレートで構築する。

- **name**: `FISC {code} {タイトルから「こと。/。」を除去}` を 80字で切り詰め。
- **description**: `本要件はFISC安対基準【{code}】に基づき、{趣旨}` を 500字で切り詰め。
- **applicability**: 対応する FISC 項番・カテゴリ・タイトルの明示 + 適用対象(ワークロード) +
  要件趣旨 + NOT_APPLICABLE 条件（機能非保持／物理・組織のみ／完全委譲）。
- **compliance criteria**: 「準拠と判断できる設計」（基準文＋趣旨＋解説着眼点）と
  「非準拠と判断する設計」（制御欠如・趣旨違反）を明示し、FISC解説原文(body)を根拠として掲載。
- **remediation guidance**: AWS対応方法案（お客様が統制すべき内容＋補足情報）を先頭に併記し、
  続けて FISC解説(body)の対策事項を反映するよう案内し、出典を併記。AWS対応方法案が無い項目は
  従来どおり FISC解説(body)のみ。AWS対応データは `config/aws_remediation_v<版>.json`（版番号最大を
  自動選択）から、**厳密一致コード＋ベースコード(-N除去)**で引き当て、重複排除して併記する。
  「AWSの対応状況」列は使用しない。

各フィールドは上限超過時に `…(以下略。出典参照)` で末尾を切り詰める（`clip()`）。

### 出力フォーマット（`--format`）

同じフィールド生成ロジック（`build_*`）の結果を、用途に応じた2形式で出力できる（内容は同一・体裁のみ相違）。

- **`upload`（既定）**: 従来形式。Security Agent へアップロードして自動生成させる想定。
- **`manual`**: 手動コンソール登録用。各項目を `render_item_manual()` が生成し、5フィールドを
  それぞれ独立した ` ```text ` コードブロックに配置。各ブロックに**現在文字数/上限**と**上限超過警告**、
  項目見出しに**FISC区分・出典ページ**を併記する。`normalize()` で PDF抽出由来の行末空白・過剰な空行
  （3行以上）のみを圧縮する（FISC の文言は不変）。

---

## 5. スクリプト構成

| スクリプト | 役割 |
|---|---|
| `scripts/fisc_lib.py` | 共有ライブラリ(field builders/renderers/remediationロード/セキュリティヘルパ)。**import時副作用なし** |
| `scripts/extract_pdf.py` | PDF→全文テキスト（PyMuPDF固定、フォールバックは許可dir配下pdftotextのみ・警告・方式記録） |
| `scripts/build_items.py` | テキスト→基準項目 JSON（項番アンカー抽出＋ノイズ除去＋改行整形） |
| `scripts/classify.py` | items→6パックへ分類（include_list / keyword） |
| `scripts/generate_packs.py` | 分類結果→各パックの Markdown 生成（`--format upload/manual`、AWS対応方法案の併記） |
| `scripts/validate.py` | 文字数・項目数・ファイルサイズの機械検証 |
| `scripts/run_all.py` | 上記を一括実行するパイプライン |
| `scripts/build_remediation_config.py` | AWS作成の対応リファレンスPDF→AWS対応方法案の設定JSON生成（版指定） |
| `config/pack_mapping.json` | パック定義・分類ルール・フィールド上限（唯一の設定） |
| `config/aws_remediation_v<版>.json` | 是正ガイダンス併記用のAWS対応方法案データ（版番号最大を自動選択・第14版差し替え対応） |

### 個別実行例

```bash
S=~/.kiro/skills/fisc-to-aws-security-agent
python3 $S/scripts/extract_pdf.py --pdf FISC.pdf --out work/fisc_full.txt
python3 $S/scripts/build_items.py --text work/fisc_full.txt --out work/items.json
python3 $S/scripts/classify.py --items work/items.json --config $S/config/pack_mapping.json --out work/classified.json
python3 $S/scripts/generate_packs.py --classified work/classified.json --config $S/config/pack_mapping.json --outdir output
python3 $S/scripts/validate.py --classified work/classified.json --config $S/config/pack_mapping.json --outdir output --max-items 20

# 手動登録用フォーマットで再生成（PDF不要・classified.json から再生成可能）
python3 $S/scripts/generate_packs.py --classified work/classified.json --config $S/config/pack_mapping.json --outdir output_manual --format manual
```

---

## 6. 依存関係

- Python 3。PDF抽出は `PyMuPDF`（`import fitz`）を使用し、`scripts/requirements.txt` にピン留め
  （`pip install -r scripts/requirements.txt`）。利用不可時は警告のうえ `pdftotext`（許可システム
  ディレクトリ配下の絶対パスのみ）へフォールバック。`--require-pymupdf` でフォールバック禁止。
- 標準ライブラリのみで動作（YAMLは使わず JSON 設定）。

## 7. 再現性の担保

- 抽出・分類・生成の全工程が正規表現とテンプレート、明示定義ファイルで構成され、乱数・時刻・
  外部API・LLM に依存しない。**同一PDF＋同一 pack_mapping.json なら常に同一の出力**になる。
- `run_manifest.json` は provenance 記録のため時刻/run_id を含むが、`.md` 成果物自体は決定論的。

## 8. セキュリティ制御（脅威モデル対応）

| 対策 | 実装 |
|---|---|
| 中間/出力/config の改ざん検知 | `run_all.py` がステージ間で SHA-256 再検証。`validate.py` は実`.md`を再生成突合＋manifest照合 |
| 入力PDFの真正性 | `--pdf-sha256` 検証（`extract_pdf.py`/`build_remediation_config.py`）。設定に `source_pdf_sha256` 記録 |
| 権限 | `umask 0077` + `chmod 0600`（全成果物） |
| パストラバーサル | `realpath` 正規化＋出力先が `scripts/`・`config/` を侵さないことを保証 |
| PATH汚染 | `pdftotext` は `shutil.which`＋許可ディレクトリ限定 |
| import副作用の排除 | 共有ロジックを `fisc_lib.py`（副作用なし）へ集約 |
| Markdown注入 | PDF由来値を `sanitize_field` で無害化（正当な和文は不変） |
| 高バージョン設定注入 | 選択configとhashを表示・`run_manifest`記録。`--remediation-config`/`--remediation-sha256` で固定可 |
| 否認防止・監査 | `run_manifest.json`＋append-only `run_log.jsonl`（run_id/実行者/時刻/各SHA-256） |
| 認証情報窃取(運用側) | Security Agent書込IAMにMFA必須＋最小権限（コード外・SKILL.md参照） |
