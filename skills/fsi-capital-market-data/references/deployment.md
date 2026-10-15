# マーケットデータ サンプルアプリケーションのデプロイ手順

本ドキュメントは、BLEA for FSI のガバナンスベースがデプロイされたアカウントに [マーケットデータ] サンプルアプリケーションを導入する手順を記述する。出典は BLEA for FSI のデプロイ手順書である。

> **作業ディレクトリについて**: 本スキルは読み取り専用のテンプレート提供元である。SKILL.md や
> references 等の CDK 実行に不要なファイルはコピーせず、**CDK 実行に必要な次の 3 つだけ**を、相対参照
>（`tsconfig.json` の `extends: "../../tsconfig.base.json"`、`package.json` の
> `file:"../../resources/bleafsi-shared-constructs/v1.0.0"`）が保たれる形で作業ディレクトリ `<workdir>` に
> コピーする:
>
> - `assets/sample-cdk/` → `<workdir>/assets/sample-cdk/`
> - `tsconfig.base.json` → `<workdir>/tsconfig.base.json`
> - `resources/` → `<workdir>/resources/`（共有ライブラリ bleafsi-shared-constructs）
>
> **コピー先 `<workdir>` は、スキル利用者に次の 3 択で確認すること**: (1) カレントディレクトリ、
> (2) スキル名のディレクトリ（例 `fsi-capital-market-data-cdk/`）を新規作成、(3) 利用者が指定するディレクトリ。
> コピー後 `<workdir>/assets/sample-cdk` に移動して CDK コマンドを実行する（以下の `cd assets/sample-cdk`
> はこの移動を指す）。**共有ライブラリに依存するため、初回は `<workdir>/resources/bleafsi-shared-constructs/v1.0.0`
> で `npm install && npm run build` を実行してからデプロイすること。** スキルディレクトリ内で直接 `cdk deploy`
> しないこと（生成物でスキルが汚れる）。アカウント・リージョンは `bin/parameter.ts` に直接書かず、環境変数
> `CDK_DEFAULT_ACCOUNT` / `AWS_REGION`（または `--profile`）で与える。

> `MC` はマネジメントコンソールでの作業を、`Local` は手元環境での作業を示す。

CDK サンプル一式は本スキルの `assets/sample-cdk/` に含まれる。以下の手順内でのパス（`assets/sample-cdk/` 配下）は元リポジトリでのパスであり、本スキルでは `assets/sample-cdk/` に対応する。

## 導入手順

### 1. [マーケットデータ] サンプルアプリケーションをデプロイする（Local）

ゲストアカウントに SSO で認証している状態からのデプロイメントの手順を示す。

#### 1-1. ゲストアカウントデプロイ用の AWS CLI プロファイルを設定する

ゲストアカウントにデプロイするための AWS CLI プロファイルを設定する。ここではゲストアカウントの ID を 123456789012 としている。

`~/.aws/config`

```sh
# for Guest Account Login
[profile ct-guest-sso]
sso_start_url = https://d-90xxxxxxxx.awsapps.com/start/
sso_region = ap-northeast-1
sso_account_id = 123456789012
sso_role_name = AWSAdministratorAccess
region = ap-northeast-1
```

#### 1-2. 環境別の設定を指定する

デプロイ前に環境別（開発、ステージング、本番等）の情報を指定する必要がある。下記の TypeScript ファイルを編集する。

```sh
assets/sample-cdk/bin/parameter.ts
```

このサンプルは dev と staging という開発、検証用の設定を定義する例である。本番アカウントにもデプロイできるようにするには、prod 用の定義を追加する。

```js
export const DevParameter: StackParameter = {
  envName: 'Development',
  securityNotifyEmail: 'notify-security@example.com',
  vpcCidr: '10.100.0.0/16',
  env: {
    region: process.env.CDK_DEFAULT_REGION,
  },
};

//// Staging environment parameters ////
export const StageParameter: StackParameter = {
  envName: 'Staging',
  env: {
    account: '111111111111',
    region: 'ap-northeast-1',
  },
  securityNotifyEmail: 'notify-security@example.com',
  vpcCidr: '10.100.0.0/16',
};
```

この設定内容は以下の通りである。

| key                 | value                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------- |
| env.account         | デプロイ対象のアカウント ID。CLI の profile で指定するアカウントと一致している必要がある      |
| env.region          | デプロイ対象のリージョン                                                                     |
| envName             | 環境名。これが各々のリソースタグに設定される                                                 |
| vpcCidr             | VPC の CIDR                                                                                   |
| securityNotifyEmail | セキュリティに関する通知が送られるメールアドレス。                                           |

#### 1-3. ゲストアプリケーションをデプロイする

（ログインしていない場合）AWS IAM Identity Center（旧 AWS SSO）を使ってゲストアカウントにログインする。

```sh
aws sso login --profile ct-guest-sso
```

サンプルアプリケーションをデプロイする。

```sh
cd assets/sample-cdk
npx cdk deploy BLEAFSI-MarketData-Dev --profile ct-guest-sso
```

> `BLEAFSI-MarketData-Dev` はデプロイ対象の開発環境用のスタック名である。環境（開発、ステージング、本番）によってスタック名は異なる。

以上でサンプルアプリケーションのデプロイは完了である。

#### 1-4. （参考）AWS CloudTrail で Kinesis Data Streams API コールを記録する

CloudTrail は、Kinesis Data Streams のすべての API コールをイベントとしてキャプチャする。
サポートされているイベントアクティビティは他の AWS サービスのイベントと一緒にマネジメントコンソールのイベント履歴から参照できる。
また、証跡を作成することでイベントを Amazon S3 バケットへ配信し、継続的に記録できる。
これらによって、Kinesis Data Streams に行われたリクエスト、リクエストが行われた IP アドレス、誰がリクエストを行ったか、いつ行われたか、その他の詳細を確認できる。

詳細は以下を参照。
[AWS CloudTrail を使用した Amazon Kinesis Data Streams API コールのログ記録](https://docs.aws.amazon.com/ja_jp/streams/latest/dev/logging-using-cloudtrail.html)
