# ガバナンスベース アーキテクチャ詳細

本ドキュメントは BLEA for FSI ガバナンスベースの技術的な構成要素を記述する。ガバナンスベースは
AWS Control Tower によるマルチアカウント環境を前提に、セキュアなベースラインを確立するための
共通基盤である。すべての金融ワークロードはこのガバナンスベースの上にデプロイされる。

## 構成機能の一覧

ガバナンスベースは下記の機能から構成される。実現方法（AWS サービス / CDK）を併記する。

| #   | 機能                                                       | 実現方法（AWS サービス/CDK）                                                                                        |
| --- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| 1   | セキュリティ関連 AWS サービスの有効化                      | AWS CloudTrail<br>AWS Config<br>AWS Security Hub<br>AWS GuardDuty<br>AWS IAM Access Analyzer<br>AWS Trusted Advisor |
| 2   | ログ集約                                                   | Control Tower                                                                                                       |
| 3   | Control Tower コントロール（旧ガードレール）               | Control Tower                                                                                                       |
| 4   | セキュリティアラート                                       | CDK                                                                                                                 |
| 5   | ユーザーの多要素認証                                       | IAM Identity Center                                                                                                 |
| 6   | IAM ポリシー/ロール、IAM グループの準備                    | CDK                                                                                                                 |
| 7   | （オプション）CloudTrail データイベントの有効化            | CDK                                                                                                                 |
| 8   | （オプション）SSM セッションマネージャーの監査ログ取得     | CDK                                                                                                                 |

## 1. セキュリティ関連 AWS サービスの有効化

Control Tower を利用することで、ガバナンスベースの一部の機能は自動的に設定される。Control Tower が
対応していないセキュリティサービスは AWS Organizations に対して一括有効化を行うことで、以後新しい
アカウントが作られると自動的に設定される。

Organizations 全体に対して AWS Security Hub、Amazon GuardDuty および IAM Access Analyzer を有効化し、
これらの委任アカウント（委任された管理者）として Audit アカウントを指定する。AWS Trusted Advisor の
組織ビューの有効化はオプションである。

以下の内容は Control Tower およびセキュリティサービスの Organizations 対応により設定される。

- CloudTrail による 管理 API のロギング
- AWS Config による構成変更の記録
- Security Hub による通知の集約
- GuardDuty による異常なふるまいの検知

## 2. ログの集約

AWS CloudTrail、AWS Config のログは各アカウントごとに個別に保管するのではなく、ログ集約アカウント
（Control Tower 環境下では Log Archive アカウント）上の S3 バケットに集約して保管する。Control Tower
使用時は各ゲストアカウントに対して自動的に AWS CloudTrail、AWS Config の有効化および集約ログの設定を
行う。

> **Note**
> CloudTrail 用の CloudWatch Logs ロググループは、集約アカウントではなく各アカウント個別に準備している。
> これは BLEA for FSI ではゲストアカウントのログ監視はゲストアカウント側の管理者が実施すべきと考えるため
> である。

CDK スタック中で `cloudtrail-trail.ts` コンストラクトを実行することで、CloudTrail 用の CloudWatch Logs
ロググループをゲストアカウント上に作成できる。

## 3. Control Tower コントロール（旧ガードレール）

Control Tower はコントロールとしてアカウントの統制機能（予防的統制/発見的統制）を提供する。これらの
コントロールは内部的には SCP、Config ルールを利用して実現しているため、ユーザー側で同等の SCP または
Config ルールを準備することで、Control Tower 相当のコントロールを各アカウント上に準備することができる。

FISC 安全対策基準への対策のために、Control Tower 管理者アカウント上で組織内の OU に向けて追加の
ガードレール（選択的・強く推奨）を有効化する。FISC 実務基準と Control Tower コントロールの対応は
[fisc-mapping.md](fisc-mapping.md) を参照。

## 4. セキュリティアラートの定義

BLEA for FSI では CloudWatch メトリクスフィルターによるアラーム、および EventBridge ルールを使用して、
下記のセキュリティアラート（SNS トピックによるメール配信）を設定している。CDK コンストラクト
`security-alarm.ts` により、ゲストアカウント上にセキュリティアラート定義と配信用の SNS トピックを作成する。

| #   | セキュリティアラートの内容                         | ソース           | タイプ                          |
| --- | -------------------------------------------------- | ---------------- | ------------------------------- |
| 1   | IAM インラインポリシーの削除                       | CloudTrail 証跡  | CloudWatch メトリクスフィルター |
| 2   | 複数回数の権限のない操作またはログイン失敗         | CloudTrail 証跡  | CloudWatch メトリクスフィルター |
| 3   | IAM ユーザーへのアクセスキーの作成                 | CloudTrail 証跡  | CloudWatch メトリクスフィルター |
| 4   | ROOT ユーザーでの直接操作                          | CloudTrail 証跡  | CloudWatch メトリクスフィルター |
| 5   | AWS Config ルールの違反                            | AWS Config       | EventBridge ルール              |
| 6   | AWS Health のイベント通知                          | AWS Health       | EventBridge ルール              |
| 7   | Security Group への変更                            | EC2              | EventBridge ルール              |
| 8   | Network ACL への変更                               | EC2              | EventBridge ルール              |
| 9   | CloudTrail 証跡への変更                            | AWS CloudTrail   | EventBridge ルール              |
| 10  | Security Hub での Critical/High の検出（Findings） | AWS Security Hub | EventBridge ルール              |
| 11  | GuardDuty での検出（Findings）                     | AWS GuardDuty    | EventBridge ルール              |

CloudWatch メトリクスフィルターアラームの評価は 300 秒周期であり、「複数回数の権限のない操作またはログイン
失敗」のしきい値は 5 回、その他は 1 回である。GuardDuty の EventBridge ルールは重要度 4 以上（4〜8.9）の
検出を通知する。Security Hub の EventBridge ルールは重要度 CRITICAL/HIGH かつコンプライアンスステータスが
FAILED、ワークフローステータスが NEW/NOTIFIED、レコード状態が ACTIVE の検出を通知する。SNS トピックは
CloudWatch からの publish を許可し、SSL 経由でない publish を拒否する。

### 自動修復設定を持つ Config ルール

次の自動修復設定を持つ Config ルールを設定している。CDK コンストラクト `security-auto-remediation.ts`
により作成される。

| Config マネージドルールの識別子     | ルール内容                                                                 | 自動修復の内容                              |
| ----------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------- |
| VPC_DEFAULT_SECURITY_GROUP_CLOSED   | デフォルトの Security Group では全てのインバウンド/アウトバウンド通信が許可されていないこと | 対象 Security Group の全てのルールを削除 |

このルールの Config ルール名は `bb-default-security-group-closed` であり、SSM ドキュメント
`AWSConfigRemediation-RemoveVPCDefaultSecurityGroupRules` により自動修復を行う。自動修復は最大 5 回、
60 秒間隔でリトライする。なお 2023/4/26 時点で大阪リージョンにはこの SSM ドキュメントが存在しないため、
大阪リージョンにはこの自動修復はデプロイされない。

## 5. ユーザーの多要素認証（MFA）

Control Tower 管理下のアカウントに対して AWS IAM Identity Center（旧 AWS SSO）で MFA を設定する。全ての
サインインに MFA を有効化するには、MFA 要求の設定を「サインインごと（常時オン）」にする。MFA を強制する
には、MFA デバイスをユーザーが持っていない場合の設定を「サインイン時に MFA デバイスを登録するよう要求する」
にする。

## 6. IAM ポリシー/ロール、IAM グループの準備

BLEA for FSI ガバナンスベースでは以下の 4 種類の IAM ポリシー/ロール および そのポリシーを割り当てた
IAM グループを作成する。CDK コンストラクト `iam-sample.ts` により作成される。

- SysAdmin システム管理者
- IamAdmin IAM 権限のみを持つ管理者
- ReadOnlyAdmin 参照権限のみを持つ管理者
- InstanceOps EC2 周りの権限のみを持つ管理者

SysAdmin、IamAdmin ポリシーは `aws:MultiFactorAuthPresent` が true であること（MFA 認証済み）を条件とし、
課金操作（aws-portal:*Billing）、CloudTrail の削除/停止/更新、KMS の破壊的な操作を拒否する。InstanceOps は
EC2/ELB/CloudWatch/AutoScaling を許可しつつ VPC/サブネット/ルート/ゲートウェイ等のネットワーク変更操作は
拒否する。ReadOnlyAdmin は各サービスの参照系 API のみを許可する。

## 7. CloudTrail データイベントの有効化（オプション）

Control Tower で自動的に有効化される CloudTrail 証跡は管理イベントに対してのみであり、S3 バケットアクセスの
ようなデータイベントに関しては別途有効化する必要がある。FISC 実務基準への対応の観点では、ユーザーデータが
保管される S3 バケットに対しては CloudTrail データイベントの記録を行うことを推奨する。データイベントの
CloudTrail 証跡ログも集約ログに保管する。

CDK スタック（base-ct-logging）でログ集約用アカウントにデータイベント用のログ集約 S3 バケットを作成し、
CDK コンストラクト `cloudtrail-dataevent.ts` により、その S3 バケットに紐付けてゲストアカウントのデータ
イベント用の CloudTrail 証跡を作成する。このコンストラクトはデフォルトではコメントアウトされており、
`controlTowerKMSKeyArn`、`cloudTrailBucketName`、`targetBuckets` を指定して有効化する。CloudTrail 証跡は
Control Tower の KMS キーで暗号化され、CloudWatch Logs ロググループの保持期間は 2 週間である。

## 8. SSM セッションマネージャーの監査ログ取得（オプション）

SSM セッションマネージャー使用時のセッションログの記録を有効化する。CDK コンストラクト
`session-manager-log.ts` により、セッションログ保管用の S3 バケット（`bleafsi-base-sm-auditlog-<アカウント>`）
をゲストアカウント上に作成し、このバケットをセッションマネージャーの設定でログ保管先に指定する。バケットには
`s3:DeleteObject` を拒否するポリシーが付与される。

セッションマネージャー実行時に監査ログを指定された S3 バケットに出力するためには、ログイン対象となる EC2
インスタンスのプロファイルにカスタマー管理ポリシー `BLEA-FSI-BASE-SessionManagerLog-WritePolicy`（ゲスト
アカウント用 CDK テンプレートで生成）を追加する必要がある。このポリシーは `AWSLogs/*` 配下への `s3:PutObject`、
`s3:PutObjectAcl` と `s3:GetEncryptionConfiguration` を許可する。

> **Note**
> Session Manager アクセスログの Log Archive アカウントへのログ集約はサポートされていないため、ゲスト
> アカウントのローカル S3 バケットにログは記録される。

## 参考

- FISC 実務基準と Control Tower コントロールの対応: [fisc-mapping.md](fisc-mapping.md)
- 非 Control Tower 環境でのセットアップ: [non-ct-setup.md](non-ct-setup.md)
- Landing Zone v3.0 の注意事項: [landing-zone-v3.md](landing-zone-v3.md)
- BLEA との差異: [diff-from-blea.md](diff-from-blea.md)
- デプロイ手順: [deployment.md](deployment.md)
