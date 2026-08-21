---
name: fsi-foundation-openapi
description: >-
  「金融リファレンスアーキテクチャ日本版（BLEA for FSI）」の取り組みに基づく、AWS 上で金融オープン
  API（オープン API）ワークロードを構築するためのリファレンスアーキテクチャと CDK サンプル。サードパーティ
  からアクセス可能な銀行 API を設計・デプロイする際にこのスキルを使用する。対象には、Amazon Cognito +
  API Gateway で認証する基本的な参照系 API（残高照会 / 株価照会）と、mTLS および OAuth2/OpenID Connect
  認可サーバー（Keycloak または Authlete）で保護する金融グレード API（FAPI、資金移動 / 売買指図）が含まれる。
  FISC 安全対策基準マッピング、マルチリージョン DR 設計、および提供される 2 つの CDK サンプル
  （guest-openapi-base-sample と guest-openapi-fapi-sample）を扱う。トリガーキーワード：Open API、
  オープンAPI、FAPI、金融グレードAPI、認可サーバー、Keycloak、mTLS、相互TLS、Cognito API。
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# 金融オープン API（オープン API）

## 1. ワークロード概要

本リファレンスアーキテクチャにおける **オープン API** は、全国銀行協会（全銀協）の定義に従い、
**サードパーティ（外部企業等）からアクセス可能な API** である。金融機関が、個人や Fintech パートナーに
対して、強固なアイデンティティ・認可・トランスポートセキュリティを保ちながら、サービスを API 経由で
公開することを可能にする。その権限範囲は次の 2 つのクラスのいずれかである。

- **参照・照会系 API（参照・照会系）** — 主にエンドユーザー向けの、読み取り指向の API。
  例：株価・為替相場情報照会、銀行残高照会、ポイント照会。
- **更新・実行系 API（更新・実行系）** — 主に金融グレードのアクセスを必要とする外部 Fintech
  企業向けの、状態を変更する API。例：株式・投信の売買指図、資金移動（振込・振替）。

**ビジネス上の動機。** オープン API は、日本におけるオープンバンキングと Fintech 連携の技術的基盤である。
銀行が、強固なアイデンティティ・認可・トランスポートセキュリティを維持しながら、口座・市場・取引の機能を
パートナーに安全に公開できるようにする。本ワークロードは、特定のドキュメント規格（OpenAPI Specification /
Swagger）、FAPI への準拠、OAuth2/OpenID Connect を **必須とはしない**。これらは API クラスに応じた
オプションである。2 つのアクセス方式が提供される。

- **ベーシック API アクセス** — 参照・照会系クラス向けに、フルの AWS マネージドサービス（認証に Amazon
  Cognito、API 管理に Amazon API Gateway）を採用する。
- **金融グレード API（FAPI）アクセス** — 更新・実行系クラス向けに、認可サーバーに加えて相互 TLS 認証と
  暗号化を採用する。FAPI 1.0 の挙動を開発・テストで検証する用途を想定している。

## 2. ベストプラクティスと主要コンポーネント

### ベストプラクティス

- MUST: 参照・照会系 API アクセスの認証は、Amazon API Gateway をフロントに置いた Amazon Cognito ユーザープールで行うこと。
- MUST: 更新・実行系（金融グレード）API アクセスの認証は、相互 TLS（mTLS、クライアント証明書）と認可サーバーを組み合わせて行うこと。
- MUST: Amazon API Gateway、Amazon Cognito、Amazon CloudFront にまたがるすべてのクライアント向け通信を TLS で暗号化し、API バックエンドへの通信は利用者側で暗号化すること。
- MUST: Amazon EBS と Amazon Aurora の保存データを AWS Key Management Service で暗号化し、暗号化鍵を KMS キーポリシーで保護すること。
- MUST: Amazon CloudFront に AWS WAF を適用し、CloudFront ディストリビューションを地域制限（許可リスト）で制限して攻撃対象領域を削減すること。
- MUST: IAM 権限は最小権限のみを付与し、IAM ロールの一時認証情報を通じてリソースにアクセスすること。
- MUST: 認可サーバーおよび DBMS（Amazon Aurora）に対して CloudTrail を有効化し、VPC フローログと Amazon CloudWatch Logs を取得すること。
- MUST: ワークロードをマルチリージョン / マルチ AZ 構成で構築し、回復性のために高可用性を備えた AWS マネージドサービスを優先すること。
- SHOULD: マルチリージョン DR 構成において、リージョン間で認証情報を同期する必要がないよう、外部 IdP を利用すること。
- SHOULD: FAPI 1.0 Advanced では、クライアント認証に Keycloak のデフォルトである `private_key_jwt` ではなく `tls_client_auth`（クライアント TLS）を利用すること。
- SHOULD: Amazon API Gateway をリソースサーバーとする場合、API Gateway の mTLS はクライアント証明書の失効も CRL も確認しないため、Lambda Authorizer を実装してクライアント証明書の失効と CRL を確認すること。
- SHOULD: サーバー / クライアント証明書の有効期限を管理し、失効前に双方を更新すること。CloudFront 用証明書は us-east-1、API Gateway 用証明書は ap-northeast-1 に（ACM で）登録すること。
- SHOULD: FAPI の ID トークンには PS256 または ES256 の署名鍵を利用すること（Keycloak のレルムはこれらの鍵ペアをデフォルトでは作成しない）。
- MUST NOT: API バックエンドやクライアント / リソースサーバーアプリケーションを本サンプルの一部として提供しないこと。これらはスコープ外であり、利用者が実装する必要がある。
- MAY: AWS Systems Manager を利用して EC2 インスタンスを集中管理し、AWS Inspector で認可サーバー / バックエンドのコンテナイメージや EC2 の脆弱性をスキャンしてもよい。
- WILL: FAPI サンプルは、FAPI 1.0 の挙動を開発・テストで検証する用途を想定したものであり、そのまま本番稼働できる認可サーバーではない。
- WILL: Route 53 がリージョン間でリクエストを振り分ける。リクエストをどのように振り分ける / 切り替えるかは、API バックエンドシステムのポリシーに依存する。
- MUST: このスキルから構築する全ての CDK Stack に cdk-nag の AwsSolutionsChecks を Aspects で適用し、未抑制の AwsSolutions-* 検出が 0 件であることを CI テスト（jest 等）でゲートする。例外は NagSuppressions に reason を明記して抑制する（詳細は references/cdk-nag.md）。

### 主要コンポーネント

#### API 管理（ベーシック）

- **コンポーネント概要**: 参照・照会系 REST API の作成・公開・保守・モニタリング・保護を行う。
  エッジ配信とキャッシュのために CDN をフロントに置き、WAF マネージドルールによる保護と、TLS 上の
  カスタム / 代替ドメインを備える。
- **想定 AWS サービス**: Amazon API Gateway（REST API、リージョナルカスタムドメイン、
  Cognito Authorizer）、Amazon CloudFront、AWS WAF（WAFv2）、AWS Certificate Manager、
  Amazon Route 53、AWS Lambda（サンプルバックエンド）。

#### API 認証 — ベーシック（IdP）

- **コンポーネント概要**: 参照・照会系 API クラス向けの、ウェブ / モバイルのユーザー認証・認可・ユーザー
  管理。API Gateway の Cognito Authorizer が消費する ID トークンを発行する。
- **想定 AWS サービス**: Amazon Cognito（ユーザープール `apiUserPool`、ユーザープールクライアント
  `apiUserPoolClient`）。

#### 認可サーバー（FAPI）

- **コンポーネント概要**: VPC 上で稼働し、トークンの発行とイントロスペクションを行う、FAPI 1.0 対応の
  認可サーバー（Authorization Server）。FAPI 1.0 Baseline / Advanced プロファイルに対応する。3rd
  パーティ製プロダクト（Authlete）または OSS（Keycloak）として提供され、デプロイ可能なサンプルとして
  提供されるのは OSS の Keycloak パターンのみである。
- **想定 AWS サービス**: Amazon ECS on AWS Fargate（Amazon ECR からの Keycloak コンテナ）、Network
  Load Balancer、Amazon Aurora MySQL / Amazon RDS、AWS Secrets Manager、Amazon EC2
  （Authlete / 認可サーバーのホスティングパターン）。

#### mTLS / 証明書セキュリティ（FAPI）

- **コンポーネント概要**: CA / 中間 CA / サーバー / クライアント証明書を用いた、クライアント・認可サーバー・
  リソースサーバー間の相互 TLS トランスポートセキュリティ。認可サーバーとリソースサーバーの双方に対して
  同一のクライアント証明書を用いる。
- **想定 AWS サービス**: AWS Certificate Manager、Amazon API Gateway（リソースサーバーとしての
  mTLS 有効化 REST/HTTP API）、AWS Lambda（CRL / 失効確認用の Lambda Authorizer）。

#### ネットワーク & データ層（FAPI）

- **コンポーネント概要**: Fargate 認可サーバーと暗号化された Aurora データベースをホストする、分離された
  マルチ AZ の VPC（public / protected / isolated サブネット）。インターフェース / ゲートウェイ VPC
  エンドポイントと、暗号化された VPC フローログを備える。
- **想定 AWS サービス**: Amazon VPC（CloudWatch Logs、ECR、ECR Docker、S3 の VPC エンドポイント）、
  Amazon Aurora MySQL（暗号化）、AWS KMS、Amazon S3（フローログバケット）、ネットワーク ACL。

#### モニタリング & ガバナンス

- **コンポーネント概要**: ワークロード全体に対する、運用モニタリング、サービス正常性の検知、監査ログ、
  および IaC ベースの構成 / バックアップ。
- **想定 AWS サービス**: Amazon CloudWatch（メトリクス、Logs、Container Insights）、AWS Health
  Dashboard、AWS CloudTrail、AWS Cloud Development Kit（AWS CDK）、Amazon Aurora 自動バックアップ。

## 3. FISC 準拠サマリー

FISC マッピングは、本ワークロードが **FISC 安全対策基準（実務基準、第 11 版）** にどのように対応するかを
文書化したものである。対応は **ガバナンスベーステンプレート（共通統制環境）** と **オープン API ワークロード
テンプレート** に分かれ、各行には使用者側での追加対策の例も併記している。記載しているのは BLEA for FSI での
対策のみであり、システム全体の安全性には、利用者のアプリケーション実装に加えて運用・開発プロセス上の統制が
別途必要である。

ワークロードテンプレートがカバーする主要な規制上の考慮事項は以下のとおり。

- **アクセス制御と認証**（実 1、実 2、実 9、実 26）: 参照系 API には Cognito、更新・実行系 API には mTLS
  クライアント証明書 + 認可サーバー認証。
- **暗号化**（実 3、実 4、実 7、実 13、実 30、実 69）: 保存データには EBS/Aurora に対する AWS KMS、通信には
  API Gateway / Cognito / CloudFront に対する TLS。
- **ログと監査**（実 6、実 10、実 72）: 認可サーバーと Aurora に対する CloudTrail、VPC フローログと
  CloudWatch Logs。
- **ネットワーク保護**（実 14、実 15、実 20）: CloudFront への AWS WAF、VPC エンドポイント、ECS/Aurora の
  通信を制御するセキュリティグループ。
- **可用性 / DR**（実 84〜実 88、実 104）: マルチリージョン / マルチ AZ、高可用性を備えたマネージドサービス。
- **モニタリングと運用**（実 46、実 47、実 101〜実 103）: サービス障害検知のための CloudWatch モニタリングと
  AWS Health Dashboard。
- **IaC と変更管理**（実 39、実 42、実 43）: 構築・構成・バックアップのための AWS CDK、Aurora の自動バックアップ。

多くの項目は、対象外（業務アプリケーション、管理・運用プロセス、開発プロセス、または AWS クラウド側で対策済み）
としてマークされている。全エントリ（実 1〜実 148）と 3 列のフルテーブルを保持したものは
[references/fisc-mapping.md](references/fisc-mapping.md) を参照。

## 4. リファレンスアーキテクチャ

本リファレンスアーキテクチャは、両 API クラスのパターンとマルチリージョン DR 設計を示す。完全な技術詳細は
[references/architecture.md](references/architecture.md) を参照。

**パターン概要。** パターン一覧の全体像は `assets/images/open-api-Arch-Pattern.png` を参照。本
アーキテクチャは、デプロイ可能な 3 つのバリアントを区別する。

**ベーシック API（参照・照会系）。** エンドユーザーは Amazon Cognito を通じて認証する。リクエストは
Amazon CloudFront（AWS WAF と地域制限付き）を経由して、Cognito ユーザープール Authorizer を用いる
リージョナルな Amazon API Gateway REST API に到達し、サンプルでは AWS Lambda がバックエンドとなる。
図：`open-api-Arch-Basic-Diag.png`、`open-api-Arch-Basic-Flow.png`。

**金融グレード API（FAPI）。** 更新・実行系アクセスには、FAPI 1.0 Advanced スタイルの相互 TLS が必要である。
FAPI 対応の認可サーバーがトークンを発行・イントロスペクトし、リソースサーバー（例：Amazon API Gateway +
バックエンド）がトークンとクライアント証明書を検証する。認可サーバーのサブバリアントとして 2 つが
文書化されている。

- **FAPI / 3rd Party（Authlete）** — 図 `open-api-Arch-FAPI-Authlete-Diag.png`、
  `open-api-Arch-FAPI-Authlete-Flow.png`。アーキテクチャとしてのみ文書化（サンプルなし）。
- **FAPI / OSS（Keycloak）** — 図 `open-api-Arch-FAPI-keycloak-Diag.png`、
  `open-api-Arch-FAPI-keycloak-Flow.png`。デプロイ可能な `guest-openapi-fapi-sample` として提供。
  Keycloak は、マルチ AZ の VPC 内で、インターネット向け NLB の背後の ECS Fargate 上で稼働し、Aurora
  MySQL をバックエンドとする。

**マルチリージョン DR。** 広域災害事象（例：関東広域被災）に対して、オープン API スタックはリージョン
ごと（例：東京と大阪）に独立してデプロイされ、Amazon Route 53 がリクエストを振り分ける。アイデンティティ /
認証には外部 IdP を利用するため、リージョン間の認証同期は不要である。図：
`open-api-Arch-Multi-region.png`。

## 5. CDK サンプル概要

2 つの AWS CDK（TypeScript）サンプルが [assets/sample-cdk/](assets/sample-cdk/) 配下に提供される。
いずれも、BLEA for FSI のガバナンスベースが既に導入されているゲストアカウントにデプロイする。デプロイの
詳細は [references/deployment.md](references/deployment.md) を参照。コピーされた
`assets/sample-cdk/.../test/*.test.ts` が cdk-nag 強制パターンの正典であり、抽出した抑制ルール台帳と、
自分の Stack でゲートを再現する方法は [references/cdk-nag.md](references/cdk-nag.md) を参照。

> **サンプルアプリのセキュリティに関する注意**: 2 つの CDK サンプル（base と FAPI）はいずれもリファレンス／検証用デモであり、本番利用可能ではない。base サンプルでは WAF が count モード（非ブロック・レート制限なし）で Cognito がパスワード認証・MFA 任意。FAPI サンプルでは Keycloak↔Aurora の DB リンクが平文（`useSSL=false`）、DB セキュリティグループが VPC CIDR 全体を許可し、FAPI の mTLS 照合が緩い。実利用の前に、WAF のブロック化・DB の TLS 化・セキュリティグループの厳格化・FAPI mTLS の厳格化を行うこと。各サンプルは `SECURITY_NOTICE.md` を同梱し、`cdk synth` / `cdk deploy` のたびに警告を表示する。

**`guest-openapi-base-sample`** — ベーシック API 環境。Amazon Cognito ユーザープール（`apiUserPool`）+
クライアント、Amazon API Gateway REST API（Cognito Authorizer、CLF アクセスログ、リージョナルカスタム
ドメイン）、Lambda の「hello」バックエンド、API ステージに関連付けた AWS マネージドルールグループ
（Common、KnownBadInputs、AmazonIpReputationList、Linux、SQLi）を持つ AWS WAF（WAFv2）WebACL、および
Amazon CloudFront ディストリビューション（HTTPS のみ、地域許可リスト US/GB/JP、S3 アクセスログバケット）
をプロビジョニングする。2 つの ACM 証明書（CloudFront は us-east-1、API Gateway は ap-northeast-1）と
Route 53 エイリアスレコードが必要である。Cognito の ID トークンを用いた curl で検証する。

**`guest-openapi-fapi-sample`** — FAPI（Keycloak）環境。専用のマルチ AZ VPC（public / protected /
isolated サブネット、KMS 暗号化された S3 バケットへの VPC フローログ、CloudWatch Logs / ECR / ECR
Docker / S3 の VPC エンドポイント、カスタム NACL）と、Keycloak デプロイをプロビジョニングする。Keycloak
デプロイは、Amazon ECR からの **カスタム Keycloak 16.1.1** コンテナイメージを実行する ECS Fargate
サービス（タスク 1024 CPU / 2048 MiB、desired count 2、CPU 80% で 2〜10 にオートスケール）で構成され、
インターネット向け Network Load Balancer（TCP 443 → 8443、送信元 IP スティッキネス）をフロントに置き、
暗号化された Amazon Aurora MySQL / RDS クラスターをバックエンドとし、Keycloak 管理者認証情報は AWS
Secrets Manager で自動生成される。デプロイには、カスタム Keycloak イメージのビルドとプッシュ（サーバー
証明書を焼き込む）、CA / 中間 / サーバー / クライアント証明書の作成、および FAPI 1.0 のための手動の
Keycloak レルム / クライアント / ポリシー設定が必要である。

> 注記：FAPI のデプロイドキュメントは工事中とされている。参照している Keycloak（jboss/keycloak）
> コンテナリポジトリが廃止されたためである。手順の考え方はリファレンスとして引き続き有効である。
