# cdk-nag による強制（ガバナンスベース）

このドキュメントは、本スキルから **実際に本番相当の CDK を書く下流エンジニア** に対し、
cdk-nag（`AwsSolutions` パック）による静的検査を強制するためのものである。内容は上流
BLEA for FSI の `usecases/base-ct-guest/test/*.test.ts` および
`usecases/base-ct-logging/test/*.test.ts` から抽出したものであり、理由等は上流の記載を
逐語コピーしている（発明しない）。

## 強制の 3 層

上流の各ユースケースは、次の 3 層で cdk-nag を一貫して強制している。下流でも自分の Stack に
対して同じパターンを再現すること。

1. **全 Stack に Aspects でパックを適用する。**

   ```ts
   import { AwsSolutionsChecks } from 'cdk-nag';
   cdk.Aspects.of(stack).add(new AwsSolutionsChecks());
   ```

   Aspect が適用されない Stack は一切検査されない。**すべての** Stack に適用することが第 1 の
   強制点である。

2. **未抑制の検出があれば CI を失敗させる（ゲート）。**

   ```ts
   const errors = Annotations.fromStack(stack).findError('*', Match.stringLikeRegexp('AwsSolutions-.*'));
   expect(errors).toHaveLength(0);
   ```

   未抑制の `AwsSolutions-*` エラーが 1 件でもあれば jest テストが失敗し、パイプラインを
   ブロックする。これが実質的な「強制」にあたる。

3. **抑制は必ず reason を書いて記録する（監査規律）。**

   ```ts
   NagSuppressions.addResourceSuppressionsByPath(stack, '<construct path>', [
     { id: 'AwsSolutions-IAM5', reason: '<なぜ許容できるか>' },
   ]);
   ```

   例外は削除するのではなく、パスごとに `reason` 付きで記録する。これにより判断が監査可能な
   まま残る（FISC のエビデンスとして重要）。

## 抑制ルール台帳（上流での抑制内容）

上流テストが本ガバナンスベースで抑制している全 `AwsSolutions-*` ルールを、ユースケース別に
一覧する。`reason` は上流ソースからの逐語コピーである。下流エンジニアは、参照実装が
「reason 付きで許容した」検出はどれで、自分の Stack では改めて正当化・修正すべき検出はどれかを、
この台帳で判別すること。**下流での一括コピーは禁止**であり、自分の Stack で実際にレビューした
検出のみを抑制すること。

抽出コマンド例（上流テストディレクトリに対して実行）:

```bash
# ルール別の抑制件数
grep -rhoE "AwsSolutions-[A-Z0-9]+" <testdir> | sort | uniq -c | sort -rn

# ルール + reason のペア（重複排除）
grep -rhoE "id: 'AwsSolutions-[A-Z0-9]+', reason: '[^']*'" <testdir> \
  | sed -E "s/id: '([^']*)', reason: '([^']*)'/\1\t\2/" | sort -u
```

### base-ct-guest（ゲストアカウント）

| ルールID | 抑制件数 | 抑制理由（上流での記載） |
| --- | --- | --- |
| AwsSolutions-IAM5 | 3 | `this stack is used for administrative task` |
| AwsSolutions-S1 | 2 | `this s3 bucket is used to store server access log itself` |
| AwsSolutions-SNS2 | 1 | `SNS encryption is an option` |
| AwsSolutions-IAM4 | 1 | `this stack is used for administrative task` |

### base-ct-logging（Log Archive アカウント）

| ルールID | 抑制件数 | 抑制理由（上流での記載） |
| --- | --- | --- |
| AwsSolutions-S1 | 1 | `this s3 bucket is used to store server access log itself` |

## 一般的な抑制理由の分類

BLEA for FSI 全体で見ると、抑制のほとんどは次のいずれかに分類できる。下流エンジニアは、
これを手掛かりに「サンプル/管理タスク固有ゆえに許容された抑制」と「自分の Stack では改めて
正当化が必要な抑制」を区別すること。

- **デプロイ時のみ使うロール/カスタムリソース由来**（`AwsSolutions-IAM4` / `AwsSolutions-IAM5` /
  L1 など）。上流では自動修復ロール等について `this stack is used for administrative task` の
  reason で抑制している。管理タスク専用であることが前提であり、自分のワークロードで同種の
  ワイルドカード権限を安易に流用しないこと。
- **ログ格納バケット自身の仕様由来**（`AwsSolutions-S1`）。サーバーアクセスログを格納する
  バケット自体にはアクセスログを設定できないため、`this s3 bucket is used to store server
  access log itself` の reason で抑制している。
- **設定がオプションであることに起因するもの**（`AwsSolutions-SNS2` など）。上流では SNS の
  サーバーサイド暗号化を任意扱いとし `SNS encryption is an option` の reason で抑制している。
  自分のワークロードでは、要件次第で暗号化を有効化する判断もあり得る。

## テストテンプレート

下流の CDK プロジェクトにコピーして使える、資産非依存の cdk-nag 強制テストテンプレートを
同梱している。自分の Stack の import と instantiation を埋め、レビュー済みの例外のみ
`NagSuppressions` に reason 付きで追加すること。

- [../assets/cdk-nag-test.template.ts](../assets/cdk-nag-test.template.ts)
