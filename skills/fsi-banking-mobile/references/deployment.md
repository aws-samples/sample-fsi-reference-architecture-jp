# [モバイルバンキング] ワークロード サンプルコードのデプロイ手順

サンプルコードは `assets/sample-cdk/` に含まれる。以下はゲストアカウントにデプロイする手順である。

> **作業ディレクトリについて**: 本スキルは読み取り専用のテンプレート提供元である。SKILL.md や
> references 等の CDK 実行に不要なファイルはコピーせず、**CDK 実行に必要な次の 2 つだけ**を、
> 相対参照（`assets/sample-cdk/tsconfig.json` の `extends: "../../tsconfig.base.json"`）が保たれる
> 形で作業ディレクトリ `<workdir>` にコピーする:
>
> - `assets/sample-cdk/` → `<workdir>/assets/sample-cdk/`
> - `tsconfig.base.json` → `<workdir>/tsconfig.base.json`
>
> **コピー先 `<workdir>` は、スキル利用者に次の 3 択で確認すること**: (1) カレントディレクトリ、
> (2) スキル名のディレクトリ（例 `fsi-banking-mobile-cdk/`）を新規作成、(3) 利用者が指定するディレクトリ。
> コピー後 `<workdir>/assets/sample-cdk` に移動して CDK コマンドを実行する（以下の `cd assets/sample-cdk`
> はこの移動を指す）。**フロントエンドは `lib/frontend` で `npm install && npm run build` を実行して
> `build/` を生成してからデプロイすること**（生成しないと `cdk synth`/`deploy` が `CannotFindAsset` で失敗する）。
> アカウント・リージョンは `bin/parameter.ts` に直接書かず、環境変数 `CDK_DEFAULT_ACCOUNT` / `AWS_REGION`
>（または `--profile`）で与える。

## 導入手順

### 1. ゲストアカウントデプロイ用の AWS CLI プロファイルを設定する

ゲストアカウントにデプロイするための AWS CLI プロファイルを設定する。ここではゲストアカウントの ID を 123456789012 としている。`~/.aws/config`：

```sh
# for Guest Account Login
[profile ct-guest-sso]
sso_start_url = https://d-90xxxxxxxx.awsapps.com/start/
sso_region = ap-northeast-1
sso_account_id = 123456789012
sso_role_name = AWSAdministratorAccess
region = ap-northeast-1
```

### 2. プロジェクトディレクトリに移動

```sh
cd assets/sample-cdk
```

（本スキルでは `assets/sample-cdk/` がこのディレクトリに相当する。）

### 3. 依存関係のインストールとビルド

```sh
npm install
```

```sh
npm run build
```

### 4. モバイルバンキングワークロードをデプロイする

（ログインしていない場合）AWS IAM Identity Center（旧 AWS SSO）を使ってゲストアカウントにログインする。

```sh
aws sso login --profile ct-guest-sso
```

ゲストアカウントで CDK ブートストラップを実行する。

```sh
npm run bootstrap
```

### 5. デプロイ方法の選択

モバイルバンキングワークロードには三つの CDK Stack が存在する。

- `CoreBankingSystemStack`: コアバンキングシステム（口座管理、取引処理、顧客管理）
- `OnlineBankingAppBackendStack`: オンラインバンキングアプリのバックエンド（認証、セッション管理、CoreBankingSystem との連携）
- `OnlineBankingAppFrontendStack`: Web アプリケーションフロントエンド

以下のコマンドで全てデプロイされる。

```sh
npm run deploy
```

必要に応じて、個別のスタックのみをデプロイすることも可能である：

```sh
# バックエンドのみデプロイ
npx cdk deploy OnlineBankingAppBackendStack

# フロントエンドのみデプロイ
npx cdk deploy OnlineBankingAppFrontendStack

# コアシステムのみデプロイ
npx cdk deploy TemporarCoreBankingSystemStack
```

デプロイオプションは `bin/app.ts` で環境変数により制御されている：

```js
// デプロイオプション設定
const deployOptions = {
  // コアバンキングシステムをデプロイするかどうか
  // 既存の基幹系システムがある場合は false に設定
  deployCoreSystem: process.env.DEPLOY_CORE_SYSTEM !== 'false', // デフォルトはtrue（サンプル用）

  // オンラインバンキングアプリのバックエンドをデプロイするかどうか
  deployBackend: process.env.DEPLOY_BACKEND !== 'false', // デフォルトはtrue

  // オンラインバンキングアプリのフロントエンドをデプロイするかどうか
  deployFrontend: process.env.DEPLOY_FRONTEND !== 'false', // デフォルトはtrue
};
```

環境変数を使用して、デプロイするスタックを制御できる：

```sh
# バックエンドのみデプロイ
DEPLOY_FRONTEND=false
DEPLOY_CORE_SYSTEM=false
npm run deploy

# フロントエンドのみデプロイ
DEPLOY_BACKEND=false
DEPLOY_CORE_SYSTEM=false
npm run deploy

# コアバンキングシステム + バックエンドのみデプロイ
DEPLOY_FRONTEND=false
npm run deploy
```

コアバンキングシステム + バックエンドのみデプロイした場合、`lib/frontend/public/config.json` に、OutPuts の `OnlineBankingAppBackendStack.CoreApiBaseUrl` の値を設定する。以下のコマンドでローカルでフロントエンドを実行することができる。

```sh
cd lib/frontend
npm start
```

### 6. フロントエンドアプリケーションの確認

デプロイ完了後、CloudFront の URL からフロントエンドアプリケーションにアクセスできる：

1. AWS マネジメントコンソールで CloudFront サービスを開く
2. 作成されたディストリビューションのドメイン名を確認
3. ブラウザでアクセスしてアプリケーションの動作を確認（利用手順は `architecture.md` の「アプリケーション利用手順」を参照）

## 環境変数の優先順位

コアバンキングシステムのエンドポイントは以下の優先順位で決定される：

1. **temporary-core-banking-system のエンドポイント**（デプロイされた場合）
2. **環境変数 `CORE_API_BASE_URL`**（本番環境での上書き用）

## 削除手順

サンプルアプリケーションを削除する場合：

```bash
npm run destroy
```

注意：DynamoDB テーブルなど、削除保護が有効なリソースは手動で削除する必要がある場合がある。
