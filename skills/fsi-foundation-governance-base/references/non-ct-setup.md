# シングルアカウント／非 Control Tower 環境でのガバナンスベースのセットアップ方法

BLEA for FSI は AWS Control Tower によるマルチアカウント環境を前提に構成されているが、本ドキュメントでは
シングルアカウントや非 Control Tower 環境のアカウントにガバナンスベースと同等の統制機能をセットアップする
方法を説明する。出典は `doc/governance-base/how-to-setup-governance-base-in-nonct-env.md`。

> **Note**
> 各金融ワークロード サンプルアプリケーションは Control Tower 環境を前提にしていないため、非 Control Tower
> 環境で動かすために特別な対応は必要ない。

ガバナンスベースは下記の機能から構成される。

| #   | 機能                                                       | 実現方法（AWS サービス/CDK)                                                                                          |
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

下記の AWS サービスを手作業で有効化する。

- AWS CloudTrail
- AWS Config
- AWS Security Hub
- AWS GuardDuty
- AWS IAM Access Analyzer
- AWS Trusted Advisor（オプション）

## 2. ログの集約

AWS CloudTrail、AWS Config のログはログ集約アカウント（Control Tower 環境下では Log Archive アカウント）上の
S3 バケットに集約して保管する。Control Tower 使用時は各ゲストアカウントに対して自動的に有効化および集約ログの
設定が行われるが、非 Control Tower 環境下ではユーザー側で実施する必要がある。

> **Note**
> CloudTrail 用の CloudWatch Logs ロググループは、集約アカウントではなく各アカウント個別に準備する。これは
> BLEA for FSI ではゲストアカウントのログ監視はゲストアカウント側の管理者が実施すべきと考えるためである。

ガバナンスベースの CDK スタック中で `usecases/base-ct-guest/lib/cloudtrail-trail.ts` コンストラクトを実行する
ことで、CloudTrail 用の CloudWatch Logs ロググループをゲストアカウント上に作成できる。

## 3. Control Tower コントロール（旧ガードレール）

Control Tower のコントロールは内部的には SCP、Config ルールを利用して実現しているため、ユーザー側で同等の
SCP または Config ルールを準備することで、Control Tower 相当のコントロールを各アカウント上に準備できる。BLEA
for FSI で適用を推奨しているコントロールに対する Config ルールの対応は以下の通り。

| マネージドルール識別子                | 対象リソース   | ルール内容                                                                                                                                 |
| ------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| ROOT_ACCOUNT_MFA_ENABLED              | ROOT ユーザ    | ROOT ユーザーに対して MFA が有効化されていることを確認                                                                                     |
| IAM_ROOT_ACCESS_KEY_CHECK             | ROOT ユーザ    | ROOT ユーザーに対してアクセスキーが作成されていないことを確認                                                                              |
| IAM_USER_MFA_ENABLED                  | IAM ユーザ     | IAM ユーザーの MFA が有効になっていることを確認                                                                                            |
| MFA_ENABLED_FOR_IAM_CONSOLE_ACCESS    | IAM ユーザ     | コンソールにアクセスする IAM ユーザーの MFA が有効になっていることを確認                                                                   |
| S3_BUCKET_PUBLIC_READ_PROHIBITED      | S3             | S3 バケットでパブリック読み取りアクセスが許可されていないことを確認                                                                        |
| S3_BUCKET_PUBLIC_WRITE_PROHIBITED     | S3             | S3 バケットでパブリック書き込みアクセスが許可されていないことを確認                                                                        |
| S3_ACCOUNT_LEVEL_PUBLIC_ACCESS_BLOCKS | S3             | S3 に対するパブリックアクセスブロック設定がアカウントレベルから設定されていることを確認                                                    |
| EC2_VOLUME_INUSE_CHECK                | EBS            | EBS ボリュームが EC2 にアタッチされていることを確認                                                                                        |
| EBS_OPTIMIZED_INSTANCE                | EBS            | EBS 最適化できる EC2 インスタンスに対して EBS 最適化が有効になっていることを確認                                                           |
| ENCRYPTED_VOLUMES                     | EBS            | EC2 インスタンスにアタッチされた EBS ボリュームが暗号化されていることを確認                                                                |
| EC2_EBS_ENCRYPTION_BY_DEFAULT         | EBS            | EBS ボリュームの暗号化がデフォルトで有効になっていることを確認                                                                             |
| RDS_INSTANCE_PUBLIC_ACCESS_CHECK      | RDS            | RDS インスタンスに対してパブリックアクセスが可能になっていない（publiclyAccessible フィールドが false）ことを確認                          |
| RDS_SNAPSHOTS_PUBLIC_PROHIBITED       | RDS            | RDS のスナップショットがパブリックでない事を確認                                                                                           |
| RDS_STORAGE_ENCRYPTED                 | RDS            | RDS DB インスタンスに対してストレージの暗号化が有効になっていることを確認                                                                  |
| RESTRICTED_INCOMING_TRAFFIC           | Security Group | 使用中の Security Group が特定のポートに対して無制限のインバウンド通信を許可していない事を確認<br>[対象ポート] 20, 21, 3389, 3306, 4333    |
| INCOMING_SSH_DISABLED                 | Security Group | Security Group に対して無制限の SSH アクセスが許可されていないことを確認                                                                   |

詳細は [fisc-mapping.md](fisc-mapping.md) を参照。

## 4. セキュリティアラートの定義

BLEA for FSI では CloudWatch メトリクスフィルターによるアラーム、および EventBridge ルールを使用して、下記の
セキュリティアラート（SNS トピックによるメール配信）を設定している。CDK コンストラクト
`usecases/base-ct-guest/lib/security-alarm.ts` により、ゲストアカウント上にアラート定義と配信用 SNS トピックを
作成できる。

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

また、次の自動修復設定を持つ Config ルールを設定している。CDK コンストラクト
`usecases/base-ct-guest/lib/security-auto-remediation.ts` により作成できる。

| Config マネージドルールの識別子   | ルール内容                                                                 | 自動修復の内容                       |
| --------------------------------- | -------------------------------------------------------------------------- | ------------------------------------ |
| VPC_DEFAULT_SECURITY_GROUP_CLOSED | デフォルトの Security Group では全てのインバウンド/アウトバウンド通信が許可されていないこと | 対象 Security Group の全てのルールを削除 |

## 5. IAM ポリシー/ロール、IAM グループの準備

BLEA for FSI ガバナンスベースでは以下の 4 種類の IAM ポリシー/ロール および そのポリシーを割り当てた IAM
グループを作成している。CDK コンストラクト `usecases/base-ct-guest/lib/iam-sample.ts` により作成できる。

- SysAdmin システム管理者
- IamAdmin IAM 権限のみを持つ管理者
- ReadOnlyAdmin 参照権限のみを持つ管理者
- InstanceOps EC2 周りの権限のみを持つ管理者

## 6. CloudTrail データイベントの有効化（オプション）

Control Tower で自動的に有効化される CloudTrail 証跡は管理イベントに対してのみであり、S3 バケットアクセスの
ようなデータイベントは別途有効化する必要がある。データイベントの CloudTrail 証跡ログも集約ログに保管する。

ガバナンスベースでは、CDK スタック `usecases/base-ct-logging/lib/bleafsi-base-ct-logging-stack.ts` を実行して
ログ集約用アカウントにデータイベント用の集約 S3 バケットを作成できる。また CDK コンストラクト
`usecases/base-ct-guest/lib/cloudtrail-dataevent.ts` を実行して、その S3 バケットに紐付けてゲストアカウントの
データイベント用 CloudTrail 証跡を作成できる。

## 7. SSM セッションマネージャーの監査ログ取得（オプション）

SSM セッションマネージャー使用時のセッションログの記録を有効化する。CDK コンストラクト
`usecases/base-ct-guest/lib/session-manager-log.ts` を実行してセッションログ保管用の S3 バケットを作成し、
このバケットをセッションマネージャーの設定でログ保管先に指定する。詳細は [deployment.md](deployment.md) の
「SSM セッションマネージャーの S3 ログ出力を手動でセットアップ」を参照。
