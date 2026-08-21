# ガバナンスベース デプロイ手順

本ドキュメントは AWS Control Tower 管理下のアカウントに BLEA for FSI ガバナンスベースを導入する手順、
Control Tower AFC を利用した自動プロビジョニング、大阪リージョンへのデプロイ、および手作業での設定手順を
記述する。Control Tower を導入していない環境へのデプロイは [non-ct-setup.md](non-ct-setup.md) を参照。

> **作業ディレクトリについて**: 本スキルは読み取り専用のテンプレート提供元である。SKILL.md や
> references 等の CDK 実行に不要なファイルはコピーせず、**CDK 実行に必要な次の 3 つだけ**を、相対参照
>（各 usecase の `tsconfig.json` の `extends: "../../tsconfig.base.json"`、`package.json` の
> `file:"../../resources/bleafsi-shared-constructs/v1.0.0"` — いずれも `assets/sample-cdk/<usecase>/` から
> 見て 2 階層上の `assets/` を指す）が保たれる形で作業ディレクトリ `<workdir>` にコピーする:
>
> - `assets/sample-cdk/` → `<workdir>/assets/sample-cdk/`（`base-ct-guest` / `base-ct-logging` を含む）
> - `assets/tsconfig.base.json` → `<workdir>/assets/tsconfig.base.json`
> - `assets/resources/` → `<workdir>/assets/resources/`（共有ライブラリ bleafsi-shared-constructs）
>
> **コピー先 `<workdir>` は、スキル利用者に次の 3 択で確認すること**: (1) カレントディレクトリ、
> (2) スキル名のディレクトリ（例 `fsi-foundation-governance-base-cdk/`）を新規作成、(3) 利用者が指定するディレクトリ。
> コピー後 `<workdir>/assets/sample-cdk/<usecase>` に移動して CDK コマンドを実行する（以下の
> `cd assets/sample-cdk/<usecase>` はこの移動を指す）。**共有ライブラリに依存するため、初回は
> `<workdir>/assets/resources/bleafsi-shared-constructs/v1.0.0` で `npm install && npm run build` を
> 実行してからデプロイすること。** スキルディレクトリ内で直接 `cdk deploy` しないこと（生成物でスキルが
> 汚れる）。アカウント・リージョンは `bin/parameter.ts` に直接書かず、環境変数 `CDK_DEFAULT_ACCOUNT` /
> `AWS_REGION`（または `--profile`）で与える。

## 導入手順[全体の流れ]

| #   | 手順                                                                     | MC/Local | 対象アカウント                     |
| --- | ------------------------------------------------------------------------ | -------- | ---------------------------------- |
| 1   | AWS Control Tower およびセキュリティサービスのセットアップ               | MC       | CT 管理アカウント                  |
| 2   | デプロイ対象のゲストアカウントを AWS Control Tower で作成する            | MC       | CT 管理アカウント                  |
| 3   | 依存パッケージのインストールとコードのビルド                            | Local    | -                                  |
| 4   | AWS IAM Identity Center（旧 AWS SSO）に合わせて AWS CLI の認証情報を設定 | Local    | -                                  |
| 5   | Control Tower 管理者アカウントでの追加設定                               | MC       | CT 管理アカウント                  |
| 6   | Log Archive アカウント用ガバナンスベースをデプロイする                   | Local    | CT Log Archive アカウント          |
| 7a  | ゲストアカウント用ガバナンスベースをデプロイする                        | Local/MC | ゲストアカウント                   |
| 7b  | Control Tower AFC を利用した自動プロビジョニング                         | MC       | ゲストアカウント                   |
| 8   | （オプション）大阪リージョンにデプロイする                               | Local/MC | CT 管理アカウント/ゲストアカウント |

`MC` はマネジメントコンソールでの作業を、`Local` は手元環境での作業を示す。

## 1. AWS Control Tower およびセキュリティサービスのセットアップ（MC）

Control Tower をセットアップし、Organizations 全体に対して AWS Security Hub、Amazon GuardDuty および
IAM Access Analyzer を有効化する。これらの委任アカウントとして Audit アカウントを指定する。

- Control Tower のセットアップ: AWS ドキュメント「Control Tower のセットアップ」を参照
- Security Hub のセットアップ: 「Organizations 環境下の Security Hub のセットアップ手順」（後述）を参照
- GuardDuty のセットアップ: 「Organizations 環境下の GuardDuty のセットアップ手順」（後述）を参照
- IAM Access Analyzer のセットアップ: AWS ドキュメント「Access Analyzer の設定」を参照
- AWS Trusted Advisor のセットアップ（オプション）: AWS ドキュメント「AWS Trusted Advisor の組織ビュー」を参照

## 2. ゲストアカウントを作成する（MC）

Control Tower の Account Factory を使って新しいアカウント（ゲストアカウント）を作成する。

## 3. 依存パッケージのインストールとコードのビルド（Local）

github から BLEA for FSI の git リポジトリを clone する。

```sh
git clone https://github.com/aws-samples/baseline-environment-on-aws-for-financial-services-institute.git
```

依存する NPM パッケージをインストールする。

```sh
npm ci
```

（デプロイのみの場合は必須ではないが）Git に Commit する際に Linter、Formatter、git-secrets による
チェックを行うための pre-commit hook を登録することを推奨する。

## 4. AWS CLI の認証情報を設定する（Local）

Control Tower 環境では AWS IAM Identity Center（旧 AWS SSO）の利用を推奨する。まず AWS CLI がバージョン 2
以上であることを確認する。

```sh
aws --version
```

`~/.aws/config` に Log Archive アカウント用およびゲストアカウント用のプロファイルを設定する。ここでは
マネジメントアカウント ID を `1111111111111`、Log Archive アカウント ID を `222222222222`、ゲストアカウント
ID を `123456789012` とする。

```text
# for Management Account Login
[profile ct-management-sso]
sso_start_url = https://d-90xxxxxxxx.awsapps.com/start/
sso_region = ap-northeast-1
sso_account_id = 1111111111111
sso_role_name = AWSAdministratorAccess
region = ap-northeast-1

# Accessing with AWSControlTowerExecution Role on Logging Account
[profile ct-logging-exec]
role_arn = arn:aws:iam::222222222222:role/AWSControlTowerExecution
source_profile = ct-management-sso
region = ap-northeast-1

# for Guest Account Login
[profile ct-guest-sso]
sso_start_url = https://d-90xxxxxxxx.awsapps.com/start/
sso_region = ap-northeast-1
sso_account_id = 123456789012
sso_role_name = AWSAdministratorAccess
region = ap-northeast-1
```

Control Tower の仕様により、Audit（Log Archive）アカウントにデプロイするには、まずマネジメントアカウントの
`AWSAdministratorAccess` ロールなど必要な権限を持つロールでログインし、そこからスイッチして処理を実行する必要がある。`ct-management-sso`
プロファイルで SSO ログインし、ラッピングされたプロファイル `ct-logging-exec` を CDK から使用する。ゲスト
アカウントには `ct-guest-sso` プロファイルで SSO ログインする。

AWS IAM Identity Center にログインする例（ゲストアカウント）。

```sh
aws sso login --profile ct-guest-sso
```

## 5. Control Tower 管理者アカウントでの追加設定（MC）

- FISC 安全対策基準への対策のために、組織内の OU に向けて追加のガードレール（選択的・強く推奨）を有効化する。
  対応は [fisc-mapping.md](fisc-mapping.md) を参照。
- AWS IAM Identity Center（旧 AWS SSO）の MFA を必須化する（手順は後述）。

## 6. Log Archive アカウント用ガバナンスベースをデプロイする（Local）

### 6-1. 環境別の設定を指定する

`assets/sample-cdk/base-ct-logging/bin/parameter.ts` を編集する。`dev` と `staging` の例が定義されており、本番用には
`prod` の定義を追加する。

```js
// Parameter for Dev - Anonymous account & region
export const DevParameter: StackParameter = {
  envName: 'Development',
};

// Parameter for Staging
export const StageParameter: StackParameter = {
  envName: 'Staging',
  env: {
    account: '111111111111',
    region: 'ap-northeast-1',
  },
};
```

| key         | value                                                                                  |
| ----------- | -------------------------------------------------------------------------------------- |
| envName     | 環境名。これが各々のリソースタグに設定される                                           |
| env.account | デプロイ対象のアカウント ID。profile で指定するアカウントと一致している必要がある      |
| env.region  | デプロイ対象のリージョン（東京 ap-northeast-1 を想定）                                 |

開発環境では AWS SSO でログインしているアカウントにデプロイするように環境変数からアカウントとリージョンを
取得する。`account` を明示的に指定した場合は、CLI Profile で指定するアカウント/リージョンと一致していないと
デプロイできない。Staging 以降の環境では `account` を指定することを推奨する。

### 6-2. Log Archive アカウントにデプロイする

```sh
aws sso login --profile ct-management-sso

cd assets/sample-cdk/base-ct-logging
npx cdk bootstrap --profile ct-logging-exec   # 初回のみ
npx cdk deploy --profile ct-logging-exec
```

このデプロイで S3 バケット（CloudTrail データイベント、大阪リージョン用の Config データ用）が作成される。
デプロイ完了時に集約ログ用の S3 バケット名（`BLEAFSI-LogBase-Dev.SharedLogBucket`）が出力されるので記録する。

> NOTE: BLEA 環境にインストールしたローカルの cdk を利用するため `npx` を使用する。IAM ポリシーに関する
> 変更確認をスキップしたい場合は `--require-approval never` オプションを指定する。

## 7. ゲストアカウント用ガバナンスベースをデプロイする（Local/MC）

> 注意: Control Tower Landing Zone v2.9 以前の環境、または v3.0 にアップデートした環境にデプロイする際の
> 注意点は [landing-zone-v3.md](landing-zone-v3.md) を参照。環境によってはソースコードの修正が必要になる。

### 7-1. デプロイ情報（Context）を設定する（Local）

`assets/sample-cdk/base-ct-guest/bin/parameter.ts` を編集する。

```js
export const DevParameter: StackParameter = {
  envName: 'Development',
  account: process.env.CDK_DEFAULT_ACCOUNT,
  primary: {
    region: 'ap-northeast-1',
  },
  secondary: {
    region: 'ap-northeast-3',
  },
  securityNotifyEmail: 'notify-security@example.com',
  controlTowerKMSKeyArn: 'dummy-key-arn',
  cloudTrailBucketName: 'dummy-bucket-name',
  targetBuckets: ['dummy-bucekt-name'],
};
```

| key                   | value                                                                                          |
| --------------------- | ---------------------------------------------------------------------------------------------- |
| envName               | 環境名。これが各々のリソースタグに設定される                                                   |
| account               | デプロイ対象のアカウント ID。profile で指定するアカウントと一致している必要がある              |
| primary.region        | デプロイ対象の Primary リージョン（東京 ap-northeast-1 を想定）                                |
| secondary.region      | デプロイ対象の Secondary リージョン（大阪 ap-northeast-3 を想定）。省略可能                     |
| securityNotifyEmail   | セキュリティに関する通知が送られるメールアドレス                                               |
| controlTowerKMSKeyArn | 7-5-d 参照。CloudTrail による S3 データイベントを記録する際のみ使用                             |
| cloudTrailBucketName  | 7-5-d 参照。CloudTrail による S3 データイベントを記録する際のみ使用                             |
| targetBuckets         | 7-5-d 参照。CloudTrail による S3 データイベントを記録する際のみ使用                             |

### 7-2. ゲストアカウントにデプロイする（Local）

```sh
aws sso login --profile ct-guest-sso

cd assets/sample-cdk/base-ct-guest
npx cdk bootstrap --profile ct-guest-sso    # 初回のみ（Primary/Secondary の各リージョン）
npx cdk deploy BLEAFSI-Base-Primary-Dev --profile ct-guest-sso
```

スタック名は環境ごとに異なる（xxx-Dev は開発環境用）。デプロイ完了時に Session Manager ログ用 S3 バケット名
（`BLEAFSI-Base-Primary-Dev.SSMSessionManagerLogBucket`）が出力されるので記録する。

このデプロイで以下がセットアップされる。

- デフォルトセキュリティグループの閉塞（逸脱した場合自動修復）
- AWS Health イベントの通知
- セキュリティに影響する変更操作の通知
- メールによるセキュリティイベントの通知
- S3 バケット作成（SSM セッションマネージャーの S3 ロギング）

### 7-3. アカウントの S3 パブリックアクセスのブロック設定（MC）

アカウント全体で Amazon S3 のパブリックアクセスをブロックする。

### 7-4. セキュリティ指摘事項の修復

デプロイ後でも Security Hub のベンチマークレポートで CRITICAL または HIGH でレポートされる検出項目が
ある。これらには手動で対応（Remediation）が必要である。

### 7-5. その他のオプションのセットアップ（MC）

- **a. Systems Manager Quick Setup**: EC2 を利用する場合は Systems Manager による管理を推奨。Quick Setup は
  IAM インスタンスプロファイルロールの設定、SSM Agent の隔週自動アップデート、30 分ごとのインベントリ収集、
  パッチ不足検出の日次スキャン、CloudWatch agent のインストール/月次アップデートを提供する。
- **b. Trusted Advisor の検知結果レポート**: AWS ベストプラクティスのアドバイスをメールで定期受信可能。
- **c. Amazon Macie**: 機械学習とパターンマッチングにより S3 バケット上の機密データ（PII 等）を検出・保護。
- **d. CloudTrail による S3 データイベントの記録**: デフォルトでは全アカウントで CloudTrail の管理操作 API
  呼出が記録される。データイベントの有効化は必要に応じて実施する。ユーザーデータが保管される S3 バケットには
  データイベントの記録を推奨する。有効化するには `parameter.ts` に下記 3 要素を指定し、`lib/bleafsi-base-ct-guest-stack.ts`
  の項番 6 のコメントを外す。

  | 変数名                | 値                                                                                    |
  | --------------------- | ------------------------------------------------------------------------------------- |
  | controlTowerKMSKeyArn | Control Tower 管理者アカウントで設定されている KMS 暗号化キーの ARN                    |
  | cloudTrailBucketName  | Log Archive アカウントに作成した集約ログ用の S3 バケット名（手順 6-2）                 |
  | targetBuckets         | CloudTrail データイベント取得の対象となる S3 バケット名（リスト形式で複数指定可）      |

  KMS 暗号化キーの ARN は、Control Tower 管理者アカウントにログインし、Control Tower サービスのメニューから
  「ランディングゾーン設定」→「設定」タブ→「KMS 暗号化」>「キー ARN」の値をコピーして得る。設定後に
  `BLEAFSI-Base-Dev` スタックをデプロイする。

- **e. SSM セッションマネージャーの S3 ログ出力を手動でセットアップ**: 後述の手作業設定手順を参照。

## 7b. Control Tower AFC を利用した自動プロビジョニング

Control Tower Account Factory Customization（AFC）を使用すると、Control Tower でのゲストアカウント作成時に
ガバナンスベースを自動的にプロビジョニングできる。AFC は Service Catalog に登録した CloudFormation テンプレートを
ブループリントとして使用する。

### 1. 事前準備

Service Catalog ハブアカウントを利用する前提とする。

1. **Service Catalog ハブアカウントの準備**: Control Tower Account Factory で新規アカウントを作成する。
2. **IAM ロールの準備**: Control Tower 管理アカウントから Service Catalog ハブアカウント上の Service Catalog への
   アクセスを許可するため、IAM ロール `AWSControlTowerBlueprintAccess` をハブアカウント上で作成する。この作業は
   ハブアカウント上で `AWSControlTowerExecution` ロールにスイッチロールしてから行う（それ以外のロールで作成すると
   SCP により処理が失敗する）。

   - 許可ポリシー: `AWSServiceCatalogAdminFullAccess`、`AmazonS3ReadOnlyAccess`
   - 信頼関係: `AWSControlTowerAdmin` サービスロールと、アカウント作成時に使用するロールの ARN を Principal に指定

   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Principal": {
                   "AWS": [
                   "arn:aws:iam::<CT管理カウントのアカウントID>:role/service-role/AWSControlTowerAdmin",
                   "<CT管理アカウントでアカウントを作成する際に使用するロールのARN>"
                   ]
               },
               "Action": "sts:AssumeRole"
           }
       ]
   }
   ```

3. **Service Catalog での権限設定**: Control Tower 管理者アカウントで下記を実行し、Service Catalog と StackSets に
   Organizations の権限を委譲する。

   ```sh
   aws organizations enable-aws-service-access --service-principal servicecatalog.amazonaws.com
   aws organizations enable-aws-service-access --service-principal member.org.stacksets.cloudformation.amazonaws.com
   ```

### 2. ブループリント用 CloudFormation テンプレートの準備

リポジトリを clone し `npm ci` を実行、`parameter.ts` を設定した後、cdk synth で CloudFormation テンプレートを
生成する。

```sh
cd assets/sample-cdk/base-ct-guest
npx cdk synth BLEAFSI-Base-AFC -j --version-reporting false > governance-base-blueprint.json
npx ts-node update-template
```

`update-template.ts` は生成した CloudFormation テンプレートから `Rules` と `Parameters` セクションを削除する。

### 3. Service Catalog へのブループリントの登録

Service Catalog ハブアカウントまたは Control Tower 管理者アカウント上で作業する。Service Catalog の[製品]
リストで[製品を作成]し、`governance-base-blueprint.json` をアップロードして製品を作成する（製品名: BLEA for
FSI Governance Base、方法の選択: テンプレートファイルの使用）。AFC から利用する場合は製品をポートフォリオに
追加してアカウントと共有する必要はない。

### 4. ゲストアカウントへのブループリントの適用

Control Tower 管理者アカウントで、アカウントの新規作成または更新時にブループリントを適用する。アカウント作成/
更新画面の[アカウントファクトリーのカスタマイズ - オプション]で以下を入力する。

- AWS Service Catalog の製品を含むアカウント: Service Catalog ハブアカウントのアカウント ID（12 桁）
- 製品を選択: BLEA for FSI Governance Base
- デプロイメントリージョン: ホームリージョン

実行終了後に[ブループリント名]、[ブループリントステータス]、[ブループリント製品バージョン]を確認する。

## 8. （オプション）大阪リージョンへのデプロイ

大阪リージョンを利用したマルチリージョン構成では、以下の手順に従う。

| #   | 手順                                                      | MC/Local | 対象アカウント                     |
| --- | --------------------------------------------------------- | -------- | ---------------------------------- |
| 1   | Security Hub の検出結果の集約で大阪リージョンを追加       | MC       | CT Audit アカウント                |
| 2   | 大阪リージョンでの Security Hub の有効化                  | MC       | ゲストアカウント                   |
| 3   | 大阪リージョンでの GuardDuty の有効化                     | MC       | ゲストアカウント                   |
| 4   | ゲストアカウント用ガバナンスベースをデプロイする         | Local    | CT 管理アカウント/ゲストアカウント |

1. **Security Hub の検出結果の集約に大阪リージョンを追加（MC）**: Control Tower Audit アカウントで、Security Hub の
   [設定]→[リージョン]タブ→[編集]で「アジアパシフィック（大阪）」をチェックして保存する。
2. **大阪リージョンでの Security Hub の有効化（MC）**: ゲストアカウントでリージョンを大阪に切り替え、Security Hub を
   有効化する。
3. **大阪リージョンでの GuardDuty の有効化（MC）**: ゲストアカウントでリージョンを大阪に切り替え、GuardDuty を
   有効化する。
4. **デプロイ（Local）**: `parameter.ts` の `secondary.region`（ap-northeast-3）と `cloudTrailBucketName` を指定する。
   ゲストアカウントに再ログインしてデプロイする（大阪リージョンの CDK ブートストラップは完了している前提）。

   ```sh
   aws sso logout --profile ct-management-sso
   aws sso login --profile ct-guest-sso

   cd assets/sample-cdk/base-ct-guest
   npx cdk deploy BLEAFSI-Base-Secondary-Dev --profile ct-guest-sso
   ```

   このデプロイで大阪リージョンに AWS Health イベント通知、セキュリティ変更操作の通知、メール通知、Session Manager
   ログ用 S3 バケットがセットアップされる。

## 手作業での設定手順

### Organizations 環境下の Security Hub のセットアップ手順

1. Organizations 管理アカウントにログイン
2. Security Hub 管理者アカウントとして Audit アカウントを指定（CLI の場合）

   ```
   aws securityhub enable-organization-admin-account --region ap-northeast-1 --admin-account-id #auditアカウントのID#
   ```

3. Audit アカウントにログイン
4. [Security Hub]→[設定]で「このリージョンで組織の Security Hub を有効化する」を有効化
5. 「Auto Enable default Standards」を ON にする（OFF にすると「AWS 基礎セキュリティのベストプラクティス」と
   「CIS AWS Foundations Benchmark」が自動有効化されない）。「Auto-enable accounts」を ON にすると全メンバー
   アカウントで自動有効化される。

### Organizations 環境下の GuardDuty のセットアップ手順

1. Organizations 管理アカウントにログイン
2. GuardDuty の委任された管理者として Audit アカウントを指定（CLI の場合）

   ```
   aws guardduty enable-organization-admin-account --region ap-northeast-1 --admin-account-id #auditアカウントのID#
   ```

3. Audit アカウントにログイン
4. [GuardDuty]→[設定]→[アカウント]で「このリージョンで Organization の GuardDuty を有効化する」を有効化。この設定で
   全メンバーアカウントで自動有効化される。S3 保護と Kubernetes Audit Logs Monitoring はオプション。

### AWS IAM Identity Center（旧 AWS SSO）の MFA 設定手順

1. **MFA の有効化**: MFA 要求の設定を「サインインごと（常時オン）」にする。
2. **MFA デバイスの強制設定**: MFA デバイスをユーザーが持っていない場合の設定を「サインイン時に MFA デバイスを
   登録するよう要求する」にする。

### SSM セッションマネージャーの S3 ログ出力を手動でセットアップ

AWS ドキュメントの「Amazon S3 を使用してセッションデータをログ記録する（コンソール）」の手順を実行し、手順 6-2 の
CDK テンプレートで作成した S3 バケットにセッションログを保管する。「S3 のキープレフィックス」は `AWSLogs` を指定する。

**[重要]** セッションマネージャー実行時に監査ログを S3 バケットに出力するためには、ログイン対象の EC2 インスタンスの
プロファイルにカスタマー管理ポリシー `BLEA-FSI-BASE-SessionManagerLog-WritePolicy`（ゲストアカウント用 CDK テンプレートで
生成）を追加する必要がある。このポリシーがないとセッション開始が S3 への権限エラーで失敗する。

> NOTE: Session Manager アクセスログの Log Archive アカウントへのログ集約はサポートされていないため、ログはゲスト
> アカウントのローカル S3 バケットに記録される。
