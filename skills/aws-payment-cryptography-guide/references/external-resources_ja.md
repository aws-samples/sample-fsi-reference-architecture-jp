# 外部リソース集

AWS Payment Cryptography に関するリンク・参考資料をカテゴリ別に整理したガイドです。
実装の参考、最新情報の確認、深い学習にご活用ください。

---

## 公式ドキュメント

| リソース | URL |
|----------|-----|
| **ユーザーガイド** | https://docs.aws.amazon.com/payment-cryptography/latest/userguide/ |
| **コントロールプレーン API リファレンス** | https://docs.aws.amazon.com/payment-cryptography/latest/APIReference/ |
| **データプレーン API リファレンス** | https://docs.aws.amazon.com/payment-cryptography/latest/DataAPIReference/ |
| **サービスエンドポイントとクォータ** | https://docs.aws.amazon.com/general/latest/gr/payment-cryptography.html |

> **注**: ブラウザの言語設定を日本語にすると自動的に日本語版が表示されます（翻訳が利用可能な場合）。

### 主要 CLI コマンド

- `aws payment-cryptography create-key` — 対称鍵・非対称鍵の作成
- `aws payment-cryptography import-key` — TR-31/TR-34 による鍵インポート
- `aws payment-cryptography export-key` — KEK でラップした鍵のエクスポート
- `aws payment-cryptography list-keys` — 鍵一覧の取得
- `aws payment-cryptography get-key` — 鍵メタデータと属性の取得
- `aws payment-cryptography delete-key` — 鍵削除のスケジュール（最低7日間）
- `aws payment-cryptography-data generate-pin-data` — PIN ブロックの生成
- `aws payment-cryptography-data verify-pin-data` — PIN の検証
- `aws payment-cryptography-data translate-pin-data` — PIN フォーマット変換
- `aws payment-cryptography-data generate-card-validation-data` — CVV/CVC 生成
- `aws payment-cryptography-data verify-card-validation-data` — CVV/CVC 検証
- `aws payment-cryptography-data encrypt-data` — 決済データの暗号化
- `aws payment-cryptography-data decrypt-data` — 決済データの復号
- `aws payment-cryptography-data generate-mac` — MAC の生成
- `aws payment-cryptography-data verify-mac` — MAC 値の検証

CLI リファレンス: https://docs.aws.amazon.com/cli/latest/reference/payment-cryptography/

---

## AWS ブログ記事

### サービス発表

- **"Move Payment Processing to the Cloud with AWS Payment Cryptography"** (2023年6月)
  サービスローンチ発表。鍵管理、暗号化操作、決済ワークロードのクラウド移行を解説。
  https://aws.amazon.com/blogs/aws/move-payment-processing-to-the-cloud-with-aws-payment-cryptography/

- **"AWS Payment Cryptography is PCI PIN and P2PE certified"** (2024年2月)
  PCI PIN v3.1 および P2PE v3.1 認証取得の発表。
  https://aws.amazon.com/blogs/security/aws-payment-cryptography-is-pci-pin-and-p2pe-certified/

- **"PCI PIN and P2PE compliance packages ... are now available"** (2026年5月)
  AWS Artifact 経由でコンプライアンスパッケージが入手可能に。
  https://aws.amazon.com/blogs/security/pci-pin-p2pe-compliance-packages-aws-payment-cryptography/

### 技術詳細・チュートリアル

- **"Synchronize keys automatically from payment HSMs to AWS Payment Cryptography"** (2025年6月)
  オンプレミス HSM からの自動鍵同期の実装ガイド（TR-31 + イベント駆動）。
  https://aws.amazon.com/blogs/security/synchronize-keys-automatically-from-payment-hsms-to-aws-payment-cryptography/

- **"How to use AWS Payment Cryptography Service to simplify payment flows"** (2026年3月)
  PIN 変換、カード検証、MAC 生成のエンドツーエンド・チュートリアル。
  https://aws.amazon.com/blogs/security/how-to-use-aws-payment-cryptography-to-simplify-payment-flows/

- **"Transforming transactions: Streamlining PCI compliance using AWS serverless architecture"** (2023年10月)
  Payment Cryptography + Lambda + API Gateway のサーバーレス決済パターン。
  https://aws.amazon.com/blogs/security/transforming-transactions-streamlining-pci-compliance-using-aws-serverless-architecture/

---

## サンプルコード & SDK

### GitHub リポジトリ

- **AWS Samples — Payment Cryptography Service**
  https://github.com/aws-samples/samples-for-payment-cryptography-service

  含まれる内容: Java SDK 鍵管理サンプル、Python ECDH 鍵交換フロー、
  PIN 変換ワークフロー、カード検証データ生成/検証、CloudFormation テンプレート

### SDK 対応状況

| SDK | パッケージ名 |
|-----|-------------|
| Java | `software.amazon.awssdk:paymentcryptography` |
| Python (boto3) | `boto3.client('payment-cryptography')` |
| JavaScript/TypeScript | `@aws-sdk/client-payment-cryptography` |
| .NET | `AWSSDK.PaymentCryptography` |
| Go | `github.com/aws/aws-sdk-go-v2/service/paymentcryptography` |

---

## 料金 & SLA

| リソース | URL |
|----------|-----|
| **料金** | https://aws.amazon.com/payment-cryptography/pricing/ |
| **機能概要** | https://aws.amazon.com/payment-cryptography/features/ |
| **よくある質問 (FAQ)** | https://aws.amazon.com/payment-cryptography/faqs/ |
| **SLA** | https://aws.amazon.com/payment-cryptography/sla/ |

### 料金モデルの概要

- アクティブな鍵ごとの月額料金
- API コール（暗号化操作）ごとの従量課金
- 初期費用・長期契約なし
- 削除待ち状態の鍵には課金されない

> **ヒント**: 東京リージョン (ap-northeast-1) の料金ページで日本円の価格を確認できます。

---

## コンプライアンスリソース

### AWS 提供のコンプライアンス資料

- **AWS Artifact** — PCI PIN AOC、P2PE AOV、共有責任サマリーをコンソールからダウンロード。
  https://aws.amazon.com/artifact/

- **AWS コンプライアンスプログラム** — 全認証・認定の概要。
  https://aws.amazon.com/compliance/programs/

- **PCI DSS on AWS** — PCI DSS レベル1準拠と共有責任の FAQ。
  https://aws.amazon.com/compliance/pci-dss-level-1-faqs/

### 主要コンプライアンス認証

| 規格 | ステータス | 対象範囲 |
|------|-----------|----------|
| PCI PIN v3.1 | 認証済み | PIN 処理と鍵管理 |
| PCI P2PE v3.1 | 認証済み | ポイントツーポイント暗号化の復号 |
| PCI DSS v4.0 | 対象範囲内 | AWS PCI DSS 評価の一部 |
| PCI 3DS | 対象範囲内 | AWS の PCI DSS/3DS 評価に含まれる |
| SOC 1/2/3 | 対象範囲内 | AWS SOC レポートに含まれる |

---

## 業界標準（外部リソース）

### ペイメントカード業界

- **PCI Security Standards Council (PCI SSC)**
  https://www.pcisecuritystandards.org/
  PCI DSS、PCI PIN、PCI P2PE、PA-DSS 標準の管理団体。決済セキュリティの国際基準を策定。

- **PCI PIN セキュリティ要件**
  https://www.pcisecuritystandards.org/document_library/

### 鍵管理標準

- **ANSI X9.143 (TR-31)** — 相互運用可能なセキュア鍵交換鍵ブロック仕様。
  AWS Payment Cryptography の鍵インポート/エクスポートで使用。

- **ANSI X9.24-2 (TR-34)** — 対称鍵配布のための非対称技術。
  非対称ラッピングによる初期鍵インジェクションに使用。

### EMV 標準

- **EMVCo**
  https://www.emvco.com/
  チップベース決済カード、非接触決済、トークナイゼーション、3-D Secure の
  EMV 仕様を管理するグローバル技術団体。

---

## その他のリソース

- **AWS re:Invent セッション** — "payment cryptography" で検索
  https://www.youtube.com/@AWSEventsChannel

- **AWS Well-Architected Framework — 金融サービスレンズ**
  安全で回復力のある決済アーキテクチャ構築のガイダンス。

- **AWS パートナーソリューション** — 決済処理パートナーとの事前構築統合
  https://aws.amazon.com/solutions/partners/

- **AWS 日本語ハンズオン** — ワークショップ・ハンズオン資料
  https://aws.amazon.com/jp/events/aws-event-resource/hands-on/

---

*最終更新: 2026年7月*
