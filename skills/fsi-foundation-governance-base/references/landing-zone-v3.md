# AWS Control Tower Landing Zone ver3.0 のアップデートに関する注意事項

本ドキュメントは Control Tower Landing Zone v3.0 へのバージョンアップに伴う `base-ct-guest` のデプロイ時の
注意事項と、必要となるソースコードの修正方法を記述する。出典は `doc/governance-base/update-for-landigzon30.md`。
AWS Control Tower Landing Zone の v3.0 へのバージョンアップに伴い、`usecases/base-ct-guest` のデプロイ前に、
ご自身の環境に合わせて `base-ct-guest` のソースコードを修正していただく場合がある。

## アップデートによる BLEA への影響

AWS Control Tower Landing Zone ver.3.0 より、CloudTrail の設定を有効化した場合の CloudTrail のログは、管理
アカウントの AWS CloudWatch Logs に集約されるようになった。

- ご参考: https://docs.aws.amazon.com/controltower/latest/userguide/2022-all.html#version-3.0

その結果、これまでゲストアカウント上に存在していた CloudTrail のログが出力される CloudWatch Logs のロググループが
新たに作成されなくなり、`base-ct-guest` でデプロイされていた AWS CloudTrail のログを監視する通知がデプロイできなく
なった。

## BLEA for FSI の対応方針

BLEA for FSI では、ベースとなった BLEA と同様にゲストアカウントのログ監視はゲストアカウントの管理者が実施すべきと
考えるため、これまで AWS Control Tower Landing Zone がアカウントのプロビジョニング時に作成していた AWS CloudTrail
証跡と AWS CloudWatch Logs のリソースを CDK テンプレートによるガバナンスベースのセットアップ時に生成するように修正
した。この対応によりゲストアカウントでの CloudTrail 証跡が二重に取得される（Control Tower がセットアップする組織
レベルの証跡と BLEA for FSI によりセットアップされるゲストアカウント内での証跡）ことに注意すること。

ただし、適用する Control Tower Landing Zone のバージョンが 3.0 より前であった場合や、3.0 以降へのアップデート時に
ランディングゾーン設定の AWS CloudTrail 設定で「組織レベルのログ記録」を有効にしない場合は、デフォルトの状態では
CDK スタック（`usecase/base-ct-guest/lib/bleafsi-base-ct-guest-stack.ts`）により不要な CloudTrail 証跡ログが作成
されてしまうため、ご自身の環境に合わせてソースコードを一部修正することを推奨する。

## ソースコードの修正方法

以下のフローチャートに従い、ご自身の環境に適した `usecase/base-ct-guest/lib/bleafsi-base-ct-guest-stack.ts` の
ソースコードの修正方針を確認すること。図中の略語は CT: Control Tower、LZ: Landing Zone、CTrail: CloudTrail。

```mermaid
flowchart TD
A[START] --> B{CT LZを<br>v3.0より前から<br>利用している}
B -->|YES| C{LZのバージョンを3.0<br>に更新してCTrailの[組織レベルのログ記録」設定を<br>有効化する}
C -->|NO| D[ケース2: 修正要]
C -->|YES| E[ケース2: 修正不要]
B -->|NO| E
```

### ケース 1: 修正要 — ゲストアカウント上で新規のリソースを作成しない

バージョン 3.0 より前の AWS Control Tower Landing Zone が作成したリソースを利用するため、ゲストアカウント上に新規の
CloudTrail 証跡と CloudWatch Logs ロググループを作成しないように `bleafsi-base-ct-guest-stack.ts` を修正する。

[修正手順] `bleafsi-base-ct-guest-stack.ts` の 7 行目の import 文と、42, 43 行目にあるコード（block2）をコメントアウト
して、33 行目（block1）のコードのコメントを外す。

7 行目の import 文をコメントアウト:

```js
//import { CloudTrail } from './cloudtrail-trail';
```

block2（CloudTrail 証跡を新規作成するコード）をコメントアウト:

```js
// ----- block2 ----
//const cloudTrail = new CloudTrail(this, `CloudTrail`, props.env);
//const cloudTrailLogGroupName = cloudTrail.cloudTrailLogGroup.logGroupName;
// -----------------
```

block1（Control Tower が作成した既存ロググループを参照するコード）のコメントを外す:

```js
// ----- block1 ----
const cloudTrailLogGroupName = 'aws-controltower/CloudTrailLogs';
// ----------------
```

### ケース 2: 修正不要 — ゲストアカウント上に新規でリソースを作成する

`bleafsi-base-ct-guest-stack.ts` の修正は不要。`cloudtrail-trail.ts` によりゲストアカウント上に CloudTrail 証跡と
CloudWatch Logs ロググループが作成される。

## 備考

- AWS Control Tower Landing Zone の ver.3.0 において、一度でも AWS CloudTrail の「組織レベルのログ記録」設定を無効化
  すると、過去に生成されていた AWS CloudTrail と AWS CloudWatch Logs のリソースは削除される。
