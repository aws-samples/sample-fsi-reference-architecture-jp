# バックアップデータのイミュータブル化（Vault Lock / S3 Object Lock）

## 概要

本リファレンスは、本スキルが採用するバックアップデータのイミュータブル化（改変・削除に対する耐性付与）の設計について示す。ランサムウェア対策の観点では、攻撃者がアカウントの管理者権限を奪取した場合でも、バックアップデータが削除や改変されない構成を作ることが復旧の最後の砦となる。

イミュータブル化を実現するための主要な機能として、AWS Backup の **Vault Lock**（Backup vault に保管されるバックアップデータ向け）と Amazon S3 の **S3 Object Lock**（S3 バケットに保管されるオブジェクト向け、ログデータ等で活用可能なもの）が提供されている。本リファレンスでは両機能の特性、コンプライアンスモードとガバナンスモードの選択判断、保持期間の設計、多層防御の組み合わせ、LAG vault との関係について整理する。

マルチアカウント構成における配置は [01-multi-account-architecture.md](./01-multi-account-architecture.md)、ログ保護の文脈での Object Lock 適用は [07-log-collection-and-protection.md](./07-log-collection-and-protection.md) を参照する。

## 基盤メカニズム: WORM 保護による改変・削除耐性

Vault Lock と S3 Object Lock はいずれも **WORM（Write Once, Read Many）** のモデルでデータを保護する。一度書き込まれたバックアップデータやオブジェクトは、設定された保持期間内は誰も削除・上書きすることができない（モードによっては AWS のサポートでも変更不可）。

ランサムウェア対策の観点では、以下の効果を発揮する。

- 攻撃者がアカウント管理者権限を奪取しても、保持期間内のバックアップは削除できない
- 内部不正・誤操作によるバックアップ消失を防止する
- ルートユーザーですら保持期間を短縮できないため、組織内の権限統制ミスにも耐性を持つ

ただし、Vault Lock と S3 Object Lock は**保護対象が異なる別々の機能**である。本構成では、保護対象に応じて両者を使い分ける。

| 機能 | 保護対象 | 主な用途 |
|---|---|---|
| AWS Backup Vault Lock | Backup vault に保管されたバックアップデータ（復旧ポイント） | AWS Backup で取得したバックアップの保護 |
| Amazon S3 Object Lock | S3 バケットに保管されたオブジェクト | ログデータ（CloudTrail、Config、VPC Flow Logs 等）の保護、オンプレからの S3 直接バックアップの保護 |

## AWS Backup Vault Lock

### 概要

AWS Backup Vault Lock は、Backup vault に対する WORM 保護を実現する機能である。Vault Lock を有効化すると、Vault 内の復旧ポイントは設定された保持期間内、削除や変更ができなくなる。

Vault Lock は AWS Backup の標準機能として提供されており、追加料金は発生しない。Cohasset Associates により SEC 17a-4、CFTC、FINRA 規制の環境での利用に対する適合性評価が実施されており、規制対応が求められる金融機関でも採用しやすい機能となっている。

### Vault lock のモード

Vault Lock には以下の2つのモードがある。

| モード | 概要 | 主な用途 |
|---|---|---|
| **Governance mode（ガバナンスモード）** | 特定の IAM 権限を持つユーザーでなければ Lock の解除や変更は一切不可 | 組織内のガバナンス要件を満たしつつ、特定の管理者には変更権限を残したい場合に活用が可能 |
| **Compliance mode（コンプライアンスモード）** | grace time（クーリングオフ期間）を経過した後は、いかなるユーザー/権限であっても、またAWS 側からも Lock を解除・変更できない | 規制対応が厳格に求められ、改変・削除を絶対に許容できない場合に活用が可能 |

コンプライアンスモードの **grace time** とは、Vault Lock を有効化した直後に設けられる猶予期間のことである。grace time 中は Vault Lock の設定を変更したり、Lock 自体を解除したりすることが可能だが、grace time が経過するとそれらの操作が一切できなくなる。

### モード選択の判断軸

ランサムウェア対策および金融機関の規制対応の観点からは、本スキルでは **Compliance mode の採用を基本構成として推奨する**。理由は以下の通り。

- 攻撃者が管理者権限を奪取した場合でも、コンプライアンスモードであれば Lock の解除や保持期間の短縮が不可能であり、ランサムウェア対策として最も強固な保護が得られる
- SEC 17a-4 等の規制対応を必要とする業務システムでは、コンプライアンスモードが規制要件を満たすために必要となるケースが多い
- 内部不正や誤操作のリスクからも保護される

ただし、コンプライアンスモードを採用する際には以下の点に注意する。

- 一度 grace time が経過すると、保持期間の変更や Lock の解除が一切できないため、**保持期間の設定は慎重に行う**必要がある
- 保持期間を長く設定しすぎると、ストレージコストが想定以上に膨らむリスクがあるため、業務要件・規制要件と照らし合わせた上で適切な期間を設定する
- 保持期間が「無期限（Always）」となる設定を誤って適用すると、復旧ポイントが永久に削除できなくなり、コストが累積する

ガバナンスモードは、運用の柔軟性を残したい場合や、本格運用前の検証段階で採用する選択肢となる。ただし、ランサムウェア対策の観点では、攻撃者が IAM 権限を奪取した場合に Lock を解除されるリスクが残るため、本番環境での恒久的な採用は推奨しない。

### 保持期間の設計

Vault Lock では、以下の2種類の保持期間が関係する。

| 保持期間 | 概要 |
|---|---|
| **Vault Lock の最小保持期間 / 最大保持期間** | Vault Lock 自体に設定される、Vault 内の復旧ポイントが従うべき保持期間の範囲 |
| **バックアップライフサイクルの保持期間** | 各バックアップ取得時に、バックアッププラン側で設定される個別の保持期間 |

両者は独立して動作するが、Vault Lock の最小・最大保持期間に違反するバックアップライフサイクル設定は許容されない。設計時には以下を考慮する。

- 業務要件・規制要件（例: 7 年間の保管義務）から逆算して、Vault Lock の保持期間を設定する
- バックアップライフサイクル側の保持期間も Vault Lock の範囲内に収まるよう統一的に設計する
- コスト最適化のため、ライフサイクル管理によるコールドストレージへの移行も併せて検討する（ただしコンプライアンスモードでは移行後の保持期間も Lock の対象となるため、移行設計は慎重に行う）

## Amazon S3 Object Lock

### 概要

S3 Object Lock は、S3 バケットに保管されるオブジェクトに対する WORM 保護を実現する機能である。本スキルでは、ログデータ（CloudTrail、Config、VPC Flow Logs 等）を保管する S3 バケットや、オンプレミス環境から S3 へ直接バックアップするデータの保護で活用する。

Vault Lock と同様に、Cohasset Associates により SEC 17a-4、CFTC、FINRA 規制への適合性評価が実施されている。

### Retention period と Legal hold

S3 Object Lock では、オブジェクトのリテンション（保持）を以下の2つの方法で管理する。

| 機能 | 概要 |
|---|---|
| **Retention period（保持期間）** | 個々のオブジェクトに固定の保持期間を設定する。期間中はオブジェクトの削除・上書きができない。バケット単位のデフォルト保持期間を設定することも可能 |
| **Legal hold（リーガルホールド）** | 期限を設定せず、明示的に解除されるまでオブジェクトの保護を維持する。Retention period とは独立しており、両方を併用することも可能 |

ランサムウェア対策および規制対応の観点では、Retention period による保持期間の設定が基本となる。Legal hold は、訴訟対応や監査対応で「特定のオブジェクトを期限なく保護する必要が生じた」場合に活用する補助的な機能である。

### Retention mode（リテンションモード）

Retention period には Vault Lock と同様に2つのモードが存在する。

| モード | 概要 |
|---|---|
| **Governance mode** | 特別な IAM 権限を持つユーザーであれば、保持期間の変更や削除が可能 |
| **Compliance mode** | いかなるユーザー（AWS アカウントのルートユーザーを含む）であっても、保持期間中の削除・変更は不可能 |

ランサムウェア対策および金融機関の規制対応の観点からは、本スキルでは **Compliance mode の採用を基本構成として推奨する**。判断軸は Vault Lock と同様であり、攻撃者の IAM 権限掌握に対する耐性を確保するためには Compliance mode が必要となる。

### S3 Versioning との組み合わせ（前提条件）

S3 Object Lock は **S3 Versioning（バージョニング）が有効化されたバケットでのみ動作する**。これは、Object Lock がオブジェクトのバージョン単位で保護を適用する仕組みになっているためである。

S3 Versioning と Object Lock の組み合わせにより、以下の保護が実現される。

- 同じキーのオブジェクトが上書きされた場合、新しいバージョンが追加されるが、保護対象の旧バージョンは保持される
- 削除操作を行っても、保護対象のバージョンは削除されず、削除マーカーのみが追加される

## 多層防御の組み合わせ

ランサムウェア対策では、Vault Lock や Object Lock 単独ではなく、複数の保護機構を組み合わせた多層防御を採用することを推奨する。これは、単一の防御層が突破された場合でも他の層で保護される構成を実現するためである。

### バックアップデータ向けの多層防御（AWS Backup）

| 保護層 | 役割 |
|---|---|
| Vault Lock（Compliance mode） | Backup vault 内の復旧ポイントを WORM 保護 |
| クロスアカウントコピー | 業務アカウント単独でのバックアップ消失を防止（[01-multi-account-architecture.md](./01-multi-account-architecture.md) 参照） |
| KMS 暗号化（アカウント別の独立した CMK） | 攻撃者が特定アカウントの鍵を奪取してもコピー先データの復号を防止（[04-encryption-strategy.md](./04-encryption-strategy.md) 参照） |
| SCP による Vault 削除操作の Deny | Organizations レベルで Vault 削除アクションを予防的に Deny（[06-policy-and-access-control.md](./06-policy-and-access-control.md) 参照） |

### ログデータ向けの多層防御（Amazon S3）

| 保護層 | 役割 |
|---|---|
| S3 Object Lock（Compliance mode） | オブジェクトを WORM 保護 |
| S3 Versioning | 上書き・削除があっても旧バージョンを保持 |
| MFA Delete | バージョンの完全削除には MFA 認証が必要となり、攻撃者による削除を実質的に防止 |
| SCP による S3 バケット削除・ポリシー変更の Deny | Organizations レベルで S3 バケットの破壊的操作を予防的に Deny |

これらを組み合わせることで、いずれか1つの防御層が突破されても他の層でデータが保護される構成となる。

## LAG vault との関係

LAG vault（Logically air-gapped vault）は、Vault Lock 相当のイミュータブル化が**作成時点から強制適用される** Vault である。通常の Backup vault に対する Vault Lock 設定の手順を踏む必要がなく、LAG vault を作成した時点で改変・削除耐性が組み込まれている。

| 項目 | 通常の Backup vault + Vault Lock | LAG vault |
|---|---|---|
| イミュータブル化の適用 | Vault 作成後、Vault Lock を別途有効化する必要がある | 作成時点で自動的に適用される |
| モード選択 | Governance mode / Compliance mode から選択 | Compliance mode 相当が強制適用 |
| 設定変更の余地 | grace time 中は変更可能 | 作成時に最小・最大保持期間を設定し、それ以降は変更不可 |

LAG vault を採用する場合、ユーザー側で Vault Lock を別途設定する必要はなく、保持期間の設定のみを行えばよい。LAG vault の採用判断は [01-multi-account-architecture.md](./01-multi-account-architecture.md) の「構成選択の3パターン」を参照する。

## 対策効果のサマリ表

本リファレンスで扱う各要素が、ランサムウェア対策としてどのリスクに有効かを整理する。

| 対策要素 | 防御するリスク | 有効なシナリオ |
|---|---|---|
| Vault Lock（Compliance mode） | バックアップの削除・改ざん | 攻撃者が IAM 権限・ルート権限を奪取した場合 |
| Vault Lock（Governance mode） | 通常運用での誤操作によるバックアップ消失 | 内部の誤操作リスクが主な懸念で、緊急時の管理者操作余地を残したい場合 |
| S3 Object Lock（Compliance mode） | ログデータの削除・改ざん | 攻撃者がログ集約先の S3 バケットへの権限を得た場合 |
| S3 Object Lock（Legal hold） | 訴訟・監査対応で特定オブジェクトを期限なく保護する必要 | 法務対応が必要なインシデント発生時 |
| S3 Versioning | オブジェクト上書き・削除による消失 | 誤操作、内部不正による削除 |
| MFA Delete | 攻撃者によるバージョン完全削除 | 攻撃者が S3 バケットの管理権限を奪取した場合 |
| LAG vault のイミュータブル化強制 | Vault Lock 設定漏れによる保護不全 | 運用負担を軽減しつつ確実に保護したい場合 |

## 関連する他 reference

- [01-multi-account-architecture.md](./01-multi-account-architecture.md): マルチアカウント構成における Vault 配置、LAG vault の採用判断
- [04-encryption-strategy.md](./04-encryption-strategy.md): KMS 暗号化、キー管理戦略の詳細
- [06-policy-and-access-control.md](./06-policy-and-access-control.md): SCP による Vault 削除操作の Deny 等のポリシー設計
- [07-log-collection-and-protection.md](./07-log-collection-and-protection.md): ログ保護における Object Lock の活用

## 参考: 公式ドキュメント

- [AWS Backup](https://docs.aws.amazon.com/aws-backup/)
- [Amazon S3](https://docs.aws.amazon.com/AmazonS3/)

AWS Backup Vault Lock の grace time の動作仕様、コンプライアンスモードでの保持期間設定の詳細、Cohasset Associates によるコンプライアンス評価レポート、S3 Object Lock の Retention period・Legal hold の設定手順、S3 Versioning との組み合わせの詳細等は、AWS Backup および Amazon S3 公式ドキュメントの最新版を参照すること。
