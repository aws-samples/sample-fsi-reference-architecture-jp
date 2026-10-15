# cdk-nag による強制（Open API ワークロード）

本ドキュメントは、このスキルから **実際の CDK を実装する下流のエンジニア** が、自分の Stack に対して
cdk-nag を確実に適用・ゲートするための知識をまとめたものである。ここに記載する抑制ルール台帳は、上流の
BLEA for FSI リファレンス実装のテストコード（`usecases/guest-openapi-base-sample/test/*.test.ts` および
`usecases/guest-openapi-fapi-sample/test/*.test.ts`）から逐語抽出したものであり、**発明ではなく抽出** である。

## 強制の 3 層

上流の CDK 付き BLEA for FSI ユースケースは、いずれも以下の 3 層で cdk-nag を強制している。下流でも
同じパターンを自分の Stack 上で再現すること。

### 1. すべての Stack に AwsSolutions パックを適用する（Aspects）

```ts
import { AwsSolutionsChecks } from 'cdk-nag';
cdk.Aspects.of(stack).add(new AwsSolutionsChecks());
```

Aspect が適用されない Stack はそもそも検査されない。**すべての Stack** に適用することが第 1 の強制点である。

### 2. 未抑制の検出があれば CI を失敗させる（ゲート）

```ts
const errors = Annotations.fromStack(stack).findError('*', Match.stringLikeRegexp('AwsSolutions-.*'));
expect(errors).toHaveLength(0);
```

未抑制の `AwsSolutions-*` エラーが 1 件でもあれば jest テストが失敗し、パイプラインをブロックする。これが
実質的な「強制」である。

### 3. reason を明記した場合のみ抑制する（監査規律）

```ts
NagSuppressions.addResourceSuppressionsByPath(stack, '<construct path>', [
  { id: 'AwsSolutions-IAM5', reason: '<なぜ許容できるのか>' },
]);
```

例外は削除するのではなく、パスごとに `reason` を付けて記録する。これにより判断が監査可能な状態で残り、
FISC の証跡として重要になる。上流では base 側が `addResourceSuppressionsByPath`（リソースパス単位）、
FAPI 側が `addStackSuppressions`（Stack 全体・`applyToChildren=true`）を用いている。

## 抑制ルール台帳

上流のテストが抑制している `AwsSolutions-*` ルールの一覧。reason は上流での記載を逐語コピーしたものである。
下流エンジニアは、この台帳を「リファレンス実装が理由付きで許容した検出」対「修正が必要な検出」を区別する
手がかりとして用いること。**自分の Stack で実際にレビューしていない検出を一括コピーで抑制してはならない。**

### base: `guest-openapi-base-sample`（リソースパス単位の抑制）

| ルールID | 抑制件数 | 抑制理由（上流での記載） |
| --- | --- | --- |
| AwsSolutions-IAM4 | 2 | `It is used only when deploying.` / `It is a sample build project.` |
| AwsSolutions-IAM5 | 1 | `It is used only when deploying.` |
| AwsSolutions-COG2 | 1 | `It is a sample build project.` |
| AwsSolutions-COG3 | 1 | `It is a sample build project.` |
| AwsSolutions-APIG2 | 1 | `It is a sample build project.` |
| AwsSolutions-APIG3 | 1 | `cdk-nag tool bug.` |
| AwsSolutions-S1 | 1 | `It is a log bucket.` |

### FAPI: `guest-openapi-fapi-sample`（Stack 全体の抑制）

| ルールID | 抑制件数 | 抑制理由（上流での記載） |
| --- | --- | --- |
| AwsSolutions-S1 | 2 | `OK. Not to use an additional S3 bucket for S3 Access Logs. because simplification to this sample.` |
| AwsSolutions-RDS6 | 1 | `OK. Not to use IAM Database Authentication, because performance aspects.` |
| AwsSolutions-RDS11 | 1 | `CAN NOT Avoid. Aurora serverless v1 cannot change the default port 3306.` |
| AwsSolutions-SMG4 | 1 | `OK. does not need secrets rotations because It's needs additional Lambda functions.` |
| AwsSolutions-IAM4 | 1 | `OK to use AWS automated generation policies.` |
| AwsSolutions-IAM5 | 1 | `OK to use AWS automated generation policies.` |
| AwsSolutions-ECS2 | 1 | `Not secrets value, just a environment values.` |
| AwsSolutions-EC23 | 1 | `OK. Security group is open to internet for its responsibility` |
| AwsSolutions-ELB2 | 1 | `OK. NLB does not write any access log under TCP listner configuration.` |

> 補足: FAPI 側の `addStackSuppressions` には、上記に加えて `AwsSolutions-*` ではない
> `CdkNagValidationFailure`（reason: `suppress warnings.`）が 1 件含まれる。これは AwsSolutions パックの
> 検出ではなく cdk-nag の検証失敗の抑制であるため、本台帳（`AwsSolutions-*` ルール）からは除外している。
> また `AwsSolutions-S1` は上流テスト内で同一 reason のエントリが 2 回記載されている（重複）。

## 一般的な抑制理由の分類

BLEA for FSI 全体を通じて、抑制のほとんどは次の 2 カテゴリに分類できる。下流エンジニアは、
サンプル固有の抑制と、自分の環境で改めて正当化が必要な抑制とを区別すること。

- **デプロイ時のみ使うロール / カスタムリソース由来**（IAM4 / IAM5 / L1 など）: 例として本ワークロードの
  `It is used only when deploying.`、`OK to use AWS automated generation policies.` が該当する。
  デプロイ時にのみ用いられる自動生成ロールやマネージドポリシーに対する抑制であり、本番アプリの権限とは
  区別される。
- **サンプルアプリ由来**（`It is a sample build project.` など）: サンプルとしての簡略化に起因する抑制で
  （例: base の COG2/COG3/APIG2、FAPI の S1 の「アクセスログ用 S3 を追加しない」）、本番実装では
  そのまま流用せず、自分のセキュリティ要件に照らして再評価する必要がある。

その他、`cdk-nag tool bug.`（ツール側の不具合に対する暫定抑制）や、`CAN NOT Avoid. ...`（サービスの制約上
回避できないもの）のように、上流の判断根拠が個別に明記されているケースもある。いずれも自分の Stack では
検出内容を実際にレビューした上で、必要な reason を明記して抑制すること。

## テストテンプレート

上記 3 層をそのまま再現できる、資産非依存のテストテンプレートを同梱している。自分の CDK プロジェクトの
`test/` にコピーし、プレースホルダの import と Stack 生成を自分の Stack に置き換えて利用すること。

- [../assets/cdk-nag-test.template.ts](../assets/cdk-nag-test.template.ts)
