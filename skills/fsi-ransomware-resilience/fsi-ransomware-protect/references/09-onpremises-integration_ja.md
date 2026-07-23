# オンプレミス環境のバックアップ統合

## 概要

本リファレンスは、本スキルが採用するオンプレミス環境のバックアップを AWS で取得・保護する設計について示す。日本の金融機関では、オンプレミス環境に重要なシステムを保有しているケースが依然として多く、特に VMware ベースの仮想化環境が広く稼働している。これらのオンプレミス環境もランサムウェアの脅威にさらされており、ランサムウェア対策としてのバックアップ・データ保護は AWS 環境だけでなくオンプレミス環境を含めて統合的に設計することを推奨する。

オンプレミスのバックアップを AWS 側に保管することで、3-2-1 ルールにオンプレミス環境を組み込み、オンプレミスが侵害された場合でも AWS 側にクリーンなバックアップが残る構成を実現することが可能となる。

本リファレンスでは、AWS Backup Gateway による VMware 環境のバックアップ、DataSync / Storage Gateway / S3 API による S3 へのバックアップ、2つのアプローチの使い分け、通信経路のプライベート化、帯域設計、VMware 環境固有の感染チェックワークアラウンド、オンプレミス環境のログ収集・保護について整理する。

マルチアカウント構成における配置は [01-multi-account-architecture.md](./01-multi-account-architecture.md)、Vault Lock の詳細は [02-immutability.md](./02-immutability.md)、KMS 暗号化は [04-encryption-strategy.md](./04-encryption-strategy.md) を参照する。

## 基盤メカニズム: AWS への統合保護の意義

オンプレミス環境のバックアップを AWS 側に保管する設計は、ランサムウェア対策の観点で以下の効果をもたらす。

- **3-2-1 ルールへのオンプレミス環境の組み込み**: オンプレミスとは物理的・論理的に分離された AWS 環境にバックアップを配置することで、オンプレミス側が全面的に侵害された場合でも AWS 側にクリーンなバックアップが残る構成となる
- **AWS 側のデータ保護機能の適用**: AWS Backup の Vault Lock（イミュータブル化）、KMS 暗号化、クロスアカウント・クロスリージョンコピー等の保護機能を、オンプレミスのバックアップに対しても適用することが可能となる
- **統合的な運用・監査**: オンプレミスと AWS 環境のバックアップを AWS 側で一元的に運用・監査することで、ランサム対策の体制を組織横断で構築できる

オンプレミスのデータを AWS で保護するアプローチは大別して以下の2つに整理できる。

| アプローチ | 主な対象環境 |
|---|---|
| **AWS Backup Gateway による VMware 環境のバックアップ** | VMware vSphere 環境 |
| **DataSync / Storage Gateway / S3 API による S3 へのバックアップ** | VMware 以外の環境、または AWS Backup Gateway の制約に該当する VM |

## アプローチ1: AWS Backup Gateway による VMware 環境のバックアップ

### 機能概要

AWS Backup Gateway をオンプレミスの VMware 環境に配置することで、AWS Backup を使ったオンプレミス VM のバックアップ取得が可能となる。Backup Gateway は VMware 環境と AWS Backup の橋渡し役を担い、AWS Backup のバックアッププラン機能を通じて日次・週次・月次等の定期バックアップを取得することができる。バックアップから VMware 環境へのリストアも可能であり、有事の際にはオンプレミス側で復旧することができる。

### AWS Backup の保護機能の適用

AWS Backup Gateway 経由で取得したバックアップは AWS Backup の Backup vault に保管されるため、AWS 環境のバックアップと同じ保護機能を適用することが可能となる。

- Vault Lock によるイミュータブル化（[02-immutability.md](./02-immutability.md) 参照）
- KMS による暗号化（[04-encryption-strategy.md](./04-encryption-strategy.md) 参照）
- クロスアカウント・クロスリージョンコピーによる多重保護（[01-multi-account-architecture.md](./01-multi-account-architecture.md) 参照）
- Audit Manager レポートによる監査証跡の記録（[08-monitoring-and-audit.md](./08-monitoring-and-audit.md) 参照）

### 制約事項

AWS Backup Gateway を採用する際には以下の制約に注意する。具体的なバージョン番号や対応状況は機能拡張により変わる可能性があるため、設計時には AWS Backup 公式ドキュメントの [Working with hypervisors](https://docs.aws.amazon.com/aws-backup/latest/devguide/working-with-hypervisors.html) の最新版を参照することを推奨する。

- **vSphere の対応バージョン制約**: サポートされる vSphere のバージョンに制限がある
- **非対応のディスク構成**: RDM（Raw Device Mapping）ディスク、NVMe コントローラーとそのディスク、独立永続ディスクモード（Independent Persistent）、独立非永続ディスクモード（Independent Non-Persistent）等が対応外となる場合がある

これらの非対応要素を含む VM については、後述のアプローチ2 を併用することを検討する。

## アプローチ2: DataSync / Storage Gateway / S3 API による S3 へのバックアップ

### 機能概要

VMware 環境ではないオンプレミスシステム、または AWS Backup Gateway の制約に該当する VM については、オンプレミスのデータを Amazon S3 バケットにアップロードし、S3 Object Lock 等によってイミュータブルに保護するアプローチを推奨する。

### 利用可能な転送手段

| 転送手段 | 主な特徴 |
|---|---|
| **AWS DataSync** | 大量データの定期的な転送に適している。スケジュール実行、帯域制御、データ整合性検証等の機能を備える |
| **AWS Storage Gateway（File Gateway）** | NFS / SMB 経由でオンプレミスから S3 にデータを保管する。オンプレミスのアプリケーションからは通常のファイルシステムとして見える形となる |
| **S3 API（直接アップロード）** | AWS CLI の `aws s3 sync` コマンドや S3 API を使った直接アップロード。スクリプトベースの柔軟な運用が可能 |

| 条件 | 推奨手段 |
|---|---|
| 大量データの定期転送、帯域制御が必要 | AWS DataSync |
| オンプレミスアプリから NFS / SMB でアクセスしたい | AWS Storage Gateway（File Gateway） |
| スクリプトベースの柔軟な運用、既存の転送ジョブとの統合 | S3 API / `aws s3 sync` |

### データ保護

S3 にアップロードしたデータは、以下の保護機構を組み合わせて多層防御することを推奨する。詳細は [02-immutability.md](./02-immutability.md) および [07-log-collection-and-protection.md](./07-log-collection-and-protection.md) を参照する。

- **S3 Object Lock**: アップロードされたデータをイミュータブルに保護する。コンプライアンスモード / ガバナンスモードを規制要件に応じて選択
- **S3 Versioning**: Object Lock の前提として有効化が必要となる。上書き・削除があっても旧バージョンが残るため、誤操作・攻撃に対する追加の保護層となる
- **S3 暗号化**: SSE-S3 または SSE-KMS による保管時暗号化

## 2つのアプローチの使い分け

| 条件 | 推奨アプローチ |
|---|---|
| オンプレミスが VMware 環境で、VM 単位のバックアップ・リストアが必要 | アプローチ1: AWS Backup Gateway |
| VMware 以外の環境（物理サーバー、Microsoft Hyper-V 等） | アプローチ2: DataSync / Storage Gateway / S3 API |
| VMware 環境だが、RDM / NVMe / 独立ディスクモード等の非対応要素を含む VM | アプローチ2: DataSync / Storage Gateway / S3 API |
| ファイル単位のバックアップで十分（VM 全体のリストアは不要） | アプローチ2: DataSync / Storage Gateway / S3 API |

VMware 環境であっても全 VM が AWS Backup Gateway の対応条件を満たすとは限らないため、組織内の VM 構成を確認した上で、ハイブリッドにアプローチ1とアプローチ2を併用する設計も選択肢となる。

## 通信経路のプライベート化

多くの金融機関では、バックアップデータの通信経路としてインターネット経由ではなくプライベート経路での通信を選択されるケースが多い。本スキルでは、その前提に立ち、オンプレミスから AWS への通信経路のプライベート化を推奨する。

### アプローチ1（AWS Backup Gateway）の場合

```
オンプレミスシステム
  → AWS Backup Gateway（オンプレミスに配置）
    → AWS Direct Connect
      → VPC
        → AWS PrivateLink
          → AWS Backup
```

AWS Direct Connect と AWS PrivateLink の組み合わせにより、インターネットを経由しないプライベートな経路でバックアップデータが転送される構成となる。

### アプローチ2（S3 へのバックアップ）の場合

```
オンプレミスシステム
  → AWS Direct Connect
    → VPC
      → VPC Endpoint（S3 Gateway Endpoint）
        → Amazon S3 バケット
```

AWS Direct Connect と VPC Endpoint（Gateway Endpoint for S3）の組み合わせにより、インターネットを経由しないプライベートな経路でデータ転送が可能となる。

## 帯域設計と既存通信への影響

オンプレミスから AWS への定期的なバックアップは、AWS Direct Connect の帯域を消費するため、既存の業務通信への影響を考慮した設計が必要となる。

### AWS Backup Gateway の帯域制御

AWS Backup Gateway は帯域幅制御（bandwidth throttling）の機能を備えており、業務時間帯の帯域使用を制限する等の運用が可能となる。これにより、Direct Connect を通じた既存通信への影響を抑制することができる。

### 増分バックアップによる通信量の軽減

AWS Backup による VMware バックアップは、初回はフルバックアップとなるが、以降は CBT（Changed Block Tracking）を利用した増分バックアップとなる。そのため、初回以降のバックアップに伴う通信量・実行時間は初回と比較すると限定的となる。

業務影響度の高いシステムでは、初回フルバックアップを業務影響の少ない時間帯（休日夜間等）に実施し、以降の増分バックアップは平日にも分散して実行する設計が考えられる。

## バックアップデータの感染チェック（VMware 環境固有のワークアラウンド）

VMware 環境のバックアップに対するマルウェア感染チェックは、以下の制約により AWS 環境のバックアップとは異なるアプローチが必要となる。

### 制約事項

- **AWS Backup Restore testing 機能は VMware 非対応**: AWS 環境（Amazon EC2 等）では Restore testing 機能で自動的にリストア + 検証を行えるが、VMware 環境ではこの機能が利用できない。そのため、定期的なリストア + 感染チェックを自動化するには独自の仕組みの構築が必要となる
- **オンプレミス環境への余剰キャパシティ**: オンプレミス環境にリストア用の余剰キャパシティが確保されていないケースが多く、定期的なリストアを実施することが難しい場合がある

### EC2 へのリストアによるアプローチと制約

VMware バックアップを Amazon EC2 にリストアして感染チェックを行うアプローチも考えられるが、以下の制約に注意する。詳細は AWS Backup 公式ドキュメントおよび [VM Import/Export 公式ドキュメント](https://docs.aws.amazon.com/vm-import/latest/userguide/prerequisites.html) を参照することを推奨する。

| 制約 | 内容 |
|---|---|
| **OS ライセンス** | EC2 にリストアする際の OS ライセンスの扱い（AWS 提供ライセンス / BYOL）の確認が必要となる |
| **対応 OS の制約** | EC2 にインポート可能な OS は VM Import/Export でサポートされている OS に限定される |
| **ディスクサイズ・ディスク数の上限** | 各仮想マシンディスクのサイズ上限、ディスク数の上限に該当する VM はそのままでは EC2 にリストアできない場合がある |
| **サードパーティ製品のライセンス** | オンプレミスで利用しているウイルスチェック製品・EDR 等のライセンスが EC2 上で有効かどうかは各製品のライセンス体系に依存するため別途確認が必要 |

これらの制約を踏まえると、VMware 環境のバックアップに対する感染チェックは、組織のリソース・ライセンス・運用体制に応じて以下のいずれかを選択することが考えられる。

- VMware 環境にリストアして既存のオンプレミス製品でスキャン（独自の自動化が必要）
- EC2 にリストアして AWS 環境または既存製品でスキャン（ライセンス・OS 等の制約確認が必要）
- バックアップ取得元のオンプレミス環境で稼働中のシステムに対する継続的なマルウェア検知を併用し、バックアップ自体の感染チェックは限定的な運用とする

## オンプレミス環境のログ収集・保護

オンプレミス環境においても、ランサムウェア攻撃後の分析（攻撃経路・時刻・動作のトレース）に備えたログ収集が必要となる。ただし、オンプレミス環境のログ収集・感染チェックは AWS サービスによる効果が AWS 環境と比較すると限定的である。

### AWS サービスによる効果の限界

オンプレミス側のログ収集・分析は、オンプレミス側の製品活用・運用の領域となる。本スキルでは「必要性と考え方」を示すに留め、具体的な製品選定・設定手順には踏み込まない方針とする。

### 考えられるアプローチ

- **Syslog 転送**: VMware 環境やオンプレミスのサードパーティ製品から Syslog 転送を行い、管理アクション・監査イベントを連携・検知する
- **オンプレミス SIEM または AWS 上の SIEM への集約**: オンプレミス側のログを SIEM に集約し、AWS 環境のログと統合的に分析可能な状態にする

これらの設計は組織のセキュリティ部門・SOC チームとの連携が必要となる領域であり、フォレンジックベンダの活用も含めた検討を推奨する。

## 金融機関の文脈での設計判断

### 通信経路のプライベート化に関する設計スタンス

多くの金融機関では、バックアップデータの通信経路としてインターネット経由ではなくプライベート経路での通信を選択されるケースが多い。本スキルでは、その前提に立ち、通信経路のプライベート化（AWS Direct Connect + AWS PrivateLink / VPC Endpoint）を前提とした設計を推奨する。

### オンプレミス環境固有の制約への対応

設計時にはオンプレミス側の構成（VMware バージョン、ディスク構成、OS、サードパーティ製品ライセンス等）を確認する必要がある。これらの確認は組織のオンプレミス運用部門との連携が前提となるため、設計の初期段階で関連部署との合意形成を進めることを推奨する。

### オンプレミス側の補完的な対策の必要性

本リファレンスで述べた AWS サービスによるバックアップ・保護は、オンプレミスのデータを AWS 側に保管する範囲で価値を発揮する。一方、オンプレミス側で稼働中のシステムに対するマルウェア検知、ログ収集、フォレンジック対応等は AWS サービスのスコープ外であり、オンプレミス製品・運用との併用が前提となる。SOC 体制やフォレンジックベンダ活用も含めた組織全体での体制整備を推奨する。

## 対策効果のサマリ表

本リファレンスで扱う各設計要素が、ランサムウェア対策としてどのリスクに有効かを整理する。

| 設計要素 | 防御するリスク | 有効なシナリオ |
|---|---|---|
| AWS Backup Gateway による VMware バックアップ | オンプレミス環境のランサム被害時のデータ消失 | オンプレミス側が全面的に侵害された場合でも AWS 側にクリーンなバックアップが残る |
| DataSync / Storage Gateway / S3 API による S3 バックアップ | VMware 非対応環境・非対応 VM のデータ消失 | 物理サーバー、Hyper-V、AWS Backup Gateway の制約該当 VM の保護 |
| AWS Backup の保護機能の適用（Vault Lock、暗号化、コピー） | バックアップデータ自体の改変・削除 | クラウドに保管したバックアップに対する攻撃 |
| 通信経路のプライベート化（Direct Connect + PrivateLink / VPC Endpoint） | バックアップデータの通信経路への攻撃・盗聴 | 金融機関のセキュリティ要件への適合 |
| AWS Backup Gateway の帯域制御 | 既存業務通信への影響 | Direct Connect 帯域を共有する環境での運用負荷軽減 |
| CBT による増分バックアップ | 通信量・実行時間の長時間化 | 大規模 VMware 環境での継続的なバックアップ |
| オンプレミス側のマルウェア検知・ログ収集の併用 | オンプレ稼働中システムの感染検知漏れ | AWS 側で対処できないオンプレ側の継続的な脅威監視 |

## 関連する他 reference

- [01-multi-account-architecture.md](./01-multi-account-architecture.md): マルチアカウント構成（オンプレミスバックアップ受け入れ先のアカウント設計）
- [02-immutability.md](./02-immutability.md): Vault Lock、S3 Object Lock の詳細
- [04-encryption-strategy.md](./04-encryption-strategy.md): KMS 暗号化、キー管理戦略
- [07-log-collection-and-protection.md](./07-log-collection-and-protection.md): S3 多層防御、ログ保護

## 参考: 公式ドキュメント

- [AWS Backup](https://docs.aws.amazon.com/aws-backup/)
- [AWS DataSync](https://docs.aws.amazon.com/datasync/)
- [AWS Storage Gateway](https://docs.aws.amazon.com/storagegateway/)
- [Amazon S3](https://docs.aws.amazon.com/AmazonS3/)
- [AWS Direct Connect](https://docs.aws.amazon.com/directconnect/)

AWS Backup Gateway がサポートする vSphere バージョン、対応・非対応のディスク構成の詳細、AWS DataSync の転送設定、AWS Storage Gateway の各タイプ別仕様、VM Import/Export の制限事項、各サービスのクォータ等は、AWS Backup、AWS DataSync、AWS Storage Gateway、VM Import/Export 公式ドキュメントの最新版を参照すること。
