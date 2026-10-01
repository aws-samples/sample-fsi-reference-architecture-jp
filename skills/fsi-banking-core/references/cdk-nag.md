# cdk-nag による強制（Core Banking / 勘定系）

本ドキュメントは、このスキルから **実際の CDK を実装する下流エンジニア** が cdk-nag を
必ず実行し、その結果を CI でゲートするための知識をまとめたものである。強制パターンと抑制
ルール台帳は、上流の BLEA for FSI リファレンス実装のテストコード
（`assets/sample-cdk/test/*.test.ts`）から抽出しており、内容は
そこからの逐語的な引き写しである（発明はしていない）。

コピーして使えるテスト雛形は `../assets/cdk-nag-test.template.ts` にある。自分の Stack の
import とインスタンス化に置き換えて使うこと。

## 強制の 3 層

上流のすべての CDK 保有ユースケースは、同一の 3 層パターンで cdk-nag を強制している。
下流エンジニアは、自分が書く Stack でこれをそのまま再現すること。

### 1. 全 Stack に AwsSolutions パックを適用する（Aspects）

```ts
import * as cdk from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';

cdk.Aspects.of(stack).add(new AwsSolutionsChecks());
```

Aspect が適用されない Stack は一切検査されない。**すべての Stack** に適用することが第 1 の
強制ポイントである。

### 2. 未抑制の検出が 1 件でもあれば CI を失敗させる（ゲート）

```ts
import { Annotations, Match } from 'aws-cdk-lib/assertions';

const errors = Annotations.fromStack(stack).findError('*', Match.stringLikeRegexp('AwsSolutions-.*'));
expect(errors).toHaveLength(0);
```

未抑制の `AwsSolutions-*` エラーが 1 件でもあれば jest テストが失敗し、パイプラインをブロック
する。これが実際の「強制」の中核である。

### 3. 抑制は必ず reason を書いて行う（監査規律）

```ts
import { NagSuppressions } from 'cdk-nag';

NagSuppressions.addResourceSuppressionsByPath(stack, '<construct path>', [
  { id: 'AwsSolutions-IAM5', reason: '<なぜ許容できるのか>' },
]);
```

例外は削除するのではなく、パスごとに `reason` を付けて記録する。これにより判断が監査可能な
まま残る（FISC の証跡として重要）。

## 抑制ルール台帳（上流 test が抑制しているルール）

上流の勘定系サンプルテストが抑制している `AwsSolutions-*` ルールの一覧。抑制件数は
`grep -rhoE "AwsSolutions-[A-Z0-9]+" <testdir> | sort | uniq -c | sort -rn` で、理由は
`grep -rhoE "id: 'AwsSolutions-[A-Z0-9]+', reason: '[^']*'" <testdir>` で抽出した（複数行
記述の SMG4 のみ手動で確認）。理由は上流での記載を **逐語コピー**（原文英語、タイポも含む）。
同一ルールで理由が複数ある場合は代表例を列挙する。

| ルールID | 抑制件数 | 抑制理由（上流での記載） |
| --- | --- | --- |
| AwsSolutions-IAM5 | 84 | `It is used only when deploying.` / `Target repo are narrowed to specified account and region.` / `This resource is a sample application.` |
| AwsSolutions-ECS2 | 30 | `Not secrets value, just a environment values.` / `This resource is a sample application.` |
| AwsSolutions-IAM4 | 20 | `It is used only when deploying.` / `This is service role and used by AWS Backup` / `This resource is a sample application.` |
| AwsSolutions-S1 | 6 | `It is a log bucket.` / `This resource is a sample application.` |
| AwsSolutions-L1 | 5 | `It is used only when deploying.` / `This resource is a sample application.` |
| AwsSolutions-EC23 | 4 | `It is configured when using.` / `This resource is a sample application.` |
| AwsSolutions-ELB2 | 3 | `This resource is a sample application.` / `this stack is used for checking the operation` |
| AwsSolutions-SNS2 | 2 | `SNS encryption is an option.` |
| AwsSolutions-SMG4 | 2 | `for convenience of sample application. key rotataion is not enabled` |
| AwsSolutions-RDS6 | 2 | `It is not used for performance considerations.` |
| AwsSolutions-RDS10 | 2 | `This sample must be easy to remove.` |
| AwsSolutions-EC29 | 1 | `This resource is a sample application.` |
| AwsSolutions-EC28 | 1 | `This resource is a sample application.` |
| AwsSolutions-CB4 | 1 | `It is a sample build project.` |

この台帳は、リファレンス実装が「理由付きで許容した」検出と「修正すべき」検出を下流エンジニアが
見分けるためのものである。**下流では台帳をそのまま丸ごとコピーしてはならない**。自分の Stack で
実際にレビューした検出のみ、reason を付けて抑制すること。

## 一般的な抑制理由の分類

BLEA for FSI 全体で見ても、抑制の大半は次の 2 分類に収まる。下流エンジニアは、サンプル固有の
抑制と、自分で改めて正当化しなければならない抑制とを区別すること。

- **deploy 時のみ使うロール / カスタムリソース**（`AwsSolutions-IAM4` / `AwsSolutions-IAM5` /
  `AwsSolutions-L1`）— CDK のデプロイ時にのみ利用されるサービスロールやカスタムリソースに起因
  するもの（例: `It is used only when deploying.`）。本番ワークロード自体の権限ではないため、
  上流では理由付きで許容している。
- **サンプルアプリ由来**（`This resource is a sample application.` など）— 同梱のサンプル
  アプリケーションやサンプルビルドプロジェクトに由来するもの。本番実装では該当しないか、
  自前で対策すべき対象である。

これらはあくまでサンプルの都合による抑制であり、本番実装では原則として検出を修正するか、
自組織の判断根拠に基づいた reason へ書き換えること。

## 参照

- コピーして使うテスト雛形: `../assets/cdk-nag-test.template.ts`
- 上流の抑制の一次情報: `../assets/sample-cdk/test/*.test.ts`
