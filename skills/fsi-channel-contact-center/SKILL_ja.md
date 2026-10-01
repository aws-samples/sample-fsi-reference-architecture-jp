---
name: fsi-channel-contact-center
description: >-
  Amazon Connect を中核として、日本の金融機関向けにセキュアでコンプライアンスに準拠した信頼性の高い
  オムニチャネルコンタクトセンター（顧客チャネル / Customer Channel）を構築するためのリファレンス
  アーキテクチャ。インバウンド／アウトバウンド音声、Web チャット／Web 通話、AI 支援（Amazon Q in
  Connect、Amazon Bedrock）、通話モニタリング／コンプライアンスチェック、マルチリージョン DR、FISC
  コンプライアンスマッピングを扱う。金融コンタクトセンター／コールセンターワークロードを設計・説明・デプロイ
  する場合、Amazon Connect の統制を FISC 安全対策基準にマッピングする場合、または BLEA for FSI の
  guest-customer-channel-sample CDK を扱う場合にこのスキルを使用する。
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI 顧客チャネル (Customer Channel)

## ワークロード概要

顧客チャネルワークロードは、日本の金融機関向けに構築される**オムニチャネルコンタクトセンター**のリファレンスアーキテクチャであり、**Amazon Connect** を中核とする。金融機関は、ウェブポータルでのテキストチャット、コールセンタオペレータとの音声通話、チャットボットなど複数のチャネルを通して、顧客体験と従業員体験を向上するコンタクトセンターの構築にますます投資している。本ワークロードは、Amazon Connect をはじめとする様々な AWS のサービスと機械学習のテクノロジーを組み合わせ、金融機関に求められるセキュリティ・コンプライアンス・信頼性を備えるコンタクトセンターの構築方法を示す。

**想定する業務シナリオ:**

- **顧客チャネル**: 公衆回線を用いた音声、もしくはウェブポータルからのチャット。
- **インバウンド**: お客様窓口、代理店窓口、自動受付（テレホンバンキング、カードローン仮審査など）、受電集中。
- **アウトバウンド**: 折り返し電話、テレマーケティング、督促業務。
- **コンプライアンス**: 音声チャネルの会話の文字起こし結果から、社内のコンプライアンス規定に反する単語を検出する。

**金融サービスにおける意義:** コンタクトセンターは機微な顧客データ（電話番号、契約情報、本人確認情報）を扱い、FISC 安全対策基準（金融機関等コンピュータシステムの安全対策基準）の対象となる。本ワークロードは、BLEA for FSI のガバナンスベース上に、暗号化・アクセス制御・監査ログ・災害復旧・本人確認に対応した実装ベースラインを提供する。

## ベストプラクティスと主要コンポーネント

### ベストプラクティス

- MUST: プライマリリージョンではユーザー管理を AWS IAM Identity Center との SAML 連携で行い、パスワードポリシーと MFA を強制する。
- MUST: Amazon S3 に保存するデータ（通話録音、チャットトランスクリプト、コンタクトトレースレコード）を AWS KMS キーで暗号化し、IAM ポリシーおよび S3 バケットポリシーでアクセスを保護する。
- MUST: Amazon Connect や Amazon S3 など AWS サービスとの通信および AWS サービス間の通信は、機密性と改ざん検知の両面で全て TLS を使用する。
- MUST: 電話番号・録音・コンタクトフローなどの機微なコンタクト履歴へのアクセスを、Amazon Connect のセキュリティプロファイルで制御する。
- MUST: IAM ポリシー、リソースポリシー、SCP を可能な限り最小権限で付与する。Lambda 関数に付与するロールも含める。
- SHOULD: KMS キーローテーションを有効化し、キーポリシーを管理する。暗号化鍵の管理者とデータ所有者を分割する職掌分離を検討する。
- SHOULD: コンタクトフローなど重要な設定を Amazon EventBridge と AWS Lambda を用いて定期的にバックアップし、不正な変更後に復旧できるようにする。
- SHOULD: Amazon CloudWatch で Amazon Connect の主要メトリクス（LongestQueueWaitTime, MissedCalls, CallsBreachingConcurrencyQuota, ContactFlowErrors, ThrottledCalls など）を監視し、Quota 超過やエラーを検知する。
- SHOULD: Amazon Connect のログイン/ログアウトレポートは 10,000 行までの制限があるため、S3 へのエクスポートを行う。
- SHOULD: 他の多くはマネージドサービスであるため、Lambda 関数の実行ログを記録する。
- MAY: 音声ベースの本人確認に Amazon Connect の Voice ID（声紋認証）を利用する。代替手段としてオペレータによる確認も可能とする。
- MAY: 広域災害対策としてセカンダリリージョンを採用する。これは必須ではなく、複数 AZ 冗長で十分な場合やデータレジデンシーを懸念する場合は省略できる。
- WILL: セカンダリ（DR）リージョンでは AWS IAM Identity Center を使用しないため、パスワードポリシー・MFA・ログイン失敗ログが強制されない点に留意する。
- WILL: サンプルテンプレートは変更の可能性がある Amazon Connect Preview API を使用しており、アーキテクチャの一部のみを実装している（設定の定期バックアップなどは未実装）。
- MUST: このスキルから構築する全ての CDK Stack に cdk-nag の AwsSolutionsChecks を Aspects で適用し、未抑制の AwsSolutions-* 検出が 0 件であることを CI テスト（jest 等）でゲートする。例外は NagSuppressions に reason を明記して抑制する（詳細は references/cdk-nag.md）。

### 主要コンポーネント

#### コンタクトセンター基盤

- **コンポーネント概要**: インバウンド／アウトバウンド音声、Web チャット、Web 通話を受け付け、コンタクトをエージェントにルーティングし、対話を録音し、コンタクトフローとエージェントワークスペースをホストする中核エンジン。複数 AZ で動作し高い可用性を持つ。
- **想定される AWS サービス**: Amazon Connect。

#### ID・認証

- **コンポーネント概要**: エージェント／管理者に対しパスワードポリシーと MFA を強制して ID を一元管理し、必要に応じてエンドユーザーの本人確認を行う。
- **想定される AWS サービス**: AWS IAM Identity Center（SAML 連携）、Amazon Connect ユーザー管理（セカンダリリージョン）、Amazon Connect Voice ID。オプションで外部 IdP。

#### インバウンドコンタクト処理

- **コンポーネント概要**: 着信の音声／チャットコンタクトを受け付け、自動受付と本人確認プロンプトを行い、顧客をエージェントに接続する。エージェント接続フローと、コミュニケーションウィジェットで使用する即時受付フローの両方を提供する。
- **想定される AWS サービス**: Amazon Connect（コンタクトフロー、キュー）、Amazon Lex（本人確認ボット）、Amazon Polly。

#### アウトバウンドコンタクト自動化

- **コンポーネント概要**: API 経由で発信を自動化し、折り返し電話・テレマーケティング・督促のために各発信の状態（initiated, disconnected）を管理する。
- **想定される AWS サービス**: Amazon API Gateway（IAM 認証）、AWS Step Functions、Amazon DynamoDB、Amazon EventBridge、Amazon Connect。

#### AI 支援とコンプライアンスモニタリング

- **コンポーネント概要**: ナレッジベースからのエージェント支援／セルフサービス回答、リアルタイム通話モニタリング、会話要約、および文字起こしから規定違反の発言を検出するコンプライアンスチェックを提供する。
- **想定される AWS サービス**: Amazon Q in Connect、Amazon Bedrock（Anthropic Claude、Amazon Nova モデル）、Amazon Kinesis Data Streams、AWS Lambda、AWS AppSync、Amazon DynamoDB。

#### 顧客データとケース管理

- **コンポーネント概要**: 複数コンタクトにまたがる顧客プロファイルを名寄せし、コンタクトセンターと統合された顧客問い合わせケースを管理する。
- **想定される AWS サービス**: Amazon Connect Customer Profiles、Amazon Connect Cases、Amazon AppIntegrations。

#### 録音保管・バックアップ・DR

- **コンポーネント概要**: 暗号化した通話録音・チャットトランスクリプト・コンタクトトレースレコードを保管し、遠隔バックアップと災害復旧のためにクロスリージョンでレプリケーションする。
- **想定される AWS サービス**: Amazon S3（KMS 暗号化、バージョニング、クロスリージョンレプリケーション）、AWS KMS、Amazon Data Firehose。

#### Web フロントエンドとエッジ保護

- **コンポーネント概要**: 顧客向け Web サイト（コミュニケーションウィジェット付き）と内部の通話モニタリング UI を配信し、IP ベースのフィルタリングでエッジを保護する。
- **想定される AWS サービス**: Amazon CloudFront、AWS WAF、Amazon S3、Amazon Cognito。

## FISC コンプライアンスサマリー

FISC マッピングは、顧客チャネルワークロードについて、FISC 安全対策基準（第 11 版）の実務基準に対して BLEA for FSI がどのように対応するかを示す。全 148 項目（実 1〜実 148）を網羅する。記載は BLEA for FSI が提供する対策のみであり、総合的なシステム全体の安全対策は、ユーザーアプリケーション側の実装とシステム運用・開発プロセス等での対策を含めて別途検討する必要がある。

本ワークロードが対応する主な規制上の考慮事項:

- **アクセス制御・ID（実 1, 5, 8, 9, 25, 26）**: IAM Identity Center との SAML 連携によるパスワードポリシーと MFA（プライマリリージョン）、最小権限 IAM、Amazon Connect セキュリティプロファイル、Voice ID による本人確認。DR 用セカンダリリージョンでは IAM Identity Center を使用しない点に留意。
- **データ保護（実 3, 4, 5, 7, 13, 30）**: S3 データの KMS 暗号化、転送時の TLS（機密性と改ざん検知）、適切な KMS キーポリシー。
- **監査・モニタリング（実 10, 16, 19, 20, 46, 47, 101〜103）**: Amazon Connect API 呼び出しの CloudTrail 記録、Connect ログイン/ログアウトレポート、主要メトリクスの CloudWatch 監視、Lambda 実行ログ。
- **回復性・DR（実 39, 71, 73, 74, 104）**: 複数 AZ の Amazon Connect、広域災害を想定したマルチリージョン構成、S3 バージョニング + クロスリージョンレプリケーション、CDK（IaC）による設定バックアップ。
- **対象外**: 多くの項目は AWS クラウド側、業務アプリケーション側、または管理・運用・開発プロセスで対応されるものとして明示されている。

行単位の完全な詳細（全 148 項目、欠落なし）は [references/fisc-mapping.md](references/fisc-mapping.md) を参照。

## リファレンスアーキテクチャ

リファレンスアーキテクチャは、マルチリージョン構成の Amazon Connect コンタクトセンターである。サンプルが使用するリージョン構成の例: プライマリを東京（ap-northeast-1）、オプションのセカンダリ DR リージョン、バックアップ用のターシャリリージョン（例: 大阪、ap-northeast-3）、および CloudFront WAF 用の us-east-1 スタック。

主要な設計判断:

- **Amazon Connect を中核**とし、通話録音・チャットトランスクリプト・スケジュールレポートの S3 ストレージ設定と、コンタクトトレースレコードの Amazon Data Firehose 配信を行う。いずれも KMS 暗号化。
- **ID はプライマリリージョンで SAML / IAM Identity Center** により管理し、DR リージョンでは Amazon Connect 管理ユーザーを使用する。
- **広域 DR** として、セカンダリリージョンに Connect インスタンスと電話番号をあらかじめ用意し、録音 / CTR / 設定を別リージョンへレプリケーションする。セカンダリリージョンはオプション。
- **AI 機能** として、Amazon Q in Connect（アシスタント、ナレッジベース、Amazon Bedrock モデル上の日本語プロンプトを用いた AI エージェント）と、Bedrock ベースのコンプライアンスチェック・要約を伴うリアルタイム通話モニタリングを提供する。
- **エッジ保護** は CloudFront + AWS WAF（IP 許可リスト）による。

アーキテクチャ図（注: 図は新規追加リソースより前のもの）と完全な技術詳細は [references/architecture.md](references/architecture.md) を参照。

## CDK サンプル概要

CDK サンプル（TypeScript）は、プロジェクトプレフィックス `BLEAFSI-CustomerChannel` の下に、マルチリージョン構成の Amazon Connect コンタクトセンターをプロビジョニングする。

> **サンプルアプリのセキュリティに関する注意**: 本サンプルはリファレンス／動作デモであり、本番利用可能ではない。call-monitoring サンプルにはオブジェクトレベル認可がなく（開発者 TODO 明記済み）、認証済みエージェント 1 人で全顧客の通話記録・AI 要約・コンプラ所見を閲覧できる。さらに Bedrock `invokeModel` が `Resource:'*'` で付与されている。実際の顧客データを扱う前に、呼び出し元 identity に基づく行レベル認可（および Bedrock 権限・MFA・WAF の是正）を実装すること。同じ注意書きは `assets/sample-cdk/SECURITY_NOTICE.md` に同梱され、`cdk synth` / `cdk deploy` のたびに警告として表示される。

- **Primary スタック**: Amazon Connect インスタンス（S3/KMS 録音設定、Firehose 経由の CTR、オプションの SAML を含む）に加え、インバウンド、即時インバウンド、アウトバウンド、Amazon Q in Connect、Customer Profiles、Cases のサンプル。条件付きで通話モニタリングと Web 通話のサンプル。
- **Tertiary スタック**: バックアップ用 KMS キーと S3 バケット（クロスリージョンレプリケーションの宛先）。
- **Secondary スタック**（オプション）: DR 用 Amazon Connect インスタンス。
- **WAF スタック**（us-east-1）: CloudFront WAF Web ACL。

本サンプルは Amazon Connect Preview API を使用し、アーキテクチャの一部のみを実装している。デプロイ手順（Context 設定、CDK ブートストラップ/デプロイ、SAML 設定、コミュニケーションウィジェット、テスト）は [references/deployment.md](references/deployment.md) を参照。各スタック・コンストラクトのソースに基づく詳細な解説は [references/cdk-sample.md](references/cdk-sample.md) を参照。サンプルソースは [assets/sample-cdk/](assets/sample-cdk/) の下にある。コピーされた `assets/sample-cdk/test/*.test.ts` が cdk-nag 強制パターンの正典であり、抽出した強制の3層と抑制ルール台帳（この資産は抑制ゼロでパス）は [references/cdk-nag.md](references/cdk-nag.md) を参照。
