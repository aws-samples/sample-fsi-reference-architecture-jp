---
name: fsi-banking-mobile
description: >-
  レジリエントかつイベント駆動のモバイル / オンラインバンキングワークロード
  （モバイルバンキング / オンラインバンキング）を AWS 上で構築するリファレンス
  アーキテクチャ。3 つの AWS CDK スタック（React SPA フロントエンド、サーバレス
  マイクロサービスバックエンド、モックの勘定系 API）で構成される。口座開設、
  残高照会、振込を、Lambda、DynamoDB、API Gateway、EventBridge、SQS 上で
  Event Sourcing、Transaction Outbox、Saga、CQRS の各パターンを用いて実現し、
  FISC 準拠マッピングも備える。マイクロサービスベースのバンキングワークロードの
  設計・説明・デプロイを行う際、レジリエンスパターン・結果整合性について
  質問された際、または BLEA for FSI の mobile-banking サンプル（金融リファレンス
  アーキテクチャ日本版）について問われた際にこのスキルを使用する。
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Mobile Banking（レジリエンス - モダンアーキテクチャ）

## ワークロード概要

このリファレンスアーキテクチャは **モバイル / オンラインバンキングアプリケーション**
をモデル化したものであり、**レジリエンス** の観点からマイクロサービスアーキテクチャ
の価値を例示するために構築された。バンキングの中核機能である **口座開設**、
**残高照会**、**振込** の 3 つを扱い、金融分野に限らずミッションクリティカルな
システムに適用できる、汎用的で高可用かつスケーラブルなパターンを意図している。

本ワークロードは 3 つの AWS CDK スタックとして提供される。

- **OnlineBankingAppFrontendStack** — Amazon S3、Amazon CloudFront、AWS WAF を
  通じて配信される React SPA。
- **OnlineBankingAppBackendStack** — メインデータストアに Amazon DynamoDB を
  用いた AWS Lambda 上のサーバレスマイクロサービス群。Amazon API Gateway を前面に
  配置し、Amazon EventBridge と Amazon SQS を通じて連携する。
- **TemporaryCoreBankingSystemStack** — 既存の勘定系システム（口座・残高・取引・
  顧客管理）を代替するモック（「一時的」）の勘定系 API。

口座開設と振込は **非同期** で処理される。リクエストは受け付けられ、状態変更は
**Event Sourcing** を用いてイベント（監査証跡）として記録される。勘定系 API への
呼び出しの整合性を保つために **Transaction Outbox** を用い、リトライロジックは
Lambda 関数内部に組み込まれている。本サンプルは Kiro と Amazon Q Developer で
開発され、アーキテクチャ図からの「Vibe Coding」を中心に作成された。

対をなす勘定系（勘定系）リファレンスアーキテクチャでは補償トランザクションを伴う
Saga パターンも用いている。この mobile-banking サンプルは、代替アプローチを示す
ために意図的に *異なる* 分散システムパターンのセットを採用している。詳細、
アプリケーションのウォークスルー、マルチリージョンの考慮事項については
`references/architecture.md` を参照すること。

## ベストプラクティスと主要コンポーネント

### ベストプラクティス

- MUST: すべてのデータストアを AWS KMS カスタマー管理キーで暗号化すること。
  DynamoDB テーブル、Lambda 環境変数、S3 バケット、SQS キューはすべてカスタマー
  管理キーを使用する（FISC 実3 / 実13 / 実30）。
- MUST: KMS キーの自動ローテーションを有効化し、職掌分離（鍵管理者とデータ所有者の
  分離）を考慮したキーポリシーを設計すること。
- MUST: API Gateway と CloudFront で TLS 1.2 以上を強制し、S3 バケットと SQS
  キューでは SSL を必須（`enforceSSL`）とすること。
- MUST: イベントおよび監査データを保持するテーブルで DynamoDB の
  Point-in-Time Recovery (PITR) を有効化すること（FISC 実6 / 実39）。
- MUST: Transaction Outbox パターンで書き込みパスを保護し、データベース更新と
  イベント発行がアトミックにコミットされるようにしたうえで、アウトボックス
  テーブルから外部システムへイベントをリレーすること。
- MUST: すべての状態変更をイベントストアに不変イベントとして記録し
  （Event Sourcing）、金融システムの厳格な監査証跡要件を満たすこと。
- MUST: 外部（勘定系）API 呼び出しの冪等性を担保すること。非同期リトライと
  at-least-once 配信によりメッセージが再現され得るためである。
- MUST: JWT 署名シークレットをコードや平文の環境変数ではなく AWS Secrets Manager
  で管理すること。
- MUST: API Gateway に AWS WAF を適用すること（レートベースルールに加え AWS
  マネージドルールグループ：Common、KnownBadInputs、Linux）。CloudFront にも
  適用する。
- SHOULD: 最小権限の原則を適用すること。各 Lambda 関数に、必要な特定のテーブル・
  インデックス・イベントバス・キーにスコープした固有の IAM ロールを付与する。
- SHOULD: 出金と入金を独立したサービスに分割し、一方の障害が局所化され他方に
  影響しないようにすること。
- SHOULD: 各 SQS キューに、受信回数の上限を設定したデッドレターキュー（DLQ、
  maxReceiveCount = 3）を付与し、処理失敗をリトライしつつ調査のために捕捉すること。
- SHOULD: API Gateway の使用量プランを適用し、キー単位のスロットリングと日次
  クォータを設定したうえで、各メソッドで API Key を必須とすること。
- SHOULD: API Gateway のアクセスログ、実行ログ、X-Ray トレーシング、CloudWatch
  メトリクスを有効化し、ログを CloudWatch Logs に集約すること。
- SHOULD: 勘定系 API を、IAM 認可に加え API Key とアカウント・リージョンに
  スコープしたリソースポリシーによって内部呼び出し元に限定すること。
- PREFER: S3 オリジンには、従来の Origin Access Identity (OAI) よりも CloudFront
  Origin Access Control (OAC) を使用すること。
- PREFER: EventBridge を連携のバックボーンとして使用し、既存サービスを変更する
  ことなく非同期のファンアウト処理（例：AI による本人確認書類レビュー、リスク
  スコアリング、人手によるレビュー、顧客通知）を追加できるようにすること。
- MAY: カスタムドメインなしのマルチリージョンレジリエンスには、CloudFront Origin
  Group と S3 クロスリージョンレプリケーションを用いてプライマリ・セカンダリ
  リージョン間でフェイルオーバーする。カスタムドメインを用いた本番環境では、
  Route 53 Application Recovery Controller または Standby-Takes-Over-Primary
  (STOP) 設計を用いる。
- MAY: DynamoDB グローバルテーブルを強整合性で有効化してリージョン間でイベント
  状態を同期し、リージョン切り替え後に停止したイベントを再駆動（re-drive）する。
- MUST NOT: リアルタイムの整合性を前提としないこと。処理は非同期で結果整合的で
  あるため、操作が即時に確定した状態を必要とする場合は明示的なハンドリングを
  追加すること。
- WILL: モノリスは 1 つのコンポーネントが故障するとサービス全体が停止し、単位
  としてスケールさせる必要がある。一方マイクロサービスは他のサービスを稼働させた
  まま個別にスケールでき、障害の影響を局所化する。
- WILL: 本サンプルにおけるメール配信 Lambda はログ出力のみを行うスタブである。
  実際のメール / 通知配信は別の外部システムを呼び出すことが想定されている。
- MUST: このスキルから構築する全ての CDK Stack に cdk-nag の AwsSolutionsChecks を Aspects で適用し、未抑制の AwsSolutions-* 検出が 0 件であることを CI テスト（jest 等）でゲートする。例外は NagSuppressions に reason を明記して抑制する（詳細は references/cdk-nag.md）。

### 主要コンポーネント

#### フロントエンド配信（OnlineBankingAppFrontendStack）

- **コンポーネント概要**：React シングルページアプリケーションをホストする。静的
  コンテンツはプライベートでバージョニング有効かつ KMS 暗号化された S3 バケットに
  格納され、CloudFront ディストリビューション（OAC、redirect-to-HTTPS、TLS 1.2 以上
  を最小、日本国内のみのジオ制限）を通じて配信される。アクセスログは専用の S3 ログ
  バケットに出力され、us-east-1 にデプロイされた場合に CloudFront 用の WAF Web ACL
  が作成される。
- **想定される AWS サービス**：Amazon S3、Amazon CloudFront、AWS WAF、AWS KMS、
  AWS Systems Manager Parameter Store。

#### API レイヤー（OnlineBankingAppBackendStack）

- **コンポーネント概要**：単一の Amazon API Gateway REST API（「Banking API」）が
  顧客、認証、管理、残高、振込のエンドポイントを公開する。保護されたルートには JWT
  Lambda トークンオーソライザーを使用し、使用量プラン付きのオーディエンス別 API Key
  （customer / admin / auth）、リクエスト検証、アクセス / 実行ログ、リージョナルな
  WAF Web ACL を備える。
- **想定される AWS サービス**：Amazon API Gateway、AWS Lambda（オーソライザー）、
  AWS WAF、Amazon CloudWatch Logs、AWS Systems Manager Parameter Store。

#### 口座開設サービス

- **コンポーネント概要**：Event Sourcing と Transaction Outbox を用いて、3 段階の
  口座開設フロー（顧客申込、管理者承認、自動処理）を実装する。申込状態は専用の
  イベントストアに書き込まれ、DynamoDB Stream を持つアウトボックステーブルが
  アウトボックスプロセッサを駆動し、勘定系 API を呼び出して顧客と口座を作成し、
  ログインユーザーを登録する。
- **想定される AWS サービス**：AWS Lambda、Amazon DynamoDB（イベントストア +
  Streams と StatusIndex GSI を持つアウトボックステーブル）、Amazon EventBridge。

#### 振込（出金 / 入金）サービス

- **コンポーネント概要**：振込を独立した出金・入金マイクロサービスに分割する。
  振込リクエストは `TransferRequested` イベントを記録し、`WithdrawRequested` を
  EventBridge に発行する。SQS キューイングされたワーカー Lambda と DynamoDB Stream
  駆動のアウトボックス Lambda が、勘定系 API をリトライ付きで呼び出しながら状態を
  進行させる（WITHDRAW_REQUESTED → processing → completed → DepositRequested → …
  → TransferCompleted）。
- **想定される AWS サービス**：AWS Lambda、Amazon EventBridge、Amazon SQS（DLQ
  付き）、Amazon DynamoDB（イベントストア + Streams を持つアウトボックステーブル）。

#### クエリサービス（CQRS リードモデル）

- **コンポーネント概要**：CQRS に従って書き込みパスから分離された、読み取り最適化
  された残高・取引履歴エンドポイント。残高は専用のリードモデルテーブルおよび / または
  勘定系 API から提供される。取引履歴は勘定系 API から読み取られる。
- **想定される AWS サービス**：AWS Lambda、Amazon DynamoDB（残高リードモデル）、
  Amazon API Gateway。

#### 認証・ユーザー管理

- **コンポーネント概要**：JWT ベースのログイン、トークン検証、ユーザー登録。
  ユーザーとセッションは DynamoDB に格納される（GSI とセッションの TTL 付き）。
  JWT 署名シークレットは AWS Secrets Manager に配置される。
- **想定される AWS サービス**：AWS Lambda、Amazon DynamoDB、AWS Secrets Manager、
  AWS KMS。

#### 管理機能

- **コンポーネント概要**：口座開設の疑似承認、および取引 ID による振込の
  イベントソース化された状態遷移の可視化のための、最小限の銀行管理者向け機能。
- **想定される AWS サービス**：AWS Lambda、Amazon DynamoDB、Amazon API Gateway。

#### モック勘定系システム（TemporaryCoreBankingSystemStack）

- **コンポーネント概要**：顧客・口座・残高・取引管理を提供する代替の勘定系
  （勘定系）API。IAM 認可に加え API Key とリソースポリシーを用いた内部専用の
  リージョナルな API Gateway を前面に配置し、データは KMS 暗号化された DynamoDB
  テーブルに格納される。本番環境ではこのスタックは `CORE_API_BASE_URL` の
  オーバーライドを通じて既存の勘定系システムに置き換えられる。
- **想定される AWS サービス**：Amazon API Gateway、AWS Lambda、Amazon DynamoDB、
  AWS KMS、Amazon SQS（Lambda DLQ）、Amazon CloudWatch Logs。

## FISC 準拠サマリー

本ワークロードには、**FISC 安全対策基準（実務基準）第 13 版** を本サンプルで実装
された統制にマッピングしたものが含まれる。対象範囲は
**バックエンドシステム（online-banking-app-backend：API Gateway、Lambda、
DynamoDB 等）** に限定され、モック勘定系システムとフロントエンドは対象外である。
システム全体の安全性は、ガバナンスベーステンプレートおよび運用プロセスと合わせて
評価しなければならない。

代表的な統制：KMS カスタマー管理キー暗号化（実3、実13、実30、実69）、TLS 強制
（実4、実7）、IAM / API Key / JWT アクセス制御（実1、実5、実8、実25、実61）、
DynamoDB PITR と IaC バックアップ（実6、実39）、WAF とレート制限（実14、実16、
実20）、変更追跡と整合性のための Event Sourcing / Outbox / DynamoDB Streams
（実17、実19、実65、実66）、マネージドサービスの可用性 / マルチ AZ 設計
（実84〜実88、実104、実106）。

行ごとの完全な表（ガバナンスベース統制 対 ワークロード統制 対 使用者側での追加
考慮事項）は `references/fisc-mapping.md` に保存されている。

## リファレンスアーキテクチャ

完全なアーキテクチャ解説 — 口座開設と振込の処理フロー（シーケンス図付き）、
メール配信に関する注意点、マルチリージョンの考慮事項、およびモノリス対
マイクロサービスのトレードオフと分散システム設計パターン（Saga、Transaction
Outbox、Event Sourcing、CQRS）の議論 — については `references/architecture.md`
を参照すること。エンドユーザーおよび管理者向けアプリケーションのウォークスルーも
そこに含まれている。

## CDK サンプル概要

デプロイ可能な AWS CDK サンプル（TypeScript）は `assets/sample-cdk/` 配下にある。
3 つのスタック（`bin/app.ts`、`lib/*-stack.ts`）、Lambda 関数のソース
（`lib/lambda-functions/`）、モック勘定系バックエンド
（`lib/temporary-core-banking-system-backend/`）、共有 KMS コンストラクト
（`lib/constructs/kms-construct.ts`）、React フロントエンド（`lib/frontend/`）が
含まれる。デプロイは `DEPLOY_CORE_SYSTEM`、`DEPLOY_BACKEND`、`DEPLOY_FRONTEND`
の環境変数で制御されるため、スタックを個別にデプロイでき、`CORE_API_BASE_URL` で
コアエンドポイントをオーバーライドして実際のコアシステムを指すこともできる。
ステップバイステップのデプロイおよび削除手順の全体は `references/deployment.md`
にある。

> **サンプルアプリのセキュリティに関する注意**: 本サンプルはリファレンス／動作デモであり、本番利用可能ではない。アプリケーション層に Critical 級の認可欠陥がある: 送金と残高・取引照会が口座の所有権を検証せず（IDOR）、管理 API はフロントの config に露出した API キーのみで保護され（平文の仮パスワードを伴う）。実口座を扱う前に、所有権チェックと実際の管理者認証を実装すること。同じ注意書きは `assets/sample-cdk/SECURITY_NOTICE.md` に同梱され、`cdk synth` / `cdk deploy` のたびに警告として表示される。

コピーされた `assets/sample-cdk/.../test/*.test.ts` は cdk-nag による強制パターンの
権威ある情報源である。抽出した抑制ルール台帳と再現手順については
`references/cdk-nag.md` を参照すること。
