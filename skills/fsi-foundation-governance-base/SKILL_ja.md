---
name: fsi-foundation-governance-base
description: >-
  BLEA for FSI（金融リファレンスアーキテクチャ日本版）リファレンスアーキテクチャの共通ガバナンス
  ベースライン（ガバナンスベース / Governance Base）。AWS Control Tower / AWS Organizations 環境全体に、
  セキュアで FISC 準拠のマルチアカウント基盤を確立する。ガードレール（Control Tower コントロール）、
  ログ集約、セキュリティサービス（Security Hub、GuardDuty、Config、CloudTrail、IAM Access Analyzer）の
  有効化、セキュリティアラート、自動修復、IAM ベースラインを含む。他のすべての FSI ワークロードの土台と
  なるガバナンスベースの設計・デプロイ・説明を行うとき、FISC 安全対策基準 実務基準へのコントロールの
  マッピング、base-ct-guest / base-ct-logging CDK サンプルの利用、Control Tower AFC による自動プロビジョ
  ニング、非 Control Tower 環境でのセットアップを扱うときに使用する。
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI ガバナンスベース (Governance Base)

## ワークロード概要

ガバナンスベースは BLEA for FSI（Baseline Environment on AWS for Financial Services Institute）の共通・
基盤レイヤーである。マルチアカウント AWS 環境全体にセキュアなベースラインを確立し、他のすべての FSI
ワークロード（勘定系、顧客チャネル、オープン API、マーケットデータ、データ分析プラットフォーム等）が
一貫した FISC 準拠のガバナンスの上にデプロイされるようにする。

AWS Control Tower および AWS Organizations の上に構築され、組織内の全アカウントに対して以下を提供する。

- **マルチアカウントガバナンス** — AWS Control Tower がランディングゾーン（管理、Audit、Log Archive
  アカウントおよびゲストアカウント）を管理する。Control Tower が対応しないセキュリティサービスは AWS
  Organizations レベルで一括有効化し、新規作成されたアカウントが自動的に継承するようにする。
- **ガードレール（Control Tower コントロール）** — FISC 安全対策基準 第11版 実務基準の観点で選定した
  予防的・発見的コントロール（内部的には SCP と AWS Config ルールで実装される）。
- **ログ集約** — CloudTrail の管理イベントログと AWS Config の構成変更履歴を Log Archive アカウントに
  集約する。CloudTrail S3 データイベントログ用の集約 S3 バケットを Log Archive アカウントに作成する。
- **セキュリティ検知・通知** — Security Hub、GuardDuty、Config、CloudTrail、IAM Access Analyzer の
  有効化に加え、CloudWatch メトリクスフィルターアラームと EventBridge ルールが SNS 経由でメールにより
  セキュリティアラートを配信し、Config による自動修復を行う。
- **IAM ベースライン** — 4 つの管理者ロール向けのサンプル IAM ポリシー/ロール/グループ。

ガバナンスベースは 2 つの CDK サンプルでデプロイする。`base-ct-guest`（ゲストアカウントごとのベースライン、
Primary + オプションの Secondary/大阪リージョン）と `base-ct-logging`（Log Archive アカウントの集約バケット）
である。AWS Control Tower 環境を対象とするが、シングルアカウント／非 Control Tower 環境でも再現できる。

## ベストプラクティスと主要コンポーネント

### ベストプラクティス

- MUST: 最初に AWS Control Tower をセットアップする。ランディングゾーン構築時に Control Tower がいくつかの
  ガバナンス機能を自動的に設定する。
- MUST: AWS Security Hub、Amazon GuardDuty、IAM Access Analyzer を AWS Organizations 全体で有効化し、
  委任された管理者を Audit アカウントとすることで、新規アカウントが自動的に継承するようにする。
- MUST: CloudTrail S3 データイベント取得を有効化する前に、Log Archive アカウントのガバナンスベース
  （`base-ct-logging`）をデプロイする。作成される集約 S3 バケットがそれらのログの出力先となるためである。
- MUST: FISC 向けに推奨される追加の Control Tower ガードレール（FISC マッピングで "◯" のもの）を、Control
  Tower 管理アカウントから対象 OU に対して有効化する。
- MUST: `parameter.ts` のデプロイ対象 `account` の値を、使用する AWS CLI プロファイルのアカウントと一致
  させ、誤ったアカウントにワークロードをデプロイしないようにする。
- MUST: デプロイ後、各ゲストアカウントでアカウントレベルの Amazon S3 パブリックアクセスをブロックする。
- MUST NOT: Control Tower AFC 用の IAM ロール `AWSControlTowerBlueprintAccess` を、Service Catalog ハブ
  アカウントで `AWSControlTowerExecution` 以外のロールで作成しない。他のロールで作成すると SCP により処理が
  失敗する。
- SHOULD: Control Tower 環境では長期的な認証情報ではなく AWS IAM Identity Center（旧 AWS SSO）を利用し、
  すべてのサインインで MFA を強制する。
- SHOULD: FISC 実務基準への対応の観点から、ユーザーデータを保管するバケットに対して CloudTrail S3 データ
  イベント記録を有効化する（オプション、デフォルトは無効）。
- SHOULD: デプロイ後に残存する CRITICAL / HIGH の Security Hub 検出項目を修復する。ベースラインは
  すべてを自動的には解決しない。
- SHOULD: Staging および Production 環境では `parameter.ts` の `account` フィールドを明示的に指定する。
- PREFER: 多数のアカウントをオンボードする場合、手動でアカウントごとに CDK デプロイするよりも、Service
  Catalog ブループリントを用いた Control Tower Account Factory Customization（AFC）でアカウント作成時に
  ゲストアカウントのガバナンスベースを自動プロビジョニングする方を選ぶ。
- MAY: マルチリージョン構成として、ゲストのガバナンスベースを大阪リージョン（ap-northeast-3）に Secondary
  リージョンとしてデプロイしてよい。利用しない場合は `secondary.region` を省略する。
- MAY: 要件に応じて追加の運用ベースライン（Systems Manager Quick Setup、Trusted Advisor レポート、Amazon
  Macie）を手動で有効化してよい。
- WILL: Control Tower Landing Zone v3.0 は CloudTrail ログを管理アカウントの CloudWatch Logs に集約し、
  ゲストアカウントごとのロググループを作成しなくなるため、一部の環境では `base-ct-guest` のソース修正が必要
  になる。
- WILL: BLEA for FSI はアラート用にゲストアカウント独自の CloudTrail 証跡を作成するため、CloudTrail 証跡が
  二重に記録されることがある（Control Tower の組織レベルの証跡と BLEA for FSI のゲストアカウントの証跡）。
- WILL: デフォルトセキュリティグループの自動修復（Config ルール `VPC_DEFAULT_SECURITY_GROUP_CLOSED`）は、
  SSM ドキュメント `AWSConfigRemediation-RemoveVPCDefaultSecurityGroupRules` が大阪リージョンで利用でき
  ないため、大阪リージョンにはデプロイされない。
- MUST: このスキルから構築する全ての CDK Stack に cdk-nag の AwsSolutionsChecks を Aspects で適用し、未抑制の AwsSolutions-* 検出が 0 件であることを CI テスト（jest 等）でゲートする。例外は NagSuppressions に reason を明記して抑制する（詳細は references/cdk-nag.md）。

### 主要コンポーネント

#### base-ct-logging スタック（Log Archive アカウント）

- **コンポーネント概要**: Control Tower の Log Archive アカウントにデプロイする。CloudTrail S3 データ
  イベントログおよび大阪リージョンの Config データを保管する集約 S3 バケット（`BLEAFSI-LogBase`、名前
  `bleafsi-logbase-shared-log-<アカウント>`）を作成する。1825 日（5 年）のライフサイクル有効期限、
  `s3:DeleteObject` を拒否するポリシー、`cloudtrail.amazonaws.com` と `config.amazonaws.com` への配信権限を
  持つ。バケット名は CloudFormation 出力として出力される。
- **想定される AWS サービス**: Amazon S3、AWS IAM、AWS CloudFormation（AWS CDK 経由）。

#### CloudTrail 証跡（base-ct-guest）

- **コンポーネント概要**: Control Tower LZ v3.0 以降でもアカウントローカルのアラートを機能させるため、
  ゲストアカウントの CloudTrail 証跡を作成する。証跡ログ用 S3 バケット（180 日ライフサイクル）、CloudTrail
  ログ暗号化用 KMS CMK、CloudWatch Logs ロググループ（3 ヶ月保持）を、ファイル検証・グローバルサービス
  イベント有効で作成する。Landing Zone のバージョンに応じて、既存の `aws-controltower/CloudTrailLogs`
  ロググループを参照するブロックと切り替えられる。
- **想定される AWS サービス**: AWS CloudTrail、Amazon S3、AWS KMS、Amazon CloudWatch Logs。

#### Security Alarm（base-ct-guest）

- **コンポーネント概要**: SNS トピック経由でメール配信するセキュリティアラートを定義する。CloudTrail
  ロググループに対する 4 つの CloudWatch Logs メトリクスフィルターアラーム（IAM ポリシー変更、複数回の
  権限のない操作/ログイン失敗、新規アクセスキー作成、ROOT ユーザーの操作）と 7 つの EventBridge ルール
  （Config ルールのコンプライアンス変更、AWS Health イベント、Security Group 変更、Network ACL 変更、
  CloudTrail 設定変更、Security Hub の CRITICAL/HIGH 検出、重大度 4 以上の GuardDuty 検出）を使用する。
  SNS トピックは SSL 経由の publish のみを許可する。
- **想定される AWS サービス**: Amazon CloudWatch（アラーム・Logs）、Amazon EventBridge、Amazon SNS、AWS IAM。

#### Security Auto-Remediation（base-ct-guest）

- **コンポーネント概要**: AWS Config マネージドルール `VPC_DEFAULT_SECURITY_GROUP_CLOSED`（ルール名
  `bb-default-security-group-closed`）と、SSM ドキュメント
  `AWSConfigRemediation-RemoveVPCDefaultSecurityGroupRules`（デフォルトセキュリティグループの全ルールを削除）
  を SSM オートメーションロール経由で実行する自動修復を作成する。大阪リージョンにはデプロイされない。
- **想定される AWS サービス**: AWS Config、AWS Systems Manager（Automation）、AWS IAM。

#### Session Manager Log（base-ct-guest）

- **コンポーネント概要**: SSM Session Manager の監査ログ用 S3 バケット
  （`bleafsi-base-sm-auditlog-<アカウント>`）をゲストアカウント上に作成する。`s3:DeleteObject` を拒否する
  ポリシーと、`AWSLogs/*` 配下へのログ書き込みを許可するカスタマー管理 IAM ポリシー（EC2 インスタンス
  プロファイルにアタッチ）を持つ。バケット名は CloudFormation 出力である。Session Manager ログの Log
  Archive アカウントへの集約はサポートされていないため、ログはゲストアカウントに留まる。
- **想定される AWS サービス**: Amazon S3、AWS IAM、AWS Systems Manager（Session Manager）。

#### IAM Sample（base-ct-guest）

- **コンポーネント概要**: 4 つの管理者ロール向けのサンプル IAM ポリシー/ロールと IAM グループを作成する。
  SysAdmin（システム管理者）、IamAdmin（IAM 権限のみの管理者）、ReadOnlyAdmin（参照権限のみの管理者）、
  InstanceOps（EC2 周りの管理者）。権限を持つロールは MFA（`aws:MultiFactorAuthPresent`）を要求し、課金、
  CloudTrail の改ざん、破壊的な KMS 操作を拒否する。
- **想定される AWS サービス**: AWS IAM。

#### CloudTrail Data Event（base-ct-guest、オプション）

- **コンポーネント概要**: オプション（デフォルトはコメントアウト）。指定した対象バケットの S3 データ
  イベント用 CloudTrail 証跡を作成する。Control Tower の KMS キーで暗号化し、Log Archive の集約バケットに
  出力、CloudWatch Logs グループの保持期間は 2 週間。`parameter.ts` に `controlTowerKMSKeyArn`、
  `cloudTrailBucketName`、`targetBuckets` を設定し、ゲストスタックの該当ブロックのコメントを外して有効化する。
- **想定される AWS サービス**: AWS CloudTrail、Amazon S3、AWS KMS、Amazon CloudWatch Logs。

#### 組織レベルのセキュリティサービス

- **コンポーネント概要**: CDK 外で AWS Organizations / Control Tower レベルで有効化する。AWS Security Hub、
  Amazon GuardDuty、IAM Access Analyzer を Audit アカウントを委任された管理者として組織全体で有効化し、
  AWS CloudTrail（管理イベントのロギング）と AWS Config（構成記録）は Control Tower により有効化される。
  AWS Trusted Advisor の組織ビューはオプション。新規メンバーアカウントはこれらを自動的に継承する。
- **想定される AWS サービス**: AWS Security Hub、Amazon GuardDuty、AWS IAM Access Analyzer、AWS CloudTrail、
  AWS Config、AWS Trusted Advisor、AWS Organizations、AWS Control Tower。

## FISC 準拠サマリー

ガバナンスベースは AWS Control Tower コントロール（ガードレール）を FISC 安全対策基準 第11版 実務基準に
マッピングする。2023/10/13 時点で Control Tower コントロールは全 459 個。プロアクティブ動作のコントロールと
必須ガイダンスのコントロールを除く 224 個を分析し、FISC 実務基準の観点で有効化すべきものを EC2、IAM、RDS、
S3、CloudTrail、KMS、ECR、ECS、Lambda、GuardDuty にわたって選定している。コントロールは AWS Config ルールか
SCP のいずれかで実装され、ガイダンスレベルは「強く推奨」と「選択的」がある。

完全な（省略のない）マッピング表（各コントロール ID、FISC 実務基準項目、ガイダンスレベル、重大度、サービス、
有効化推奨の有無、コメント）は [references/fisc-mapping.md](references/fisc-mapping.md) を参照。

## リファレンスアーキテクチャ

ガバナンスベースは Control Tower の管理・Audit・Log Archive アカウントと各ゲストアカウントにまたがり、Primary
リージョン（東京 ap-northeast-1）とオプションの Secondary リージョン（大阪 ap-northeast-3）に展開される。
組織レベルのセキュリティサービス有効化、Control Tower ガードレール、Log Archive アカウントでのログ集約、
アラート・自動修復・Session Manager ログ・IAM ベースライン用のゲストアカウントごとの CDK コンストラクトを
組み合わせる。

コンポーネントの機能、AWS サービスのマッピング、非 Control Tower 環境でのセットアップ、Landing Zone v3.0 の
注意事項、上流 BLEA との差異を含む技術的な詳細は以下を参照。

- [references/architecture.md](references/architecture.md) — アーキテクチャとコンポーネントの内訳。
- [references/non-ct-setup.md](references/non-ct-setup.md) — シングルアカウント／非 Control Tower 環境での
  セットアップ（Config ルールとセキュリティアラートの一覧を含む）。
- [references/landing-zone-v3.md](references/landing-zone-v3.md) — Control Tower Landing Zone v3.0 の
  アップデート注意事項と必要なソース修正。
- [references/diff-from-blea.md](references/diff-from-blea.md) — BLEA for FSI が上流 BLEA とどう異なるか。

## CDK サンプル概要

[assets/sample-cdk/](assets/sample-cdk/) 配下の 2 つの CDK サンプルがガバナンスベースをプロビジョニングする
（TypeScript、AWS CDK）。

> **ベースラインのセキュリティに関する注意**: 本スキルはセキュリティ ガバナンスベースそのものであり、ガードレール・監査ログ・検出的統制が成果物で、脅威の多くは既に緩和済みである。ただし下流で判断すべき残存事項が残る: 同梱の IAM サンプルロールは意図的に広く最小権限へ絞る必要があり、CloudTrail の S3 データイベントは既定オフ、デフォルト SG の自動修復は自動実行され、集約ログバケットは Object Lock 未設定である。各サンプルは `SECURITY_NOTICE.md` を同梱し、`cdk synth` / `cdk deploy` のたびに警告を表示する。

- **`base-ct-logging`** — Control Tower の **Log Archive** アカウントにデプロイする。CloudTrail S3 データ
  イベントログと大阪リージョンの Config データを保管する集約 S3 バケット（5 年ライフサイクル）を作成する。
  プロジェクトプレフィックスは `BLEAFSI-LogBase`。
- **`base-ct-guest`** — 各 **ゲスト** アカウント（Primary およびオプションの Secondary リージョン）に
  デプロイする。ゲストベースラインをプロビジョニングする: CloudTrail 証跡 + KMS + CloudWatch Logs、SNS
  メール配信付きの CloudWatch/EventBridge セキュリティアラーム、Config によるデフォルト SG の自動修復、
  Session Manager 監査ログバケット、IAM サンプルロール/グループ、オプションの CloudTrail S3 データイベント
  証跡。プロジェクトプレフィックスは `BLEAFSI-Base`。スタックは `BLEAFSI-Base-Primary-Dev`、
  `BLEAFSI-Base-Secondary-Dev`、および `BLEAFSI-Base-AFC`（`cdk synth` による Control Tower AFC ブループリント
  生成用）。

デプロイ順序: Control Tower と組織レベルのセキュリティサービスを有効化 → ゲストアカウントを作成 →
`base-ct-logging` を Log Archive にデプロイ → `base-ct-guest` を各ゲストアカウントにデプロイ（手動または
Control Tower AFC 経由）。

コピーされた `assets/sample-cdk/.../test/*.test.ts` は cdk-nag 強制パターンの正となるソースである。
抽出した抑制ルール台帳と、自分の Stack での強制方法は [references/cdk-nag.md](references/cdk-nag.md)
を参照。

手順ごとのデプロイ、AFC 自動プロビジョニング、大阪リージョンのセットアップは
[references/deployment.md](references/deployment.md) を参照。
