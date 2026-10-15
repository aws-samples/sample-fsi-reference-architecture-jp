---
name: fsi-capital-market-data
description: >-
  「BLEA for FSI / 金融リファレンスアーキテクチャ日本版」のベースライン上に構築する、
  金融機関向けマーケットデータ（Market Data）配信システムのリファレンスアーキテクチャ。
  本ワークロードは、株価・為替レートなどのリアルタイムなマーケットデータを取り込み・計算し、
  FIX / REST / WebSocket を通じて社内外のクライアントへ配信する。Handler / Composer /
  Distributor の 3 層構成と、疎結合のための Amazon Kinesis Data Streams を用いる。
  マーケットデータフィード / リアルタイムデータ配信ワークロードを AWS 上で設計・解説・
  デプロイ・FISC マッピングする際に本スキルを使用する（キーワード: マーケットデータ,
  market data, データ配信, Kinesis, FIX/REST/WebSocket, リアルタイム配信）。
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# マーケットデータ リファレンスアーキテクチャ（BLEA for FSI）

## ワークロード概要

金融機関のマーケットデータ配信システムは、市場に関わる様々なデータを生成し、社内外のクライアントへ配信する。配信データは通常、社内外のデータプロバイダから収集したデータを元に計算される。クライアント、プロバイダとの通信には FIX, REST, WebSocket などのプロトコルが用いられる。

マーケットデータは、データの発生頻度、発生からクライアントへの配信までに求められる鮮度によって、大きく 3 パターンに分類される。

- **リアルタイム** — 株価、為替レートなど。1 分あたり数千〜を超える更新。レイテンシセンシティブである場合も多い。
- **ニアリアルタイム** — 市況ニュース、非リアルタイムなプライス配信など。数分に 1 度の更新。
- **バッチ** — 金利指標、企業格付け、外為公示相場など。数時間〜に 1 度の更新。

本リファレンスアーキテクチャでは **リアルタイム** なユースケースを対象とする。

本アーキテクチャは BLEA for FSI のガバナンスベース（共通の統制・セキュリティアカウント基盤）の上に構築され、ゲストアカウントにデプロイされる。

## ベストプラクティスと主要コンポーネント

### ベストプラクティス

- MUST: システムを Handler App、Composer App、Distributor App の 3 つのアプリケーション層で構成し、各層に明確な責務を持たせる。
- MUST: Handler App は受信した Input データをプロデューサとして Amazon Kinesis Data Streams に書き込む。プロトコルや認証方式は Provider が定めるインターフェースに依る。
- MUST: Composer App は、Handler App（または他の Composer）が提供する Stream をコンシューマとして利用し、配信データの計算を行う。
- MUST: Distributor App は、Composer App が提供する Stream をコンシューマとして利用し、クライアントの要求に応じてフォーマットの変換や配信頻度、粒度の調整を行う。
- SHOULD: 上流の Composer App、及びその Stream が何らかの障害で利用不能になった場合に、Distributor App が直近正常時の値を固定値として提供する。
- MUST: FIX の Consumer は NLB を経由して Distributor App と通信させ、認証は FIX 通信時の Logon プロセスで実施する。
- MUST: REST, WebSocket の Consumer は ALB を経由して Distributor App と通信させ、ALB は HTTP の Authorization ヘッダを検証して認証用の Lambda と Distributor App をルーティングする。
- SHOULD: Provider, Client とのネットワークは要件に応じて Direct Connect, Internet, Private Link 等を利用する。
- MUST: 各コンテナアプリケーションは同一構成を Multi AZ で配置し、Active - Active で稼働させる。クライアントに対しては両現用な 2 つのエンドポイントを示し、障害時の切り替えをガイドする。
- SHOULD: コンポーネント間の連携に Stream を採用することでコンポーネント間の結合を疎にし、プロデューサ（Handler, Composer）が後続コンポーネントの存在や場所を意識することなくデータを提供でき、コンシューマの数を変動させることも容易にする。
- MAY: 本構成を拡張し、例えば分析用途に新たな DB などを追加したい場合、コンシューマの一員として追加する。
- MUST: データは AWS KMS で暗号化を行い、暗号鍵への適切なアクセス権の設定を行う。データを蓄積している AWS リソースに対しては適切な IAM ポリシーを設定してデータ漏洩を防止する（FISC 実 3 / 実 30 / 実 69）。
- MUST: 最小権限の原則に基づき、IAM ロールの一時クレデンシャルを用いて各リソースにアクセスする（FISC 実 9 / 実 25）。
- MUST: インターネットからのアクセスについては接続エンドポイント（Amazon ELB、Amazon API Gateway 等）で通信プロトコルを制限し、外部ネットワークからの不正侵入防止を行う。アプリケーション側で通信相手の認証を行う（FISC 実 14 / 実 15）。
- SHOULD: コンテナビルドする際に信頼できるコンテナイメージおよびライブラリであることを確認し、Amazon ECR でコンテナの脆弱性検証を行う（FISC 実 20 / 実 21 / 実 32）。
- SHOULD: Amazon CloudWatch を用いてコンピュートリソース、NW 帯域、ALB、Aurora、DynamoDB、Amazon ECS リソースを監視し、VPC フローログおよび ALB アクセスログを有効化する（FISC 実 46 / 実 72）。
- WILL: Amazon Kinesis Data Stream はデータを物理的に隔離されたロケーションに標準で 24 時間（最大 7 日）までデータ保持可能である。
- SHOULD: 可用性のためにマルチリージョン / マルチアベイラビリティーゾーン構成を構築し、高い可用性を備えている AWS マネージドサービスを利用する（FISC 実 85〜実 88）。
- SHOULD: AZ 障害への耐性を超える大規模な障害が発生した場合、サービス復旧を待つかセカンダリリージョンへの切り替え等を判断する。データプロデューサ、データコンシューマともに接続先の切り替え、リソースの作成等にかかる時間と維持コストを考慮する（FISC 実 71 / 実 73 / 実 74）。
- MUST: このスキルから構築する全ての CDK Stack に cdk-nag の AwsSolutionsChecks を Aspects で適用し、未抑制の AwsSolutions-* 検出が 0 件であることを CI テスト（jest 等）でゲートする。例外は NagSuppressions に reason を明記して抑制する（詳細は references/cdk-nag.md）。

### 主要コンポーネント

#### Handler App

- **コンポーネント概要**: 配信データの元となる Input を受信する。プロトコルや認証方式は Provider が定めるインターフェースに依る。受信データをプロデューサとして Kinesis Data Stream に書き込む。CDK サンプルでは ECS on Fargate サービス（`sample_handler` コンテナ）と専用の Kinesis Data Stream として実装されている。
- **想定 AWS サービス**: Amazon ECS（AWS Fargate）、Amazon Kinesis Data Streams、Amazon ECR。

#### Composer App

- **コンポーネント概要**: 配信データの計算を行う。多くの場合、配信データは上流の Market Data Provider や社内のリファレンスデータをインプットとして計算される。Handler App が提供する Stream をコンシューマとして利用し、他の Composer が提供する Stream をコンシューマとして利用する場合もある（例: GBPJPY を計算する Composer C の Input として、GBPUSD を計算する Composer A と USDJPY を計算する Composer B の Stream を利用する）。CDK サンプルでは ECS on Fargate サービス（`sample_composer` コンテナ）と専用の Kinesis Data Stream として実装され、計算結果は DynamoDB に格納可能である。
- **想定 AWS サービス**: Amazon ECS（AWS Fargate）、Amazon Kinesis Data Streams、Amazon DynamoDB、Amazon ECR。

#### Distributor App

- **コンポーネント概要**: Composer App が提供する Stream をコンシューマとして利用し、クライアントに向けたデータの配信を行う。クライアントの要求に応じてフォーマットの変換や配信頻度、粒度の調整を行い、上流の Composer やその Stream が利用不能な場合には直近正常時の値を固定値として提供する。FIX の Consumer は NLB を経由し、REST/WebSocket の Consumer は HTTP の Authorization ヘッダを検証する ALB を経由する。CDK サンプルでは ECS on Fargate サービス（`sample_distributor` コンテナ）を、AWS WAF と ALB アクセスログを有効化した ALB の背後に配置している。
- **想定 AWS サービス**: Amazon ECS（AWS Fargate）、Elastic Load Balancing（Application Load Balancer / Network Load Balancer）、AWS WAF、AWS Lambda（認証）、Amazon ECR。

#### データストア

- **コンポーネント概要**: 計算・合成されたマーケットデータを格納する。CDK サンプルでは、カスタマー管理の KMS 暗号化、ローカルセカンダリインデックス、消費読み込みキャパシティに対する CloudWatch アラームを備えた Amazon DynamoDB テーブルである。
- **想定 AWS サービス**: Amazon DynamoDB、AWS KMS。

#### 暗号鍵管理

- **コンポーネント概要**: Kinesis Data Streams、DynamoDB テーブル、CloudWatch Logs、SNS 監視トピックの暗号化に使用するカスタマー管理の KMS キー（CMK）。
- **想定 AWS サービス**: AWS KMS。

#### 監視・通知

- **コンポーネント概要**: ゲストシステムを監視し、通知を送信する。CDK サンプルでは、E メールサブスクリプションと TLS 強制の publish ポリシーを持つ SNS トピックが CloudWatch アラームを受信し、ECS クラスターでは CloudWatch Container Insights が有効化されている。
- **想定 AWS サービス**: Amazon CloudWatch、Amazon SNS。

#### ネットワーク

- **コンポーネント概要**: Multi AZ にまたがるパブリック VPC で、プライベートサブネット、VPC フローログ、CloudWatch Logs・DynamoDB・ECR・ECR Docker・S3 Gateway 向けの VPC エンドポイントを備える。Provider, Client との接続には要件に応じて Direct Connect, Internet, PrivateLink を利用する。
- **想定 AWS サービス**: Amazon VPC、VPC エンドポイント、AWS Direct Connect / AWS PrivateLink（要件に応じて）。

#### コンテナイメージビルドパイプライン

- **コンポーネント概要**: サンプルコンテナイメージをビルドし ECR にプッシュする。CDK サンプルでは、CodeBuild プロジェクトが `sample-ecs-app` アセット（Dockerfile + buildspec）からイメージをビルドし、デプロイ時にカスタムリソース経由でトリガーされる。
- **想定 AWS サービス**: AWS CodeBuild、Amazon ECR、Amazon S3。

## FISC 対応サマリー

本ワークロードは、FISC 安全対策基準（第 11 版）の実務基準に対してマッピングされている。マッピングは、共通統制環境（ガバナンスベーステンプレート）、金融ワークロードテンプレート（マーケットデータ）、使用者側での追加対策の例、の 3 列で構成される。本ワークロードは金融取引を行うサービスではなく、自動着信機能を持った端末へのデータ送信や記憶媒体を介したファイル授受を想定していないため、それらを理由に多数の基準が対象外（対象外）とされている。

ワークロード側の主要な対策には次が含まれる。適切な鍵アクセス制御を伴う AWS KMS 暗号化（実 3, 実 13, 実 30, 実 69）、一時クレデンシャルを用いた最小権限 IAM（実 9, 実 25）、接続エンドポイントでのプロトコル制限と通信相手の認証（実 14, 実 15）、コンテナイメージの信頼性確認と ECR による脆弱性検証（実 20, 実 21, 実 32）、GuardDuty による異常検知（実 22）、CloudWatch / VPC フローログ / ALB アクセスログによる監視（実 46, 実 72, 実 101〜実 103）、Kinesis Data Streams のデータ保持と CDK/IaC によるバックアップ（実 39）、マルチリージョン / マルチ AZ による可用性（実 85〜実 88）、大規模障害時のセカンダリリージョン切り替え検討（実 71, 実 73, 実 74, 実 84, 実 104, 実 106）。

各基準（実 1 〜 実 148）ごとの完全なマッピング表は [references/fisc-mapping.md](references/fisc-mapping.md) を参照。

## リファレンスアーキテクチャ

本アーキテクチャは、Handler App、Composer App、Distributor App の 3 層で構成され、疎結合を実現するために Amazon Kinesis Data Streams で接続される。各コンテナアプリケーションは同一構成を Multi AZ で配置し、Active - Active で稼働する。

![Architecture](assets/images/marketdata-arch.png)

各層の責務、プロトコル処理、コンポーネント間のストリーミング、可用性・拡張性に関する「その他ポイント」を含む完全な技術詳細は [references/architecture.md](references/architecture.md) を参照。

## CDK サンプル概要

デプロイ可能な AWS CDK（TypeScript）サンプルを [assets/sample-cdk/](assets/sample-cdk/) 配下に提供する。サンプルスタック（`GuestMarketDataStack`、プロジェクトプレフィックス `BLEAFSI-MarketData`）は以下をプロビジョニングする。

> **サンプルアプリのセキュリティに関する注意**: 本サンプルはリファレンス／動作デモであり、本番利用可能ではない。認証・TLS・サブスクライバ単位のエンタイトルメントは意図的に実装者へ委ねられている: Distributor の ALB は平文 HTTP `open:true`、認証 Lambda は未配線、全 tier が `stream/*` の共有ワイルドカード タスクロールを流用し、コンテナのベースイメージはダイジェスト未固定である。誤った/陳腐化した価格は誤発注に直結するため、実フィードに使用する前に、認証・TLS・エンタイトルメント・最小権限ロール・イメージ固定を実装すること。同じ注意書きは `assets/sample-cdk/SECURITY_NOTICE.md` に同梱され、`cdk synth` / `cdk deploy` のたびに警告として表示される。

- カスタマー管理の KMS キー（`AppKey`）。
- E メールサブスクリプションを持つ SNS ベースの監視アラームトピック。
- パブリック VPC（Multi AZ、VPC フローログ、VPC エンドポイント）。
- ECR リポジトリ。
- Handler、Composer、Distributor の各アプリを ECS on Fargate サービス（`desiredCount: 2`、Container Insights 有効）として構築。各々 CodeBuild ベースの `ImageBuilder` により `sample-ecs-app` イメージからビルドされる。
- 2 つの Kinesis Data Streams（Handler Stream、Composer Stream）。いずれも KMS 暗号化。
- 合成データ用の DynamoDB テーブル（カスタマー管理暗号化、LSI、CloudWatch アラーム）。
- Distributor アプリの前段に配置する ALB（AWS WAF とアクセスログ有効化）。

`bin/parameter.ts` に Dev / Staging / Prod のパラメータセットを定義する。開発スタックは `npx cdk deploy BLEAFSI-MarketData-Dev` でデプロイする。

デプロイの前提条件と手順の詳細は [references/deployment.md](references/deployment.md) を参照。

同梱される `assets/sample-cdk/.../test/*.test.ts` は、本ワークロードにおける cdk-nag 強制パターンの正典である。抽出した抑制台帳と再利用可能な強制テストテンプレートは [references/cdk-nag.md](references/cdk-nag.md) を参照。
