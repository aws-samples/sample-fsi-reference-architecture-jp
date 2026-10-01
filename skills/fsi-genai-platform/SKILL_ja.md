---
name: fsi-genai-platform
description: >-
  金融機関向けの生成 AI（Generative AI）ワークロードを AWS 上に構築するための
  リファレンスアーキテクチャ。AWS Samples の「Generative AI Use Cases (GenU)」
  アプリケーションの閉域版をベースに、金融機関向けのセキュリティカスタマイズを施した
  もの。金融サービス向け生成 AI プラットフォーム（RAG による社内ナレッジ検索、文書作成
  支援、顧客対応支援、チャット・要約・翻訳、画像・動画生成、閉域ネットワーク構成、Amazon
  Bedrock、Amazon Bedrock Guardrails、Amazon Cognito 認証、CloudWatch 監視ダッシュボード、
  KMS 暗号化、FISC（金融情報システムセンター）コンプライアンスマッピング）を設計・レビュー・
  説明する際に、この「BLEA for FSI / 金融リファレンスアーキテクチャ日本版」v1.6 の生成 AI
  アセットスキルを使用する。
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI リファレンスアーキテクチャ — 生成 AI (Generative AI)

## ワークロード概要

本スキルは、「金融リファレンスアーキテクチャ日本版（BLEA for FSI）」v1.6 の
**生成 AI（Generative AI）** リファレンスアーキテクチャをパッケージ化したものである。
金融機関における生成 AI 活用のためのサンプル実装である。

本実装は、AWS Samples で公開されている生成 AI アプリケーション **Generative AI Use Cases
(GenU)**（https://github.com/aws-samples/generative-ai-use-cases）の **閉域版（閉域ネット
ワーク構成）** をベースに、金融機関で一般的に求められるセキュリティ要件（暗号化、監査ログ、
Guardrail 強化）に対応するためのカスタマイズを施している。

GenU は、チャット、文章生成、要約、翻訳、RAG、画像生成、動画生成など、多様な生成 AI ユース
ケースを提供するオープンソースアプリケーションである。本リファレンスアーキテクチャでは以下を
提供する。

- GenU で実現可能な金融機関向けユースケースの整理
- GenU 閉域版の主要機能と活用方法の解説
- 金融要件向けに施したセキュリティ強化カスタマイズ（暗号化、監査ログ、Guardrail 設定）
- FISC 安全対策基準への対応状況（下記の FISC コンプライアンスサマリおよび
  `references/fisc-mapping.md` を参照）

**対応する金融ユースケース** には以下が含まれる。RAG による社内ナレッジの検索・活用（規程・
マニュアル・過去の稟議書・商品説明資料を自然言語で検索）、文書作成支援（稟議書・報告書・お客
様向け説明資料・社内メール）、顧客対応支援（問い合わせ内容の要約・回答案作成・過去の類似事例
検索）、データ分析支援（営業／市場データの傾向分析・レポート要約・示唆抽出）、社内コミュニケー
ション効率化（音声からの議事録自動生成・複数言語間翻訳・資料要約）。画像生成・動画生成・ダイ
アグラム生成により、プレゼン資料、社内教育コンテンツ、業務フローの可視化にも活用できる。

**前提条件と位置付け**。閉域ネットワーク構成は、組織のネットワークポリシーに合致する選択肢の
一つである。通常版（非閉域版）の GenU も十分なセキュリティ機能を備えており、要件に応じて選択
可能である。本設計は段階的なセキュリティ強化に対応しており、初期は通常版で開始し、リスク評価
に応じて Guardrails の追加、閉域ネットワーク構成への移行、MFA の強制適用などを後から追加でき
る。

## ベストプラクティスと主要コンポーネント

### Best Practices

- SHOULD: データの機密性やネットワークセキュリティポリシー上の要件がある場合、クライアント
  とシステム間の通信を閉域ネットワークに閉じる。GenU の閉域ネットワークモードを利用し、通信
  がインターネットを経由しないようにする。
- SHOULD: 閉域ネットワーク構成では、Web 静的ファイルを Amazon CloudFront ではなく
  Application Load Balancer + Amazon ECS Fargate で配信する。
- MUST: 閉域ネットワーク構成では、AWS Lambda から他の AWS サービス（Amazon DynamoDB、Amazon
  S3、Amazon Bedrock など）への通信をすべて VPC エンドポイント経由で VPC 内に完結させる。
- SHOULD: 閉域ネットワーク構成では、Amazon Cognito 認証を Amazon API Gateway の Private API
  経由でプロキシし、閉域環境から Cognito User Pool へ認証リクエストが到達できるようにする。
- MUST: Amazon Cognito でユーザーを認証・認可し、Lambda Authorizer で JWT トークンの有効性
  を検証して、適切に認可されたリクエストのみがバックエンドサービスにアクセスできるようにする。
- SHOULD: 組織の要件に応じて、Amazon Cognito のパスワードポリシーの厳格化（最小文字数・複雑
  性）、MFA の強制適用、適切なセッションタイムアウト設定を検討する。
- SHOULD: Amazon Bedrock のトークン使用量（入力／出力トークン数）、API 呼び出し状況（リクエ
  スト数・エラー率・レスポンス時間）、最近のプロンプト履歴、ユーザーの活動パターンを可視化す
  る CloudWatch 監視ダッシュボードを提供する。
- MUST: すべての操作ログを CloudWatch Logs に記録し、監査およびインシデント調査のために適切
  な保持期間とアクセス制御を設定する。
- MUST: Amazon Bedrock Guardrails を有効化してモデルの入出力をフィルタリングし、クレジット
  カード番号、国際銀行口座番号、AWS アクセスキー、メールアドレス、電話番号、パスワードなどの
  機密情報をブロックする。
- SHOULD: Guardrails を組織のポリシーに合わせてカスタマイズする（日本語対応の追加、金融業界
  向けトピックフィルタ（インサイダー取引、マネーロンダリング、金融規制違反、顧客の機密情報）
  の追加、投資助言や法令違反の恐れがある応答の制限など）。
- WILL: Guardrails はモデルとは独立して設定されるため、複数のモデルに対して共通のポリシーを
  適用できる。
- MUST: 保管データ（Amazon S3、Amazon DynamoDB、OpenSearch、Guardrails）を AWS KMS カスタ
  マーマネージドキーで暗号化し、KMS キーポリシーと鍵ローテーションを管理する。
- MUST: Amazon DynamoDB テーブルのポイントインタイムリカバリ（PITR）を有効化する。
- PREFER: サーバーレスのマネージドサービス（AWS Lambda、Amazon API Gateway、Amazon
  DynamoDB、Amazon Bedrock）を優先し、運用負荷の軽減、利用量に応じた自動スケーリング、標準で
  の高可用性を得る。
- WILL: Amazon Bedrock はモデルの学習に顧客データを使用しない設計であり、入力データの機密性
  が保護される。
- MUST: インフラストラクチャを AWS CDK でコードとして管理し、開発・検証・本番の各環境を再現
  可能にし、構成変更履歴をバージョン管理して監査可能性を確保する。
- MAY: 全機能が必要な場合は、閉域版の代わりに通常版（非閉域版）の GenU を使用する。閉域版は
  外部 IdP との SAML 統合、Voice Chat、AgentCore Chat をサポートせず、デプロイリージョンとモ
  デルのリージョンが同一である必要があるため。
- MUST NOT: 閉域版が外部 IdP との SAML 統合、Voice Chat、AgentCore Chat をサポートすると想定
  しない。これらは現在この構成では対象外である。

### Key Components

#### フロントエンド Web アプリケーション

- **Component Overview**: GenU の Web UI を配信する。閉域版では静的ファイルを CDN ではなく分
  離サブネット内のロードバランサーとコンテナタスクで配信し、通信を VPC 内に閉じる。
- **Assumed AWS Services**: Application Load Balancer、Amazon ECS Fargate、Amazon VPC（分離
  サブネット）。

#### 認証・認可

- **Component Overview**: ユーザーのサインアップ・サインインとリクエスト認可を管理する。閉域
  環境では専用の API Gateway プロキシが認証リクエストを Cognito User Pool に中継し、Lambda
  Authorizer が JWT トークンを検証する。
- **Assumed AWS Services**: Amazon Cognito、Amazon API Gateway（Private API）、AWS Lambda
  （Lambda Authorizer）。

#### バックエンド API・アプリケーションロジック

- **Component Overview**: チャット・生成・要約などのユースケースのビジネスロジックをホスト
  し、フロントエンドから呼び出され、VPC エンドポイント経由でデータストアや Amazon Bedrock と
  連携する。
- **Assumed AWS Services**: Amazon API Gateway、AWS Lambda（VPC 接続）。

#### 生成 AI 推論・RAG

- **Component Overview**: 基盤モデルの推論と、ナレッジ検索のための RAG を提供する。GenU の
  ユースケースが使用する音声・ナレッジサービスも含む。Lambda からのアクセスは VPC エンドポイ
  ント経由。
- **Assumed AWS Services**: Amazon Bedrock、Amazon Bedrock Knowledge Bases、Amazon Bedrock
  Agents、Amazon Kendra、Amazon Transcribe。

#### 出力制御（Guardrails）

- **Component Overview**: モデルの入出力をフィルタリングし、機密情報や金融固有の拒否トピック
  をブロックする。強化構成では日本語対応と金融トピックフィルタを追加している。
- **Assumed AWS Services**: Amazon Bedrock Guardrails。

#### データ永続化

- **Component Overview**: チャット履歴、システムコンテキスト、生成物を保存する。KMS カスタ
  マーマネージドキーで暗号化し、DynamoDB テーブルは PITR で保護する。
- **Assumed AWS Services**: Amazon DynamoDB、Amazon S3、AWS KMS。

#### 音声・メディアサービス（フロントエンドからの直接アクセス）

- **Component Overview**: 音声認識・音声合成やメディア生成機能を、VPC エンドポイント経由でフ
  ロントエンドから直接利用できるようにする。
- **Assumed AWS Services**: Amazon Transcribe、Amazon Polly、AWS Lambda（VPC 接続）。

#### ネットワーク接続

- **Component Overview**: VPC 内での名前解決と AWS サービスへのプライベート接続を提供し、閉域
  版がインターネットへの egress を回避できるようにする。
- **Assumed AWS Services**: Amazon VPC、Route 53 Resolver エンドポイント、Interface VPC エン
  ドポイント、Gateway VPC エンドポイント。

#### 監視・監査

- **Component Overview**: 利用状況とコストを可視化し、操作ログとモデル呼び出しログを監査のた
  めに記録する。ダッシュボードでトークン使用量、呼び出し回数、サインイン数、プロンプトログを
  表示する。
- **Assumed AWS Services**: Amazon CloudWatch（ダッシュボード、Logs）、AWS CloudTrail、VPC
  フローログ。

## FISC コンプライアンスサマリ

本アセットは **FISC 安全対策基準（第 13 版）** の実務基準（実務基準）にマッピングされている。
マッピング表は、実務基準番号ごとに、共通統制環境（ガバナンスベーステンプレート）の対策、本生
成 AI ワークロードテンプレートの対策、使用者の追加の考慮事項を記載する。記載は BLEA for FSI
で対応する対策のみであり、システム全体の安全対策はユーザーアプリケーションの実装や運用・開発
プロセスも含めて検討する必要がある。

生成 AI 側の代表的な対策には次のものが含まれる。Amazon Cognito によるユーザー保護（実 1）、
クライアント通信の閉域ネットワークへの限定（実 2、実 4、実 34）、S3／DynamoDB への IAM ベー
スのアクセス制御と AWS KMS 暗号化（実 3、実 13、実 30）、CloudWatch Logs と VPC フローログ
（実 10、実 72）、CDK によるコード化と DynamoDB PITR の有効化（実 39、実 42）、Amazon Bedrock
Guardrails によるコンテンツフィルタリング（実 69、実 152）、CloudWatch ダッシュボード監視と
CloudTrail 監査による AI 利用ガバナンス（実 151、実 152）。多くの実務基準は、金融取引を行う
サービスではないこと、管理・運用プロセスや開発プロセスでの対策であること、または AWS クラウ
ド側で対策済みであることを理由に対象外とされている。

すべての実務基準（各 実 N の項目）を省略なく記載した表は `references/fisc-mapping.md` に保存
している。

## リファレンスアーキテクチャ

閉域ネットワークアーキテクチャは Amazon VPC 内で完結する。分離サブネット内のブラウザがフロン
トエンド（Application Load Balancer + Amazon ECS Fargate）にアクセスし、AWS Lambda 関数とフ
ロントエンドは各 AWS サービスへアクセスする（Amazon DynamoDB と Amazon S3 へは Gateway VPC
エンドポイント経由、Amazon Bedrock・Amazon Transcribe・Amazon Polly・Amazon Cognito・Amazon
Kendra などへは Interface VPC エンドポイント経由）。認証は Amazon API Gateway の Private API
を経由して Amazon Cognito に中継され、Route 53 Resolver エンドポイントが VPC 内での名前解決を
提供する。

アーキテクチャ図は `assets/images/arch.png`、技術的な詳細（機能、セキュリティ強化、アーキテ
クチャ上の特徴、閉域版の機能制限）は `references/architecture.md` を参照。

## CDK サンプル概要

No CDK sample is provided for this asset in BLEA for FSI v1.6; this asset is documentation only.
（本アセットには BLEA for FSI v1.6 の CDK サンプルは提供されておらず、本アセットはドキュメン
トのみである。）

BLEA for FSI リポジトリには本ワークロードの CDK アプリケーションは含まれていない。代わりに、
外部の AWS Samples GenU リポジトリを特定のコミットでクローンし、ソースドキュメントに同梱され
たカスタマイズパッチ（`changes.diff`）を適用することでサンプルを実現する。デプロイ手順（外部
GenU プロジェクトのクローン／パッチ／ビルド／デプロイ、Bedrock モデル呼び出しログの設定、動作
確認）は参考として `references/deployment.md` に記載している。実際にデプロイされる CDK コード
は本アセットではなく外部の GenU リポジトリに存在する。
