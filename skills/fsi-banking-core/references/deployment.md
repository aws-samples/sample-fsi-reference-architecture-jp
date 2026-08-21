# デプロイ手順 [勘定系 / Core Banking]

BLEA for FSI のガバナンスベースがデプロイされたアカウントに、勘定系ワークロードのサンプルコードを導入する手順をまとめる。CDK サンプルコードは `assets/sample-cdk/` に同梱している。

> **作業ディレクトリについて**: 本スキルは読み取り専用のテンプレート提供元である。SKILL.md や
> references 等の CDK 実行に不要なファイルはコピーせず、**CDK 実行に必要な次の 2 つだけ**を、
> 相対参照（`assets/sample-cdk/tsconfig.json` の `extends: "../../tsconfig.base.json"`）が保たれる
> 形で作業ディレクトリ `<workdir>` にコピーする:
>
> - `assets/sample-cdk/` → `<workdir>/assets/sample-cdk/`
> - `tsconfig.base.json` → `<workdir>/tsconfig.base.json`
>
> **`assets/sample-cdk/` は `node_modules` を含め丸ごとコピーすること**（`rsync --exclude
> 'node_modules'` 等で依存キャッシュとして除外しないこと）。
> `lib/shared/sample-multi-region-app/canary/nodejs/node_modules/index.js` は CloudWatch
> Synthetics Canary の規約上 `nodejs/node_modules/` 配下への配置が必須な**ハンドラ実体コード**であり、
> 一般的な `node_modules` とは異なり再生成できない。除外すると `npm test` が `HandlerNotFound` で
> 失敗する。
>
> **コピー先 `<workdir>` は、スキル利用者に次の 3 択で確認すること**: (1) カレントディレクトリ、
> (2) スキル名のディレクトリ（例 `fsi-banking-core-cdk/`）を新規作成、(3) 利用者が指定するディレクトリ。
> コピー後 `<workdir>/assets/sample-cdk` に移動して CDK コマンドを実行する（以下の `cd assets/sample-cdk`
> はこの移動を指す）。スキルディレクトリ内で直接 `cdk deploy` しないこと（`node_modules`/`cdk.out` 等の
> 生成物でスキルが汚れる）。アカウント・リージョンは `bin/parameter.ts` に直接書かず、環境変数
> `CDK_DEFAULT_ACCOUNT` / `AWS_REGION`（または `--profile`）で与える。

> 表記凡例: `MC` はマネジメントコンソールでの作業、`Local` は手元環境での作業を示す。

## 導入手順

ゲストアカウントに SSO で認証している状態からのデプロイメント手順を示す。

### 1. ゲストアカウントデプロイ用の AWS CLI プロファイルを設定する

ゲストアカウントにデプロイするための AWS CLI プロファイルを設定する。以下ではゲストアカウントの ID を `123456789012` としている（`~/.aws/config`）。

```sh
# for Guest Account Login
[profile ct-guest-sso]
sso_start_url = https://d-90xxxxxxxx.awsapps.com/start/
sso_region = ap-northeast-1
sso_account_id = 123456789012
sso_role_name = AWSAdministratorAccess
region = ap-northeast-1
```

### 2. 環境別の設定を指定する

デプロイ前に環境別（開発、ステージング、本番等）の情報を指定する必要がある。`bin/parameter.ts` を編集する。

```sh
assets/sample-cdk/bin/parameter.ts
```

このサンプルは `dev` と `staging` という開発・検証用の設定を定義する例である。本番アカウントにもデプロイできるようにするには、`prod` 用の定義を追加する。

```js
// Parameter for Dev - Anonymous account & region
export const DevParameter: StackParameter = {
  envName: 'Development',
  account: process.env.CDK_DEFAULT_ACCOUNT,
  notifyEmail: 'notify-monitoring@example.com',
  dbUser: 'dbadmin',
  hostedZoneName: 'example.com',
  primary: {
    region: 'ap-northeast-1',
    regionCidr: '10.100.0.0/16',
    vpcCidr: '10.100.0.0/20',
    tgwAsn: 64512,
  },
  secondary: {
    region: 'ap-northeast-3',
    regionCidr: '10.101.0.0/16',
    vpcCidr: '10.101.0.0/20',
    tgwAsn: 64513,
  },
  monitoring: {
    region: 'us-west-2',
    regionCidr: '10.102.0.0/16',
    vpcCidr: '10.102.0.0/20',
    tgwAsn: 64514,
  },
};
```

`StageParameter` も同様の構造で定義する。設定内容は以下のとおり。

| key | value |
| --- | --- |
| envName | 環境名。これが各々のリソースタグに設定される |
| account | デプロイ対象のアカウント ID |
| notifyEmail | 通知が送られるメールアドレス |
| dbUser | AuroraDB へのログインユーザ名 |
| hostedZoneName | Route53 Private Hosted Zone に指定するドメイン名 |
| primary.region | プライマリをデプロイするリージョン |
| primary.regionCidr | プライマリリージョンの CIDR |
| primary.vpcCidr | プライマリで作成する VPC の CIDR（regionCidr に含まれる必要あり） |
| primary.tgwAsn | プライマリで作成する Transit Gateway の ASN |
| secondary.region | セカンダリをデプロイするリージョン |
| secondary.regionCidr | セカンダリリージョンの CIDR |
| secondary.vpcCidr | セカンダリで作成する VPC の CIDR（regionCidr に含まれる必要あり） |
| secondary.tgwAsn | セカンダリで作成する Transit Gateway の ASN |
| monitoring.region | 外形監視 Canary をデプロイするリージョン（監視リージョン） |
| monitoring.regionCidr | 監視リージョンの CIDR |
| monitoring.vpcCidr | 監視リージョンに作成する VPC の CIDR（regionCidr に含まれる必要あり） |
| monitoring.tgwAsn | 監視リージョンに作成する Transit Gateway の ASN |

### 3. テスト用サンプルアプリケーションをデプロイ設定

勘定系ワークロードのサンプルコードでは、ECS コンテナ上で稼働するサンプルアプリケーションとして下記の 2 種類を提供する。

1. **amazon-ecs-sample** として公開されている PHP ベースのアプリケーション（https://hub.docker.com/r/amazon/amazon-ecs-sample ）
2. **マルチリージョン環境で動作するマイクロサービス・アプリケーション** — 実際に東京リージョン/大阪リージョンでフェイルオーバー可能な TypeScript で実装されたマイクロサービス・アプリケーション

デフォルトではいずれのアプリケーションも、勘定系ワークロードのリソースと同時に AWS アカウント環境にはデプロイされない。サンプルアプリケーションをデプロイする場合は、`bin/parameter.ts` の `deploy` フラグを `true` に変更する。

> 注: どちらか片方のアプリケーションのみをデプロイすること。

```js
///// テスト用サンプルアプリケーション の設定 //////

// シンプルなECSコンテナアプリケーションの設定
export const SampleEcsAppParameter = {
  // デプロイする場合は true に指定
  deploy: false,
  // 動作確認用 NLB を作成するかどうか
  createTestResource: true,
};

// マルチリージョン マイクロサービス・アプリケーションの設定
export const SampleMultiRegionAppParameter = {
  // デプロイする場合は true に指定
  deploy: false,
  // 実行確認用のクライアントを配置するVPCのCIDR
  appClientVpcCidr: '10.103.0.0/24',
};
```

マルチリージョン マイクロサービス・アプリケーションは、デプロイ時にローカル環境で docker イメージをビルドする。そのため、docker デーモンが起動している必要がある。ビルド時にエラーが発生した場合は「[サンプルアプリデプロイ時のエラー対応](./sample-app-workaround.md)」を参照。

### 4. 勘定系ワークロードをデプロイする

（ログインしていない場合）AWS IAM Identity Center（旧 AWS SSO）を使ってゲストアカウントにログインする。

```sh
aws sso login --profile ct-guest-sso
```

ゲストアカウントで CDK ブートストラップを実行する（parameter.ts に指定した 2 つのリージョンでブートストラップ処理が行われる）。

```sh
cd assets/sample-cdk
npx cdk bootstrap --profile ct-guest-sso
```

サンプルコードをデプロイする。勘定系ワークロードの CDK サンプルコードは複数のスタックから構成されていて、順に実行される。

| スタック | 説明 |
| --- | --- |
| BLEAFSI-CoreBanking-primary-xx | 主リージョン（東京リージョン）にリソースをデプロイ |
| BLEAFSI-CoreBanking-secondary-xx | 副リージョン（大阪リージョン）にリソースをデプロイ |
| BLEAFSI-CoreBanking-monitoring-xx | 監視リージョン（オレゴンリージョン）にリソースをデプロイ |

```sh
npx cdk deploy "*Dev" --require-approval never --profile ct-guest-sso
```

> NOTE:
>
> - `"*Dev"` はデプロイ対象の開発環境用のスタック（末尾が `-Dev` のスタック）を実行する。環境（開発、ステージング、本番）によって変更する（例: `"*Prod"`）。
> - デプロイ時に IAM ポリシーに関する変更確認をスキップするために `--require-approval never` オプションを指定している。
> - デプロイ時に、以下のリソースで、タイミングによって `Create_Failed` エラーが発生するケースがある。その場合はデプロイの再実行を行う。
>   - `AWS::ECS::ClusterCapacityProviderAssociations`
>   - `AWS::DynamoDB::GlobalTable`

#### Transit Gateway ピアリングの設定（主リージョン ⇔ 副リージョン）

2 つ目のスタックである `BLEAFSI-CoreBanking-secondary-Dev` の実行が完了すると、Output として下記の 3 つの CLI コマンドが表示される。順に実行する。

| Output | 説明 |
| --- | --- |
| CLIforTGWpeeringacceptance | 主リージョンと副リージョンの TGW をピアリングするための TGW ピアリングの承認を実施する CLI |
| CLIforaddingTGWrouteinprimaryregion | 主リージョンの Transit Gateway のルートテーブルに副リージョンへのルートを追加する CLI |
| CLIforaddingTGWrouteinsecondaryregion | 副リージョンの Transit Gateway のルートテーブルに主リージョンへのルートを追加する CLI |

TGW ピアリングの承認 → 主リージョンのルート追加 → 副リージョンのルート追加、の順に実行する。承認が有効になるには少し時間がかかるため、承認後 2-3 分待ってから次のコマンドを実行する。

```sh
# TGW ピアリング承認
aws ec2 accept-transit-gateway-peering-attachment --region <主リージョン> --transit-gateway-attachment-id xx --profile ct-guest-sso

# 主リージョンのルートテーブルに副リージョンへのルートを追加
aws ec2 create-transit-gateway-route --region <主リージョン> --destination-cidr-block <副リージョンのCIDR> --transit-gateway-route-table-id <主リージョンのTGWのルートテーブルのID> --transit-gateway-attachment-id <TGWのPeering AttachmentのID> --profile ct-guest-sso

# 副リージョンのルートテーブルに主リージョンへのルートを追加
aws ec2 create-transit-gateway-route --region <副リージョン> --destination-cidr-block <副リージョンのCIDR> --transit-gateway-route-table-id <副リージョンのTGWのルートテーブルのID> --transit-gateway-attachment-id <TGWのPeering AttachmentのID> --profile ct-guest-sso
```

#### Transit Gateway ピアリングの設定（監視リージョン）

3 つ目のスタックである `BLEAFSI-CoreBanking-monitoring-Dev` の実行が完了すると、Output として下記の 6 つの CLI コマンドが表示される。順に実行する。

| Output | 説明 |
| --- | --- |
| CLIforTGWpeeringacceptancetoprimaryregion | 主リージョンと監視リージョンの TGW をピアリングするための TGW ピアリングの承認を実施する CLI |
| CLIforaddingTGWrouteinprimaryregion | 主リージョンの Transit Gateway のルートテーブルに監視リージョンへのルートを追加する CLI |
| CLIforaddingTGWroutetoprimaryregioninmonitoringregion | 監視リージョンの Transit Gateway のルートテーブルに主リージョンへのルートを追加する CLI |
| CLIforTGWpeeringacceptancetosecondaryregion | 副リージョンと監視リージョンの TGW をピアリングするための TGW ピアリングの承認を実施する CLI |
| CLIforaddingTGWrouteinsecondaryregion | 副リージョンの Transit Gateway のルートテーブルに監視リージョンへのルートを追加する CLI |
| CLIforaddingTGWroutetosecondaryregioninmonitoringregion | 監視リージョンの Transit Gateway のルートテーブルに副リージョンへのルートを追加する CLI |

主リージョンと監視リージョンの承認 → 主リージョンのルート追加 → 監視リージョンのルート追加、続いて副リージョンと監視リージョンの承認 → 副リージョンのルート追加 → 監視リージョンのルート追加、の順に実行する。各承認後は 2-3 分待ってから次のコマンドを実行する。

以上で勘定系ワークロードのデプロイは完了となる。

### 5. (オプション) マルチリージョン マイクロサービスアプリケーションを使用する

2 のマイクロサービス・アプリケーションを利用する場合は追加のセットアップが必要である。同梱の `assets/sample-cdk/sample-multi-region-app/README.md` および `deploy.md` の手順に従って、ECS コンテナアプリケーションおよび Aurora DB のセットアップを行う。アプリケーションの詳細は「[マルチリージョン マイクロサービスアプリケーション](./multi-region-app.md)」を参照。

### 6. (オプション) 動作確認用 NLB にアクセスし ECS サンプルアプリケーションの動作確認を行う

ECS サンプルアプリケーション（PHP ベース）をデプロイすると、インターネットから ECS サンプルアプリへの接続を可能にする動作確認用の NLB がデプロイされる。デプロイ完了後、`Outputs` の `BLEA-FSI-core-banking-nlb-only-for-test.TestNlbUrl` の URL を開くことでサンプルアプリにアクセスできる。

## 関連ドキュメント

- [リファレンスアーキテクチャ詳細 [勘定系]](./architecture.md)
- [マルチリージョン マイクロサービスアプリケーション](./multi-region-app.md)
- [サンプルアプリデプロイ時のエラー対応](./sample-app-workaround.md)
