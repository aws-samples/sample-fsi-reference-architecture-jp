# cdk-nag 強制（マーケットデータ ワークロード）

本スキルから **実際の CDK を書く下流エンジニア** が、自分たちの Stack で cdk-nag を必ず実行し、
CI をそれでゲートできるようにするための知識である。ここに示すルールと抑制台帳は、上流の BLEA for FSI
リファレンス実装のテストコード（`usecases/guest-market-data-sample/test/*.test.ts`）から抽出したもので
あり、発明ではない。

> 注意: 本スキルに同梱される `assets/sample-cdk/.../test/*.test.ts`（上流サンプル）は既に上流で nag
> 検証済みである。ここで説明する強制の目的は **下流** にある。本番 CDK を書く担当者が、自分たちの
> Stack に対して cdk-nag を強制できるようにすることである。

## 強制の3層

上流のマーケットデータ usecase は、次の 3 層で cdk-nag を強制している。下流エンジニアは自分たちの
Stack に対して同じパターンを再現すること。

### 1. すべての Stack にパックを適用する（Aspects）

```ts
import { AwsSolutionsChecks } from 'cdk-nag';
cdk.Aspects.of(stack).add(new AwsSolutionsChecks());
```

Aspect が適用されない Stack は一切チェックされない。**すべての Stack** に適用することが、第一の強制点で
ある。

### 2. 未抑制の検出が 1 件でもあれば CI を失敗させる（ゲート）

```ts
const errors = Annotations.fromStack(stack).findError('*', Match.stringLikeRegexp('AwsSolutions-.*'));
expect(errors).toHaveLength(0);
```

未抑制の `AwsSolutions-*` エラーが 1 件でもあれば jest テストが失敗し、パイプラインをブロックする。これ
が実際の「強制」である。

### 3. 抑制は必ず reason を明記して行う（監査規律）

```ts
NagSuppressions.addResourceSuppressionsByPath(stack, '<construct path>', [
  { id: 'AwsSolutions-IAM5', reason: '<なぜ許容できるか>' },
]);
```

例外は削除せず、パスごとに `reason` を付けて記録する。これにより判断が監査可能な状態で残る（FISC の
証跡として重要である）。

## 抑制ルール台帳

上流のマーケットデータ usecase のテストが **この資産に対して** 抑制している `AwsSolutions-*` ルール、
その抑制件数、および上流での記載どおりの reason（逐語コピー）を以下に示す。この台帳は、リファレンス
実装が「reason 付きで許容した」検出はどれか、逆に下流で修正が必要な検出はどれかを判断する材料になる。

| ルールID | 抑制件数 | 抑制理由（上流での記載） |
| --- | --- | --- |
| AwsSolutions-IAM5 | 10 | `It is used only when deploying.` / `App can read,write variety of streams` / `Target repo are narrowed to Specified account and region` / `Policies are managed by L2 construct and target resources are properly controlled` / `Policies are managed by L2 construct and resouce target is only to log` / `Target stream are properly narrowed` / `Default policy is managed by aws_codebuild construct and only used for build image` |
| AwsSolutions-L1 | 2 | `It is used only when deploying.` / `This lambda is managed by aws_codebuild and only used for deploy image` |
| AwsSolutions-IAM4 | 1 | `This role is managed by custom_resources and only used for build` |
| AwsSolutions-EC23 | 1 | `This is for just sample app` |
| AwsSolutions-S1 | 1 | `This is an access log bucket` |

> 抽出方法（上流テストディレクトリに対して実行。同梱サンプルではなく上流ソースに対して行う）:
>
> ```bash
> # ルール -> 件数
> grep -rhoE "AwsSolutions-[A-Z0-9]+" <testdir> | sort | uniq -c | sort -rn
>
> # ルール + reason（重複除去）
> grep -rhoE "id: 'AwsSolutions-[A-Z0-9]+', reason: '[^']*'" <testdir> \
>   | sed -E "s/id: '([^']*)', reason: '([^']*)'/\1\t\2/" | sort -u
> ```

## 一般的な抑制理由の分類

BLEA for FSI 全体で見ると、抑制の大半は次のいずれかに分類できる。下流エンジニアは、サンプル固有の
抑制と、自分たちの Stack で改めて正当化すべき抑制とを区別すること。

- **デプロイ時のみ使うロール / カスタムリソース由来（IAM4 / IAM5 / L1）** — CDK が生成するデプロイ用の
  ロールやカスタムリソース（CodeBuild / custom_resources 等）に対するもの。上記台帳の
  `It is used only when deploying.` / `This role is managed by custom_resources and only used for build`
  / `This lambda is managed by aws_codebuild and only used for deploy image` /
  `Default policy is managed by aws_codebuild construct and only used for build image` などが該当する。
- **サンプルアプリ由来** — 参照実装のサンプルアプリであることを理由とする抑制。上記台帳の
  `This is for just sample app`（EC23）や、アクセスログ用バケットである旨の `This is an access log bucket`
  （S1）などが該当する。

これらはあくまで **リファレンス実装** が許容した抑制である。下流の本番 Stack では、同じ検出が出た場合に
それを無条件でコピーせず、自分たちの構成に照らして再度レビューし、reason を書き直すこと。

## テストテンプレート

上記 3 層をそのまま再現できる、資産非依存の jest テストテンプレートを同梱している。自分の Stack の
import と生成に置き換えて使用すること。

- [../assets/cdk-nag-test.template.ts](../assets/cdk-nag-test.template.ts)
