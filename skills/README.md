# スキル (Agent Skills)

**金融リファレンスアーキテクチャ日本版**は、以下の**スキル**を提供します。スキルはカテゴリ別に整理しています。

## 金融ワークロード（ビジネスワークロード）

| # | スキル名 | 概要 | インターネット接続性 |
|---|----------------|-------------|------------|
| 1 | [FSI Capital OMS](fsi-capital-oms/SKILL_ja.md) | 資本市場向けクラウドネイティブなオーダー管理システム（OMS）のケーススタディ。受注・約定と発注・出来を分離した低レイテンシーメッセージング基盤 | 不要 |
| 2 | [FSI Insurance Analytics](fsi-insurance-analytics/SKILL_ja.md) | 保険業データ分析基盤のケーススタディ。Amazon S3 / Redshift レイクハウス、Aurora / Glue によるメタデータ管理 | 不要 |
| 3 | [FSI Payments Credit Card](fsi-payments-credit-card/SKILL_ja.md) | クレジットカードイシュアシステムのリファレンスアーキテクチャ。マイクロサービス・マルチリージョン Active-Active 構成 | 不要 |

## 金融ワークロード（基盤・共通インフラ）

| # | スキル名 | 概要 | インターネット接続性 |
|---|----------------|-------------|------------|
| 4 | [FSI Foundation Hybrid Cloud](fsi-foundation-hybrid-cloud/SKILL_ja.md) | AWS Outposts 上に構築するハイブリッド金融ワークロードのリファレンスアーキテクチャ。オンプレミス／顧客データセンター連携 | 不要 |
| 5 | [FSI Foundation Mainframe Integration](fsi-foundation-mainframe-integration/SKILL_ja.md) | オンプレミスのメインフレームと AWS の連携ガイダンス。3 つのデータ連携パターン（レプリケーション等）を扱う | 不要 |

## 金融ワークロード向け： 生成AI（Generative AI）

| # | スキル名 | 概要 | インターネット接続性 |
|---|----------------|-------------|------------|
| 6 | [FSI GenAI Platform](fsi-genai-platform/SKILL_ja.md) | 金融機関向け生成AIワークロードのリファレンスアーキテクチャ。「Generative AI Use Cases (GenU)」の閉域版をベースに金融向けセキュリティをカスタマイズ | 不要 |
| 7 | [FSI GenAI Use Cases](fsi-genai-usecases/SKILL_ja.md) | 金融機関向け生成AIユースケースのケーススタディ。Amazon Bedrock を中心とした 4 つの具体的ユースケース（文書審査 RAPID 等） | 不要 |

## 金融ワークロード向け： セキュリティ・レジリエンス

| # | スキル名 | 概要 | インターネット接続性 |
|---|----------------|-------------|------------|
| 8 | [FSI Cyber Resilience](fsi-cyber-resilience/SKILL_ja.md) | 金融機関向けサイバーレジリエンスの実装ガイド。エアギャップバックアップ、クロスアカウント復旧、侵害ワークロードの自動ネットワーク隔離 | 不要 |
| 9 | [FSI Ransomware Resilience](fsi-ransomware-resilience/fsi-ransomware-overview/SKILL_ja.md) | AWS 上でのランサムウェア対策の相談窓口。保護・検知・対応・復旧・組織対応の 5 フェーズ（6 サブスキル）で構成 | 不要 |

## 金融ワークロード向け AWSサービス活用支援

| # | スキル名 | 概要 | インターネット接続性 |
|---|----------------|-------------|------------|
| 10 | [FISC to AWS Security Agent](fisc-to-aws-security-agent/SKILL_ja.md) | FISC「安全対策基準」PDF から AWS Security Agent の Custom セキュリティ要件パック向けソースドキュメントを決定論的に生成 | 不要 |
| 11 | [AWS Payment Cryptography Guide](aws-payment-cryptography-guide/SKILL_ja.md) | AWS Payment Cryptography（APC）の導入・設計・移行支援。HSM 移行、PIN 検証・翻訳、鍵管理、PCI 準拠考慮事項を網羅 | 不要 |

## AWS Well-Architected フレームワーク FSI Lens for FISC

| # | スキル名 | 概要 | インターネット接続性 |
|---|----------------|-------------|------------|
| 12 | [FSI Lens for FISC](fsi-lens-for-fisc/SKILL_ja.md) | 日本の金融機関ワークロードを AWS Well-Architected フレームワークおよび FISC 安全対策基準に照らして評価する Lens | 不要 |

## AWS 情報取得

| # | スキル名 | 概要 | インターネット接続性 |
|---|----------------|-------------|------------|
| 13 | [AWS What's New](aws-whatsnew/SKILL_ja.md) | AWS What's Newアナウンスを日付フィルタリング付きで取得 | 必要 (aws.amazon.comドメイン) |
| 14 | [AWS Blogs](aws-blogs/SKILL_ja.md) | AWSブログ記事を公開APIから検索・取得 | 必要 (aws.amazon.comドメイン) |
| 15 | [AWS Security Bulletins](aws-security-bulletins/SKILL_ja.md) | AWSセキュリティ速報（脆弱性情報）を取得・検索 | 必要 (aws.amazon.comドメイン) |
| 16 | [AWS Customer References](aws-customer-references/SKILL_ja.md) | 複数の公開情報源（公式API・事例サイト・YouTube・一般Web）を横断してAWS事例を探索・整理 | 必要 (aws.amazon.com / youtube.com / 一般Web) |

## 国内 情報取得

| # | スキル名 | 概要 | インターネット接続性 |
|---|----------------|-------------|------------|
| 17 | [BOJ Statistics](boj-statistics/SKILL_ja.md) | 日本銀行（BOJ）の公開APIから時系列統計データ（金利・為替・短観・物価指数等）を取得・検索 | 必要 (boj.or.jpドメイン) |
| 18 | [Japan Security Advisories](jp-security-advisories/SKILL_ja.md) | JPCERT/CCおよびMyJVN API（IPA注意警戒情報、JVN iPedia脆弱性DB）から国内セキュリティ情報を取得・検索 | 必要 (jpcert.or.jp / jvndb.jvn.jpドメイン) |
| 19 | [FSA Announcements](fsa-announcements/SKILL_ja.md) | 金融庁の新着情報RSSと年度別アーカイブから報道発表・審議会等を期間・カテゴリで取得 | 必要 (www.fsa.go.jpドメイン) |

## 業務支援

| # | スキル名 | 概要 | インターネット接続性 |
|---|----------------|-------------|------------|
| 20 | [Customer Context Manager](customer-context-manager/SKILL_ja.md) | お客様固有のコンテキスト（略称・組織構造・キーパーソン等）を自動管理 | 不要 |
| 21 | [Product Planning](product-planning/SKILL_ja.md) | 商品企画ワークショップ（マーケティング起点／Working Backwards）を対話形式で実行 | 不要 |

## 汎用ツール

| # | スキル名 | 概要 | インターネット接続性 |
|---|----------------|-------------|------------|
| 22 | [AWS Security Guard](aws-security-guard/SKILL_ja.md) | AWS操作の事前セキュリティガード。実行前にリスクを検知し代替案を提示 | 不要 |
| 23 | [MCP Tool Invoker](mcp-tool-invoker/SKILL_ja.md) | CLIツールを使ったMCPサーバー呼び出しのリファレンススキル | 不要 |
| 24 | [Skill to Document](skill-to-document/SKILL_ja.md) | Agent Skillの内容をフォーマットされたドキュメント（PDF、DOCX、HTML）に変換 | 不要 |


# Disclaimer

提供するAgent Skillsは、予告なく追加・変更・削除される場合があります。
