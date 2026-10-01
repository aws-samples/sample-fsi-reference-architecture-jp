---
name: fsi-lens-for-fisc
description: >-
  日本の金融機関 (FSI) のワークロードを AWS 上で AWS Well-Architected
  フレームワークおよび FISC 安全対策基準 (FISC Security Guidelines) に照らして
  評価するための Well-Architected FSI Lens for FISC (FSI Lens) のナレッジベース。
  FISC 実務基準に対して金融ワークロードをレビューまたは設計するとき、Well-Architected
  の柱（運用上の優秀性・セキュリティ・信頼性）を FISC の考慮事項にマッピングするとき、
  または FSI Lens のベストプラクティスに関する質問に回答するときに、このスキルを使用する。
  トリガー: FSI Lens, FISC, 金融情報システムセンター, 安全対策基準, Well-Architected,
  ウェルアーキテクテッド, FISCOPS, FISCSEC, FISCREL, 実務基準。
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Well-Architected FSI Lens for FISC

## ワークロード概要

**AWS Well-Architected フレームワーク FSI Lens for FISC**（FSI Lens）は、AWS 上で
**日本の金融サービス業界 (FSI)** のワークロードを設計・デプロイ・運用するための
コンテキスト固有のガイダンスを提供する Well-Architected「レンズ」である。汎用的な
AWS Well-Architected フレームワークを拡張し、金融情報システムセンター（FISC / 金融情報
システムセンター）が公表する **FISC 安全対策基準・解説書**（金融機関等コンピュータシステム
の安全対策基準・解説書）に沿ったベストプラクティスを提供する。FISC 安全対策基準は、日本の
金融機関における事実上の業界標準の一つであり、金融庁の監督指針でもシステムリスクおよび
セキュリティ対策の参考文書として挙げられている。

**目的**。本レンズは、FISC 安全対策基準に沿って、**回復力・セキュリティ・運用パフォーマンス**
を促進する形で FSI ワークロードを構築する方法に焦点を当てる。アーキテクトがアーキテクチャ
をベストプラクティスに照らして一貫的に測定し、改善すべき領域を特定できるようにする。

**利用方法**。本レンズは **3 つの柱**（運用上の優秀性・セキュリティ・信頼性）で構成され、
それぞれが **FISC 質問**（`FISCOPS`・`FISCSEC`・`FISCREL` で始まる）と **ベストプラクティス**
（`-BPnn`）を持つ。各ベストプラクティスは 1 つ以上の FISC 実務基準番号（FISC 実務基準、
実 N と表記）に紐づいている。相互参照表は、各 FISC 実務基準（実 1〜実 153）を、関連する
Well-Architected フレームワークの質問および FSI Lens の質問にマッピングし、FISC 安全対策
基準の第 12 版と第 13 版のマッピングを区別している。FSI 固有でない一般的なベストプラクティス
については、ベースとなる AWS Well-Architected フレームワークも併せて参照すること。

**重要な前提・注意事項（出典より）**。
- FISC 安全対策基準には **適合／認証制度が存在しない**。よって本レンズは適合を **保証しない**。
  各組織は業務アプリケーションを含めて自社で安全対策基準へのチェックを実施する必要がある。
- FISC 安全対策基準の **第 13 版**（2025 年 3 月公表）では、新たに AI・生成 AI の安全対策
  に関する基準項目が新設された。AI ワークロードについては、AWS は本レンズに加えて、ML
  ワークロードには **Machine Learning Lens** を、生成 AI ワークロードには **Generative
  AI Lens** を併用することを推奨する。

## ベストプラクティスと主要コンポーネント

### ベストプラクティス

以下は本レンズ自体のベストプラクティスを、インジケーター接頭辞付きのルールとして再掲した
ものである。それぞれ出典ドキュメントの FISC 質問／実務基準に対応する。

運用上の優秀性（FISCOPS）:
- MUST: オペレーションを記録する。自動化されたプロセスと手動オペレーション（コンソール・
  CLI・EC2 ログイン）の両方を記録・確認し、正当な権限を持つ主体が正しく操作したことを
  示せるようにする（FISCOPS1-BP01、実 38）。
- SHOULD: コードとしてインフラストラクチャを実装し、環境全体をプログラム的に構築・分離・
  復旧できるようにする（FISCOPS1-BP02、実 42）。
- MUST: コード／アーティファクトをバージョン管理し、本番環境と開発中のコード／アーティ
  ファクトを分離することで、アプリケーションの改ざんを防ぐ（FISCOPS1-BP03、実 40／実 96）。
- SHOULD: コードレビューを自動化して、新たなバグや脆弱性を減らし、開発段階から品質を
  向上させる（FISCOPS1-BP04、実 96）。
- SHOULD: クラウドプロバイダーのイベントを監視し、ワークロードに影響しうるイベント発生時に
  アラートと修復ガイダンスを利用できるようにする（FISCOPS2-BP01、実 46）。
- SHOULD: 監視を一元化し、組織全体でクラウド監視のプラクティスを標準化して情報サイロを
  回避する（FISCOPS2-BP02、実 46）。
- SHOULD: 定期的に負荷テストを実施して主要メトリクスを特定し、アラートと自動修復が機能する
  ことを検証して平均検出時間を最小化する（FISCOPS2-BP03、実 46）。
- MUST: ワークロードに適用される規制要件を含め、データバックアップと保持の要件を理解する
  （FISCOPS3-BP01、実 39）。
- SHOULD: 短期保持のランサムウェア対策バックアップをバックアップ戦略に組み込み、アクセスを
  厳格に制限し暗号化する（FISCOPS3-BP02、実 39）。
- SHOULD: 規制要件に応じてデータを保持・パージするバックアップのライフサイクルポリシーを
  作成する（FISCOPS3-BP03、実 39）。
- MUST: RPO を満たす頻度で、ポイントインタイムリカバリに対応した継続的または定期的な
  データファイルのバックアップを確保する（FISCOPS3-BP04、実 39）。
- MUST: データだけでなく、ワークロードの再デプロイと RTO 達成に必要なインフラストラクチャ
  構成もバックアップする（FISCOPS3-BP05、実 43）。
- MUST: 重要な運用ドキュメント（設計資料・手順書）をバージョン管理し、更新時に責任者の
  承認を必須として意図しない変更／改ざんを防ぐ（FISCOPS4-BP01、実 44）。
- MUST: ドキュメントの閲覧を適切な個人またはチームに制限する（FISCOPS4-BP02、実 44）。
- SHOULD: 災害対策に必要なドキュメントのバックアップを行う（FISCOPS4-BP03、実 45）。

セキュリティ（FISCSEC）:
- MUST: 重要なファイルに適切なアクセス制御を適用して不正アクセスから保護する。最小権限と
  多層防御（セキュリティグループ・NACL・サブネット・Network Firewall・VPC 限定アクセス）を
  用いる（FISCSEC1-BP01、実 5）。
- MUST: 決まった拠点以外での操作が可能な端末を識別し、その権限の範囲を明確に定義する
  （FISCSEC1-BP02、実 61）。
- SHOULD: アイデンティティデータを扱うシステムでの権限付与／削除オペレーションを明確にし、
  申請者と承認者を分離して定期的にアクセスを見直す（FISCSEC1-BP03、実 27）。
- MUST: サポートされるすべてのリージョンで CloudTrail を有効化し、厳格に制限された一元化
  ログアカウントにログを保管し、ログファイル整合性検証を行って AWS アカウントのアクティビティ
  を監視する（FISCSEC2-BP01、実 63／実 10）。
- MUST: アカウントのアクティビティと実際の操作者の関連付けを検証可能にする（例: HR と統合
  した一元的な ID プロバイダー）（FISCSEC2-BP02、実 63）。
- SHOULD: サービスのタイムゾーンを確認し、データベースレイヤーでは UTC を使用してシステム間の
  時刻のずれを回避する（FISCSEC2-BP03、実 10）。
- SHOULD: アプリケーションレイヤの入力チェックと、データ処理履歴の収集・管理により、不良
  データの混入や不正から入力データを保護する（FISCSEC3-BP01、実 6／実 65）。
- MUST: データ分類を用いて適切なコントロールレベルを決定する。データの分類と暗号化などの
  コントロールの実装はお客様の責任である（FISCSEC4-BP01、実 69）。
- MUST: ユーザーに対して強度の高いパスワードポリシーを設定する（FISCSEC5-BP01、実 1／実 26）。
- MUST: 初回サインイン時のパスワード変更を強制する（FISCSEC5-BP02、実 1／実 26）。
- SHOULD: 接続元を必要最小限（認証情報・IP アドレス・クライアント証明書）に制限する
  （FISCSEC5-BP03、実 8）。
- SHOULD: アイデンティティと接続を一元管理し、パスワードの使い回し／漏洩リスクを軽減する
  （FISCSEC5-BP04、実 26）。
- MUST: 多要素認証 (MFA) を有効化して、ルートユーザーおよび IAM ユーザーを含む AWS リソース
  を保護する（FISCSEC5-BP05、実 26）。
- SHOULD: 特定取引時に顧客へ通知し、補助的な認証（SMS など）を追加して不正利用を検知／防止
  する（FISCSEC6-BP01、実 112）。
- MUST: アクセス履歴と状況を管理する。アプリケーション／ログインログを収集し、MFA と接続元 IP
  でアクセスを制限する（FISCSEC7-BP01、実 11／実 16／実 113）。
- MUST: 予期されるトラフィックと予期しないトラフィックを監視し、AWS WAF と AWS Shield で
  公開サイトを DoS/DDoS から守ることでアプリケーションを保護する（FISCSEC7-BP02、実 16）。
- SHOULD: 収集したログを分析してアプリケーションの動作を監視し、ログへのアクセスを制限して
  改ざん／削除を防止する（FISCSEC7-BP03、実 18）。
- MUST: AWS KMS のエンベロープ暗号化を用いて暗号化キーを安全に管理する。多くの金融のお客様
  にはカスタマー管理の CMK が推奨される（FISCSEC8-BP01、実 13／実 30）。
- SHOULD: 暗号化キーをローテーションし、CMK の自動キーローテーションを有効化する
  （FISCSEC8-BP02、実 30）。
- SHOULD: 鍵管理の権限とリソースの所有権を分離してセキュリティを強化する（FISCSEC8-BP03、
  実 30）。
- SHOULD: データの利用終了時に、そのキーが他のデータに使われていないことを確認したうえで
  暗号化キーを削除し、復号を困難にして廃棄証明の代わりとする（FISCSEC8-BP04、実 82）。
- MUST: 脆弱性へのパッチ適用・承認済みゴールデンイメージの使用・Amazon Inspector による
  AMI／コンテナのスキャンにより、コンピューティングリソースを保護してマルウェアを防ぐ
  （FISCSEC9-BP01、実 22／実 32）。
- MUST: 攻撃後にデータを復元できるよう頻繁にバックアップを取得する。AWS Backup Vault Lock で
  バックアップデータの変更を防止できる（FISCSEC9-BP02、実 22／実 32）。
- SHOULD: SPF・DKIM・DMARC に加え DNSSEC と BIMI を用いて、電子メールをなりすましと改ざん
  から保護する（FISCSEC10-BP01、実 138）。
- SHOULD: S/MIME または PGP 暗号化を用いて送信メールデータを保護し、共有ファイルをマルウェア
  スキャンする（FISCSEC10-BP02、実 138）。

信頼性（FISCREL）:
- MUST: ビジネスの重要度を用いて復旧目標を推進する。回復力の要件はビジネスサービスの重要度に
  比例させ、RTO/RPO と可用性メトリクスに反映する（FISCREL1-BP01、実 74）。
- SHOULD: アプリケーション全体を最も厳格な要件に合わせて設計するのではなく、コンポーネント
  ごとの詳細な復旧要件を適用する（FISCREL1-BP02、実 74）。
- MUST: RTO/RPO を満たすため、定義された復旧戦略（バックアップと復元・パイロットライト・
  ウォームスタンバイ・マルチリージョンアクティブ/アクティブ）を活用する（FISCREL1-BP03、実 74）。
- SHOULD: すべてのロケーションへの配信パイプライン・AWS Config のドリフト検出・CloudFormation
  により、DR サイト／リージョンの設定ドリフトを管理する（FISCREL1-BP04、実 74）。
- SHOULD: あらゆる状況下でシステムが自動的に復旧するよう、復旧を自動化する（例: Elastic
  Disaster Recovery）（FISCREL1-BP05、実 74）。
- MAY: 広域被災の DR シナリオ（例: 東京広域被災）では、リージョン間のサービス差異を考慮
  しつつ、東京リージョンと大阪リージョンにまたがるマルチリージョンのシステム構成を決定する
  （FISCREL1-BP06、実 74）。
- SHOULD: SDLC 環境（開発・テスト・本番）を分離するマルチアカウント戦略を持つ。セキュアな
  ベースラインのテンプレートとして BLEA for FSI が利用できる（FISCREL2-BP01、実 76）。
- SHOULD: AWS Organizations と SCP を用いて SDLC アカウント間で IAM の分離を実装する
  （FISCREL2-BP02、実 76）。
- SHOULD: 本番リソースと非本番リソースの間でネットワークの分離を実施する（FISCREL2-BP03、
  実 76）。
- SHOULD: 予想されるネットワークトラフィックのベースラインを確立し、異常負荷時に運用上の応答を
  トリガーする（FISCREL2-BP04、実 76）。
- MUST: 複数のロケーション（複数のアベイラビリティーゾーン、必要に応じて複数リージョン）に
  ワークロードをデプロイし、正常なリソースにフェイルオーバーする（FISCREL3-BP01、実 104）。
- SHOULD: コードとしてのインフラストラクチャと自動化を実装し、数分で環境を復旧できるように
  する（FISCREL3-BP02、実 106）。
- SHOULD: バックアップの完全性とプロセスを RTO/RPO に照らして検証するため、データの定期的な
  復旧を行う。利用可能な場合はポイントインタイムリカバリを用いる（FISCREL3-BP03、実 106）。
- WILL: FISC 安全対策基準には適合制度がないため、本レンズは適合を保証しない。各組織は自社で
  安全対策基準へのチェックを実施する必要がある（出典の注意事項）。

### 主要コンポーネント

FSI Lens はプロセス指向であり、その論理コンポーネントは 3 つの柱である。各柱は FISC 質問と
ベストプラクティスをグループ化する。「想定される AWS サービス」は、出典ドキュメントがその柱の
ベストプラクティスに関連付けているサービスである。

#### 運用上の優秀性の柱

- **コンポーネント概要**: ワークロードの変更管理（FISCOPS1）・ワークロードの障害の迅速な
  検知（FISCOPS2）・ワークロードのバックアップ取得（FISCOPS3）・重要なドキュメントの管理
  （FISCOPS4）を扱う。対応する FISC 実務基準には 実 38、40、42、43、44、45、46、39、96 が
  含まれる。
- **想定される AWS サービス**: AWS CloudTrail、AWS Systems Manager（Session Manager、
  Automation）、AWS CloudFormation、AWS Config、AWS CodeCommit、Amazon S3（Object Lock・
  ライフサイクル・CRR・バージョニング）、AWS Lambda（コード署名）、Amazon CodeGuru
  Reviewer、AWS Health Dashboard/API、Amazon CloudWatch、AWS Backup、Amazon EBS、Amazon
  DynamoDB、Amazon RDS、Amazon Aurora、Amazon EFS、Amazon Redshift、Amazon Neptune、AWS
  Storage Gateway、Amazon FSx、Amazon EC2 / AMI。

#### セキュリティの柱

- **コンポーネント概要**: アクセス許可の設定・管理（FISCSEC1）・操作記録の検証（FISCSEC2）・
  入力データの保護（FISCSEC3）・データ分類（FISCSEC4）・アイデンティティの保護（FISCSEC5）・
  不正利用の防止（FISCSEC6）・インシデント対応（FISCSEC7）・暗号化キーの管理（FISCSEC8）・
  マルウェア保護（FISCSEC9）・電子メールの安全な運用（FISCSEC10）を扱う。対応する FISC 実務
  基準には 実 1、5、6、8、10、11、13、16、22、26、27、30、32、61、63、65、69、82、112、113、
  138 が含まれる。
- **想定される AWS サービス**: AWS IAM（Access Advisor・Access Analyzer・アクセス許可境界・
  IAM Roles Anywhere）、AWS Organizations / SCP、Amazon VPC（セキュリティグループ・NACL・
  VPC エンドポイント・Network Firewall）、Amazon S3（バージョニング・アクセスログ・Object
  Lock・パブリックブロック）、AWS CloudTrail、Amazon GuardDuty（Malware Protection for S3
  を含む）、AWS Security Incident Response、Amazon CloudWatch（Logs Insights・メトリクス
  フィルタ・Alarm）、AWS Config、AWS Lambda、Amazon SQS、AWS KMS / CloudHSM、AWS IAM
  Identity Center、Amazon RDS、Amazon SNS、AWS WAF、AWS Shield（Standard/Advanced）、VPC
  フローログ、EC2 Image Builder、Amazon Inspector、AWS Systems Manager Session Manager、
  AWS Backup（Vault Lock）、Amazon SES、Amazon Route 53（DNSSEC）、Amazon Kinesis、Amazon
  OpenSearch Service、FireLens。

#### 信頼性の柱

- **コンポーネント概要**: 災害復旧要件の決定（FISCREL1）・SDLC 環境の分離の確保（FISCREL2）・
  コンポーネント障害からのワークロードの保護／復旧（FISCREL3）を扱う。DR 戦略の選択（バック
  アップと復元・パイロットライト・ウォームスタンバイ・マルチリージョンアクティブ/アクティブ）
  や、東京リージョンと大阪リージョンにまたがる広域被災の計画を含む。対応する FISC 実務基準には
  実 74、76、104、106 が含まれる。
- **想定される AWS サービス**: AWS Resilience Hub、AWS Elastic Disaster Recovery、Amazon
  Route 53、AWS Global Accelerator、AWS Config、AWS CloudFormation（StackSets を含む）、AWS
  Organizations / SCP、Amazon VPC（ピアリング・セキュリティグループ・NACL）、AWS WAF、AWS
  Shield / Shield Advanced、Amazon CloudFront、Elastic Load Balancing、Amazon EC2、AWS
  Systems Manager（Automation）、Amazon RDS、Amazon DynamoDB（ポイントインタイムリカバリ）、
  BLEA for FSI（セキュアベースラインのテンプレート）。

## FISC コンプライアンスの概要

本レンズは FISC のガイダンスそのものである。AWS Well-Architected フレームワークの柱を、
2 つのレベルで FISC の考慮事項にマッピングする。

1. **FSI Lens の質問とベストプラクティス** — 各柱の FISC 質問（`FISCOPS`／`FISCSEC`／
   `FISCREL`）とベストプラクティス（`-BPnn`）が、対応する FISC 実務基準番号（実 N）を明示的に
   引用する。
2. **リファレンス相互参照表** — 各 FISC 実務基準（実 1〜実 153）を、関連するベースの
   Well-Architected フレームワークの質問（SEC/OPS/REL/PERF）および FSI Lens の質問に
   マッピングする表。FISC 安全対策基準の **第 12 版と第 13 版で列が分かれており**、第 13 版で
   特定の WA の柱が追加された理由を説明する列を持つ。第 13 版の追加には、Machine Learning Lens
   と Generative AI Lens を指し示す新しい AI・生成 AI 基準（実 150〜実 152）が含まれる。

この相互参照のベースは、AWS が FISC 安全対策基準（第 11 版）向けに公表した FISC コンプライアンス
リファレンスである。本基準には適合制度がないため、このマッピングはガイダンスであり、適合を
保証するものではない。

柱・質問・ベストプラクティスの詳細と、完全な 実 1〜実 153 の相互参照表は、以下に保持されている。
- `references/lens-overview.md` — レンズの目的・注意事項・柱のインデックス。
- `references/operational-excellence.md` — FISCOPS の質問とベストプラクティス。
- `references/security.md` — FISCSEC の質問とベストプラクティス。
- `references/reliability.md` — FISCREL の質問とベストプラクティス。
- `references/fisc-mapping.md` — 完全な 実 1〜実 153 → WA / FSI Lens 対応表。

## リファレンスアーキテクチャ

FSI Lens は単一のリファレンスアーキテクチャを規定しない。これは Well-Architected レンズであり、
FISC 安全対策基準に照らして FSI ワークロードのアーキテクチャを評価・改善するための、柱・質問・
ベストプラクティスの集合である。本レンズがアーキテクチャ上のガイダンスを与える場合、それは
選択肢として提示される。

- **災害復旧戦略**（信頼性）: バックアップと復元・パイロットライト・ウォームスタンバイ・
  マルチリージョンアクティブ/アクティブ。複雑さの昇順、RTO/RPO の降順で列挙される。また、広域
  被災シナリオに向けた東京リージョンと大阪リージョンにまたがるマルチリージョン計画。
- **マルチアカウント分離**（信頼性）: SDLC ステージごとに AWS アカウントを分離する。例として
  **BLEA for FSI** のセキュアベースラインテンプレートが参照される。

本レンズの構造と評価アプローチは `references/lens-overview.md`（構造・柱・注意事項）に記載
されている。本レンズは専用のアーキテクチャ図を提供しない。DR 戦略とマルチアカウントのガイダンス
については `references/reliability.md` を参照すること。

## CDK サンプル概要

本アセットには CDK サンプルは提供されていない。
