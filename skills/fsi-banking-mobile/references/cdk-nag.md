# cdk-nag による強制（mobile-banking）

このスキルから実際の CDK を書く下流エンジニアが、自分たちのスタックに対して cdk-nag を確実に
適用・ゲートできるようにするためのガイドである。内容は上流の BLEA for FSI 実装のテストコード
（`usecases/guest-mobile-banking-sample/test/*.test.ts`）から抽出したものであり、抑制理由は上流の
記載を逐語コピーしている（発明していない）。

## 強制の3層

上流のテストは、CDK-bearing な BLEA-FSI ユースケース共通の 3 層パターンで cdk-nag を強制している。
下流エンジニアは自分のスタックで同じ 3 層を再現すること。

### 1. すべてのスタックにパックを適用する（Aspects）

```ts
import { AwsSolutionsChecks } from 'cdk-nag';
cdk.Aspects.of(stack).add(new AwsSolutionsChecks());
```

Aspect が適用されないスタックは一切チェックされない。**すべての** スタックに適用することが第 1 の
強制ポイントである。

### 2. 未抑制の検出で CI を失敗させる（ゲート）

```ts
const errors = Annotations.fromStack(stack).findError('*', Match.stringLikeRegexp('AwsSolutions-.*'));
expect(errors).toHaveLength(0);
```

未抑制の `AwsSolutions-*` エラーが 1 件でもあれば jest テストが失敗し、パイプラインをブロックする。
これが実際の「強制」である。

### 3. reason を明記した場合のみ抑制する（監査規律）

```ts
NagSuppressions.addResourceSuppressionsByPath(stack, '<construct path>', [
  { id: 'AwsSolutions-IAM5', reason: '<なぜ許容できるかの理由>' },
]);
```

例外は削除するのではなく、パスごとに `reason` を付けて記録する。これにより判断が監査可能な状態で
残り（FISC 証跡として重要）、`NagSuppressions.addStackSuppressions` によるスタック全体への抑制も
同様に reason を必須とする。

## 抑制ルール台帳

上流の `guest-mobile-banking-sample` のテストが本ワークロードに対して抑制している
`AwsSolutions-*` ルールの一覧である。抑制件数はテストファイル中の実際の抑制エントリ（`id:` フィールド）
の数を数えたもので、理由は上流の記載を逐語コピーしている。この台帳は「参照実装が reason 付きで
許容可能と判断した検出」と「下流で修正すべき検出」を区別するためのものである。

| ルールID | 抑制件数 | 抑制理由（上流での記載） |
| --- | --- | --- |
| AwsSolutions-IAM4 | 3 | `AWS managed policy for API Gateway CloudWatch Logs access is recommended by AWS.`（CoreApiCloudWatchRole / BankingApiCloudWatchRole に適用） / `It is used only when deploying.`（デプロイ時のみ使用するカスタムリソースの ServiceRole に適用） |
| AwsSolutions-IAM5 | 3 | `CDKが自動生成するDefaultPolicyには、Lambda関数の基本的な実行に必要な最小権限が含まれています。これらの権限はCDKの内部動作によるものであり、セキュリティ上必要な最小権限です。` / `Lambda関数は実行時に動的にログストリームを作成するため、ログストリームレベルでのワイルドカード権限（:*）が必要です。これはAWSの標準的な動作であり、具体的なログストリーム名を事前に知ることはできません。` / `CDKが自動生成するDefaultPolicyには、Lambda関数の基本的な実行に必要な最小権限が含まれています。これらの権限はCDKの内部動作によるものであり、セキュリティ上必要な最小権限です。また、Core Banking APIへのアクセス権限で具体的なAPI IDを指定することを推奨します。本現実装では ``*/v1/*/*`` のワイルドカードを使用していますが、セキュリティ上必要な最小権限です。` |
| AwsSolutions-APIG4 | 1 | `このモバイルバンキングAPIは、エンドユーザーがパブリックにアクセスするWebシステム用に設計されています。認証設計として、すべてのエンドポイントでAPI Key認証を必須とし、個人情報にアクセスする機能（残高照会、振込、取引履歴）については追加でJWT認証を実装しています。パブリックアクセスが必要なエンドポイント（ログイン、ユーザー登録、口座開設申込等）では、API Keyによる基本的なアクセス制御のみを適用し、Cognito User Pool認証は使用していません。` |
| AwsSolutions-COG4 | 1 | `このシステムでは、Cognito User Poolではなく、独自のJWT認証システムを実装しています。個人情報を扱うAPI（/api/balance、/api/transfer、/api/accounts/{id}/transactions）では、カスタムJWT Authorizerを使用してトークン検証を行い、適切な認証・認可を実現しています。パブリックアクセスが必要なAPI（/api/auth/login、/api/users/register、/api/accounts等）では、API Keyによる基本的なアクセス制御を適用し、Cognito User Pool認証は意図的に使用していません。` |
| AwsSolutions-APIG2 | 1 | `このAPIは、リクエストバリデーターを設定済みですが、CDK Nagが検出できない場合があります。API Gatewayでは適切なリクエスト検証が実装されており、各エンドポイントでAPI Key認証とJWT認証による多層防御を実現しています。` |

> 抽出コマンド例（上流のテストディレクトリに対して実行する。コピーされた sample-cdk ではなく上流
> のテストが情報源である）:
>
> ```bash
> # このワークロードのルール -> 出現数
> grep -rhoE "AwsSolutions-[A-Z0-9]+" <testdir> | sort | uniq -c | sort -rn
>
> # ルール + 逐語 reason のペア（重複排除）
> grep -rhoE "id: 'AwsSolutions-[A-Z0-9]+', reason: '[^']*'" <testdir> \
>   | sed -E "s/id: '([^']*)', reason: '([^']*)'/\1\t\2/" | sort -u
> ```
>
> 注：`grep -rhoE "AwsSolutions-[A-Z0-9]+"` は reason 本文やスナップショット内の言及も拾うため
> 件数が多めに出る。実際の抑制件数は `id: 'AwsSolutions-...'` フィールドを数えること
> （上表はこれに基づく）。また複数行にまたがる reason や配列形式のエントリは 2 番目の grep では
> 取り切れないため、必要に応じて手作業で全 reason を確認すること。

## 一般的な抑制理由の分類

BLEA-FSI 全体を通じて、抑制のほとんどは次の 2 分類に収まる。下流エンジニアはこれを手がかりに、
「サンプル固有で流用してよい抑制」と「自分の環境で改めて正当化し直すべき抑制」を区別すること。

- **デプロイ時のみ使うロール / カスタムリソース由来**（IAM4 / IAM5 / L1）：CDK が自動生成する
  DefaultPolicy、`AWS679f53fac002430cb0da5b7982bd2287` のようなカスタムリソースの ServiceRole、
  BucketDeployment 等。デプロイ処理に必要な最小権限であり、ランタイムのアプリ権限ではない。
- **サンプルアプリ由来**（APIG2 / APIG4 / COG4 等）：本サンプル固有の認証設計（独自 JWT + API Key、
  Cognito User Pool を意図的に不使用）や、CDK Nag が検出しきれない実装上の理由による抑制。これらは
  自分のアプリの設計判断に置き換えて再評価すること。

上表の reason をそのまま丸写しして抑制してはならない。自分のスタックで実際にレビューした検出のみを、
自分の言葉の reason を付けて抑制すること。

## テストテンプレート

上記 3 層をそのまま再現できる、資産非依存の cdk-nag テストテンプレートを同梱している。自分のスタック
の import とインスタンス化に差し替えて使用する。

- [`../assets/cdk-nag-test.template.ts`](../assets/cdk-nag-test.template.ts)
