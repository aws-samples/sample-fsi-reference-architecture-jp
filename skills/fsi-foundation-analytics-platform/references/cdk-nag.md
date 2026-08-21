# cdk-nag 強制

本スキルから構築する実運用 CDK には、cdk-nag（`AwsSolutionsChecks`）による静的検査を必ず適用する。
これは BLEA for FSI 上流の各ワークロードが `usecases/<usecase>/test/*.test.ts` で実装している強制パターン
を、下流エンジニアが自分の Stack に対して再現するためのものである。本資産の上流テスト
（`assets/sample-cdk/test/bleafsi-guest-simple-datalake.test.ts`）が権威的な出典である。

## 強制の 3 層

上流テストは以下の 3 層で cdk-nag を強制している。下流エンジニアは自分の Stack に対して同じ 3 層を再現すること。

1. **全ての Stack に Aspects でパックを適用する。**

   ```ts
   import { AwsSolutionsChecks } from 'cdk-nag';
   cdk.Aspects.of(stack).add(new AwsSolutionsChecks());
   ```

   Aspect を適用しない Stack は一切検査されない。全ての Stack に適用することが第 1 の強制点である。

2. **未抑制の検出があれば CI を失敗させる（ゲート）。**

   ```ts
   const errors = Annotations.fromStack(stack).findError('*', Match.stringLikeRegexp('AwsSolutions-.*'));
   expect(errors).toHaveLength(0);
   ```

   未抑制の `AwsSolutions-*` エラーが 1 件でもあれば jest テストが失敗し、パイプラインをブロックする。
   これが実際の「強制」である。

3. **抑制は必ず reason を書いて行う（監査規律）。**

   ```ts
   NagSuppressions.addResourceSuppressionsByPath(stack, '<construct path>', [
     { id: 'AwsSolutions-IAM5', reason: '<なぜ許容できるのか>' },
   ]);
   ```

   例外は削除するのではなく、パスごとに `reason` を付けて記録する。これにより判断が監査可能なまま残り、
   FISC のエビデンスとして重要となる。

## 抑制ルール台帳

上流テストが本資産に対して抑制している全ての `AwsSolutions-*` ルールを以下に示す。`抑制理由` は上流での記載
を逐語コピーしている（英語原文のまま）。これは、リファレンス実装が「理由付きで許容した」検出と、下流で
「修正すべき」検出とを区別するための一覧である。下流ではこれらを鵜呑みにコピーせず、自分の Stack に対して
実際にレビューした検出のみを抑制すること。

| ルールID | 抑制件数 | 抑制理由（上流での記載） |
| --- | --- | --- |
| AwsSolutions-S1 | 8 | Target bucket is an access log bucket |
| AwsSolutions-IAM5 | 2 | Wild card permission is neccessary |
| AwsSolutions-IAM5 | 1 | this IAM policies are used to get all the data from bucket |
| AwsSolutions-IAM4 | 1 | this stack is used for administrative task. this role uses service-linked role |
| AwsSolutions-IAM4 | 1 | Valid use of AWSQuickSightAthenaPolicy |
| AwsSolutions-SNS2 | 1 | SNS encryption is an option |
| AwsSolutions-SF2 | 1 | X-ray is an option |
| AwsSolutions-L1 | 1 | SNS encryption is an option |

抽出は上流テストディレクトリ（コピーしたサンプルではなく上流）に対して以下のコマンドで再現できる。

```bash
# ルール -> 件数
grep -rhoE "AwsSolutions-[A-Z0-9]+" <testdir> | sort | uniq -c | sort -rn

# ルール + 逐語 reason のペア（重複排除）
grep -rhoE "id: 'AwsSolutions-[A-Z0-9]+', reason: '[^']*'" <testdir> \
  | sed -E "s/id: '([^']*)', reason: '([^']*)'/\1\t\2/" | sort -u
```

## 一般的な抑制理由の分類

BLEA for FSI 全体で、抑制の大半は次の 2 分類に収まる。下流エンジニアは、サンプル固有の抑制と、自分で
再度正当化しなければならない抑制とを区別すること。

- **deploy 時のみ使うロール／カスタムリソース**（IAM4 / IAM5 / L1）: 管理タスク用ロール、サービスリンクロール、
  CDK の `Custom::CDKBucketDeployment` など、デプロイ時にのみ用いられる要素に対するワイルドカード権限や
  マネージドポリシーの利用。本資産では Glue Job ロール／QuickSight ロール／バケットデプロイのサービスロール
  がこれに該当する（IAM4 / IAM5）。
- **サンプルアプリ由来**: サンプル実装として省略・簡略化している構成に対する検出。本資産では、アクセスログ
  バケット自体のサーバーアクセスログ（S1）、SNS の暗号化（SNS2）、Step Functions の X-Ray（SF2）、
  Lambda ランタイム（L1）などが「オプションである」「アクセスログバケットが対象である」として抑制されている。

これらはリファレンス実装が許容した判断であり、下流の本番 Stack では自分の要件に照らして再評価すること。

## テストテンプレート

上流パターンを資産非依存の汎用形にしたテストテンプレートを同梱している。自分の Stack の import と
インスタンス化を埋め、レビュー済みの抑制のみを `NagSuppressions` に追加して使用する。

- [../assets/cdk-nag-test.template.ts](../assets/cdk-nag-test.template.ts)
