# CDK サンプル実装の詳細 [顧客チャネル]

本ドキュメントは、`assets/sample-cdk/`（元: `usecases/guest-customer-channel-sample`）に含まれる AWS CDK（TypeScript）サンプルアプリケーションの構成を、ソースコードから読み取れる事実に基づいて解説するものである。

> **注意**: 本サンプルは Amazon Connect の Preview API を使用しており、今後仕様変更される可能性がある。また、アーキテクチャ図の全機能を実装しているわけではない（設定の定期バックアップなどは未実装）。

## スタック構成

CDK アプリのエントリポイントは `bin/bleafsi-guest-customer-channel-sample.ts` であり、`createStacks()` 関数が環境パラメータ（`bin/parameter.ts` の `DevParameter` など）に基づいて以下のスタックを生成する。プロジェクトプレフィックスは `BLEAFSI-CustomerChannel`。

| スタック | 生成条件 | リージョン | 主な内容 |
| --- | --- | --- | --- |
| `{prefix}-{env}-Waf` (CloudFrontWafStack) | `enableCallMonitoring` が true | us-east-1（固定） | CloudFront 用 WAF Web ACL |
| `{prefix}-{env}-Tertiary` (CustomerChannelTertiaryStack) | `tertiaryRegion` 指定時 | 例: ap-northeast-3 | バックアップ用 KMS キー・S3 バケット（レプリケーション先） |
| `{prefix}-{env}-Primary` (CustomerChannelPrimaryStack) | 常時 | 例: ap-northeast-1 | Amazon Connect インスタンス本体と各種サンプル機能 |
| `{prefix}-{env}-Secondary` (CustomerChannelSecondaryStack) | `secondaryRegion` 指定時（ターシャリ必須） | 例: ap-southeast-1 | DR 用 Amazon Connect インスタンス |

- 各スタックには `Environment` タグ（環境名）が付与される。
- リージョン間参照のため `crossRegionReferences: true` を設定。
- 既定の `DevParameter` では secondaryRegion がコメントアウトされ、Primary + Tertiary + Waf の 3 スタック構成となる。

## Primary スタック（CustomerChannelPrimaryStack）

`lib/stacks/customer-channel-primary-stack.ts` が以下のリソース・サンプルを構築する。

1. **録音用 KMS キー** (`RecordingKey`, キーローテーション有効)。
2. **アクセスログバケット** (`AccessLogsBucket`, S3 マネージド暗号化) と **録音バケット** (`RecordingBucket`, KMS 暗号化, アクセスログ有効)。いずれも `PrivateBucket` コンストラクト。
3. **Amazon Connect インスタンス** (`CustomerChannelConnectInstance`)。
4. **ターシャリスタック存在時**: 録音バケットからバックアップバケットへのクロスリージョンレプリケーション（`BucketReplication`）を設定。
5. **アウトバウンドサンプル** (`CustomerChannelOutboundSample`)。
6. **WAF スタック存在時**: 通話モニタリングサンプル (`CallMonitoringSample`) と Web 通話サンプル (`WebCallSample`) をデプロイ。
7. **Amazon Q in Connect サンプル** (`QconnectSample`, 既定有効)。
8. **即時インバウンドサンプル** (`ImmediateInboundSample`)。既定キュー `BasicQueue` と Q in Connect アシスタントを連携。
9. **Customer Profiles サンプル** (`CustomerProfilesSample`, 既定有効)。
10. **Cases サンプル** (`CasesSample`, 既定有効)。

## Amazon Connect インスタンス（CustomerChannelConnectInstance）

`lib/samples/connect-instance/index.ts`。

- **インスタンス属性（既定値）**: inboundCalls=true, outboundCalls=true, autoResolveBestVoices=true, contactflowLogs=true, contactLens=true, earlyMedia=true, useCustomTtsVoices=false。
- **ID 管理方式**: `CONNECT_MANAGED`（既定）/ `SAML` / `EXISTING_DIRECTORY`。SAML の場合、`iam.SamlProvider`、`connect:GetFederationToken` を許可する IAM ロール、リレーステート URL を生成し `CfnOutput` で出力する。
- **S3 ストレージ設定**: 通話録音 (CALL_RECORDINGS)、チャットトランスクリプト (CHAT_TRANSCRIPTS)、スケジュールレポート (SCHEDULED_REPORTS) を録音バケットに KMS 暗号化して保存。
- **CTR（コンタクトトレースレコード）**: Amazon Data Firehose（`CfnDeliveryStream`, DirectPut, CMK 暗号化）経由で S3 に保存。Firehose 用ロールには最小権限の S3/KMS ポリシーを付与。
- **管理ユーザー**: `adminUsers` 指定時、セキュリティプロファイル `CustomerChannelAdmin`、ルーティングプロファイル（VOICE/CHAT/TASK/EMAIL のメディア同時実行数設定）、ソフトフォンユーザーを作成。

## インバウンドサンプル

### 通常インバウンド（inbound-sample）

`lib/samples/inbound-sample/index.ts`。

- **Amazon Lex ボット** `IdentificationBot`（本人確認用、日本語 `ja_JP`、`polly:SynthesizeSpeech` 許可、`autoBuildBotLocales` 有効）を作成し、バージョン・エイリアスを発行、Amazon Connect と関連付け（`LexIntegrationAssociation`）。定義は `lex-bot-definition.json`。
- **インバウンドコンタクトフロー** `IdentificationInboundContactFlow`（`inbound-contact-flow.json`）: Lex ボット・キュー・エージェントウィスパーフローを変数で埋め込む。
- **エージェントウィスパーフロー** `IdentificationAgentWhisperFlow`（`agent-whisper-flow.json`）。

### 即時インバウンド（immediate-inbound-sample）

`lib/samples/immediate-inbound-sample/index.ts`。コミュニケーションウィジェット（チャット / Web 通話）用のフロー。

- 顧客キュー再生フロー `ImmediateCustomerQueueFlow`（`CustomerQueue.wav` プロンプト）。
- エージェントウィスパーフロー `ImmediateAgentWhisperFlow`（`Beep.wav` プロンプト）。
- インバウンドフロー `ImmediateInboundContactFlow`（キュー ARN、顧客キューフロー、エージェントウィスパー、Q in Connect アシスタント ARN を変数で埋め込む）。

## アウトバウンドサンプル（outbound-sample）

`lib/samples/outbound-sample/index.ts`。

- **発信記録テーブル** `ContactTable`（Amazon DynamoDB, パーティションキー `ContactId`）。
- **発信ステートマシン** `StartOutboundStateMachine`（AWS Step Functions, EXPRESS 型）: Amazon Connect `StartOutboundVoiceContact` を呼び出し、結果を DynamoDB に `INITIATED` 状態で保存。トレーシング・ログ有効。
- **発信 API** `StartOutboundApi`（Amazon API Gateway REST API, IAM 認証, リクエストバリデーション, アクセスログ）。デプロイ時に IAM SigV4 署名付き curl コマンドを `CfnOutput` で出力。
- **通話終了ワークフロー** `EndOutboundContactStateMachine`: EventBridge ルール（`aws.connect` の `DISCONNECTED` / VOICE イベント）を起点に、`GetContactAttributes` を呼び出して DynamoDB レコードを `DISCONNECTED` 状態に更新。
- **アウトバウンドコンタクトフロー** `SampleOutboundContactFlow`（`outbound-contact-flow.json`）。

## Amazon Q in Connect サンプル（qconnect-sample）

`lib/samples/qconnect-sample/qconnect-sample.ts`。

- **ソースバケット** (`QconnectSourceBucket`, KMS 暗号化)。AppIntegrations 用のバケットポリシーを付与。
- **アシスタント** `MyAssistant`（KMS 暗号化）と Amazon Connect の Wisdom 関連付け。
- **データ統合** `MyDataIntegration`（Amazon AppIntegrations, S3 ソース）と **ナレッジベース**（EXTERNAL 型）を作成し、アシスタントと関連付け。
- **AI プロンプト（日本語向け）と使用モデル**:
  - QueryReformulation: `apac.amazon.nova-lite-v1:0`
  - RecommendIntentLabeling: `apac.amazon.nova-lite-v1:0`
  - ManualSearch (Answer Generation): `apac.anthropic.claude-3-5-sonnet-20241022-v2:0`
  - AnswerGeneration (Self-Service): `apac.amazon.nova-pro-v1:0`
  - PreProcessing (Self-Service): `apac.anthropic.claude-3-haiku-20240307-v1:0`
  - プロンプトテンプレートは `prompt/*.yaml`。
- **AI エージェント**: 回答レコメンド (ANSWER_RECOMMENDATION)、マニュアル検索 (MANUAL_SEARCH)、セルフサービス (SELF_SERVICE) をそれぞれ構成・アシスタントに割り当て。
- **KMS キーポリシー**: チャットでの Q in Connect 有効化のため `connect.amazonaws.com` に kms:Decrypt 等を許可。
- **モニタリング**: CloudWatch Logs（`/aws/qconnect/assistants`, 保持 1 ヶ月）への EVENT_LOGS 配信を設定。

## 通話モニタリングサンプル（call-monitoring-sample）

`lib/samples/call-monitoring-sample/call-monitoring-sample.ts` および `constructs/`。

- **Auth**: Amazon Cognito ユーザープール（`CallMonitoringAuthUserPool` プレフィックス）。
- **Api**: AWS AppSync（GraphQL）と DynamoDB テーブル。
- **Kinesis**: Amazon Kinesis Data Streams（`connect-analytics-stream`, ON_DEMAND）で Amazon Connect のリアルタイム音声セグメント（REAL_TIME_CONTACT_ANALYSIS_VOICE_SEGMENTS）を受信。
  - `connect-event-process` Lambda（Node.js 22.x）: EventBridge の通話イベント（CONNECTED_TO_AGENT / INITIATED / DISCONNECTED, VOICE / TASK）を処理し Kinesis に投入。
  - `kinesis-process` Lambda: Kinesis からデータを受け取り AppSync に mutate。要約 Lambda を呼び出す。
  - `bedrock-summary` Lambda: Amazon Bedrock で会話要約。
  - `bedrock-check-transcript` Lambda: Amazon Bedrock（既定モデル: `anthropic.claude-3-sonnet-20240229-v1:0`, リージョン us-east-1）で文字起こしデータのコンプライアンスチェックを実施。チェック項目（顧客名・電話番号の確認、プラン説明の実施、断られた後の勧誘継続などの違反）を JSON 配列で判定し、結果とコストを DynamoDB に保存。
- **Frontend**: React 製管理画面。CloudFront + WAF で配信。
- **AppIntegrations Application** `Call monitoring` としてエージェントワークスペースに統合（`ApplicationIntegrationAssociation`）。付与する権限: User.Details.View, User.Configuration.View, User.Status.View, Contact.Details.View, Contact.CustomerDetails.View, Contact.Attributes.View。

## Customer Profiles サンプル（customer-profiles-sample）

`lib/samples/customer-profiles-sample/customer-profiles-sample.ts`。

- ドメイン `amazon-connect-customer-channel-domain`（既定有効期限 366 日、KMS 暗号化、名寄せ / ルールベースマッチング有効）。ドメイン名を `amazon-connect-` で始めることでサービスロールに権限追加なしでアクセス可能。
- CTR オブジェクトタイプ（テンプレート `CTR-NoInferred`）で Amazon Connect と統合。

## Cases サンプル（cases-sample）

`lib/samples/cases-sample/cases-sample.ts`。

- Amazon Connect Cases ドメイン `connect-cases-domain` を作成し、Amazon Connect と統合（`IntegrationType.CASES_DOMAIN`）。

## Web 通話サンプル（web-call-sample）

`lib/samples/web-call-sample/index.ts`。

- アクセスログバケットとアセットバケット（S3 マネージド暗号化, パブリックアクセスブロック, SSL 強制）。
- CloudFront ディストリビューション（`S3OriginDistribution`, WAF 関連付け）。
- React 製の架空銀行サイト `mock-bank-site` を `NodejsBuild`（deploy-time-build）でビルドしデプロイ。ビルド時に Connect FQDN、ウィジェット ID、スニペット ID を環境変数として渡す。
- `FrontendUrl`（CloudFront URL）を `CfnOutput` で出力。

## Secondary / Tertiary スタック

- **Secondary**（`customer-channel-secondary-stack.ts`）: DR 用 Amazon Connect インスタンス。録音・CTR はターシャリスタックのバックアップバケット / キーに保存。ローカル録音用 KMS キーを別途作成。
- **Tertiary**（`customer-channel-tertiary-stack.ts`）: バックアップ用 KMS キー（`BackupKey`）、バックアップアクセスログバケット、バックアップバケット（`BackupBucket`, KMS 暗号化）。Primary / Secondary のレプリケーション先として公開プロパティで参照される。

## CloudFront WAF スタック（CloudFrontWafStack）

`lib/samples/call-monitoring-sample/waf-stack.ts`。

- CloudFront 用 WAF Web ACL（scope=CLOUDFRONT, us-east-1）。既定アクションは block。
- 許可 IP アドレス（IPv4 / IPv6）を IPSet として設定。既定では全 IP を許可（`0.0.0.0/1`, `128.0.0.0/1`, `::/1`, `8000::/1`）しており、Context（`wafIpv4AllowAddresses` / `wafIpv6AllowAddresses`）で絞り込む。
- CloudWatch メトリクス・サンプルリクエスト記録を有効化。
