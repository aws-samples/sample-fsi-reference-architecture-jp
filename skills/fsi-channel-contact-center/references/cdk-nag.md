# cdk-nag による強制（Customer Channel）

本ドキュメントは、このスキルから構築する CDK Stack に対して **cdk-nag** をどう強制するかを、
下流のエンジニアが自分の Stack で再現できるように説明する。内容は BLEA for FSI の上流実装
（`usecases/guest-customer-channel-sample/test/bleafsi-guest-customer-channel-sample.test.ts`）
のテストコードから抽出したものであり、この資産固有の事実に基づく。

## 強制の3層

上流の CDK 資産は、cdk-nag を次の3層のパターンで強制している。下流エンジニアも同じ3層を自分の
Stack に適用すること。

### 1. Aspects で全 Stack に AwsSolutions パックを適用する

```ts
import { AwsSolutionsChecks } from 'cdk-nag';
cdk.Aspects.of(app).add(new AwsSolutionsChecks());
```

上流テストでは、`primary` / `secondary` / `tertiary` の各 Stack を `describe.each` で列挙し、
`cdk.App` に `AwsSolutionsChecks` を Aspect として適用している。Aspect が適用されていない Stack は
一切チェックされないため、**作成した全ての Stack に適用する**ことが最初の強制点である。

### 2. `expect(errors).toHaveLength(0)` を CI ゲートにする

```ts
const errors = Annotations.fromStack(stack).findError('*', Match.stringLikeRegexp('AwsSolutions-.*'));
expect(errors).toHaveLength(0);
```

未抑制の `AwsSolutions-*` エラーが 1 件でもあれば jest テストが失敗し、パイプラインをブロックする。
これが実際の「強制」に相当する。上流テストは検出内容を握りつぶさず、失敗時に
`console.error(JSON.stringify(errors, ...))` で検出結果を出力し、CI 失敗を actionable にしている。

### 3. 例外は reason を明記した NagSuppressions でのみ抑制する

```ts
NagSuppressions.addResourceSuppressionsByPath(stack, '<construct path>', [
  { id: 'AwsSolutions-IAM5', reason: '<なぜ許容できるかの説明>' },
]);
```

抑制は削除ではなく、パス単位で `reason` 付きに記録する。これにより判断が監査可能なまま残り、
FISC の証跡として重要である。**ただし、この資産の上流テストは NagSuppressions を1件も使っていない
（下記の台帳を参照）。**

## 抑制ルール台帳

この資産は **抑制ゼロ（NagSuppressions 未使用でパス）** である。すなわち、上流の CDK 実装は
`NagSuppressions` を 1 件も使わずに cdk-nag（AwsSolutions パック）をパスしている。

| ルールID | 抑制件数 | 抑制理由（上流での記載） |
| --- | --- | --- |
| （なし） | 0 | 抑制なし（NagSuppressions 未使用でパス） |

これはポジティブな事実である。この実装は NagSuppressions を1件も使わずに cdk-nag をパスしている
（抑制ゼロ）。下流エンジニアは、この資産をベースにする限り「reference 実装が許容した抑制」を
引き継ぐ必要がない。自分の Stack で新たに検出が出た場合のみ、レビューのうえで reason を明記して
抑制すること。

> 参考（一般論）: 他の BLEA-FSI 資産では、deploy 時のみ使うロールやカスタムリソース由来の検出
> （`AwsSolutions-IAM4` / `AwsSolutions-IAM5` / `AwsSolutions-L1` など）や、サンプルアプリ由来の
> 検出に対して reason 付きの抑制を行うのが一般的である。ただし、**この資産のソース（上流テスト）に
> はそのような抑制は一切含まれていない**。したがって、他資産で見られる抑制をこの資産にそのまま
> 持ち込まないこと。

## テストテンプレート

下流の CDK プロジェクトにそのままコピーして使える、資産非依存の cdk-nag 強制テストテンプレートを
用意している。自分の Stack の import と生成に置き換えて使用すること。

- [../assets/cdk-nag-test.template.ts](../assets/cdk-nag-test.template.ts)
