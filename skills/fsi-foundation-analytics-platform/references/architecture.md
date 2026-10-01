# リファレンスアーキテクチャ [データ分析プラットフォーム Simple data lake]

## ユースケース

不確実性が高まる事業環境で高速かつ合理的に判断を下すため、データに基づく意思決定の重要性が注目されている。企業が扱うデータの規模は前例のない速度で増加しており、エクサバイト規模のデータを活用する企業も出てきている。AWS はデータ分析に関わる広範なサービスを提供しており、これらを組み合わせることでスケーラブルなデータ分析基盤を迅速に構築できる。本リファレンスアーキテクチャでは、金融機関に求められる水準のセキュリティレベルを備えつつ、将来的なニーズの変化や利用規模拡大に柔軟に対応可能で、コスト最適なデータ分析基盤を構築できるリファレンスアーキテクチャを提示する。

## アーキテクチャ図

Amazon S3 をコアとした Simple data lake のアーキテクチャサンプル。

![Architecture](../assets/images/analitics-app-data-fig030.PNG)

## アーキテクチャの特徴

### データレイクを中心とした分析環境

AWS におけるデータ分析基盤は、Amazon S3 上のデータレイクを中心に構成される。データレイクとは収集したデータを原則そのまま保存しておくデータリポジトリのことである。データレイクを作る上では、データを蓄積するコンポーネントとデータを処理するコンポーネントを分離しておくことが重要である。これは両者が異なるライフサイクルで扱われるためである。データ分析基盤上のデータは数年にわたって蓄積されることで価値を生むのに対して、データを処理する道具は社内外の環境の変化によって適切な選択肢が変わっていく。従って、蓄積と処理を分離することによって一貫したデータリポジトリを整備しつつ、将来のニーズや技術に合わせた様々な道具を使い分け可能なデータ分析基盤を構築できる。データを蓄積するコンポーネントには Amazon S3 を利用することで、高い堅牢性、コスト効率、並列アクセスへのスケーラビリティを備えたデータレイクが構築できる。

### 3 層構造のデータ配置

![3層構造のデータ配置](../assets/images/analitics-app-data-fig032.PNG)

データ分析基盤上のデータは 3 層構造で配置される。これはデータ分析基盤上のデータの将来性を確保しつつ、利活用を促進すると共に、各領域の統制と管理の境界を確保するのに役立つ。

- raw (オリジナルデータ)
  - ソースシステムのデータを未加工のまま配置するレイヤー
  - オリジナルデータを残しておくことで、将来のユースケースの変化に対応可能
  - 基本的にデータ分析基盤管理者のみがアクセス可能
- normalized (標準化データ)
  - raw レイヤーのデータを元に、データを利用する上で共通的に必要とされる名寄せや日付け形式の統一などの前処理、パーティショニングなどによるクエリ効率の最適化などを適用するレイヤー
  - 個人情報などの機微情報へのマスキングも適用し、データ分析基盤利用者に幅広く公開可能な内容にサニタイズする
  - データ分析基盤管理者が analytics レイヤーに見られる共通的な要求を抽出して normalized レイヤーに取り込み、データ分析基盤利用者による利活用を促進する
- analytics (目的別データ)
  - normalized, 他の analytics レイヤーのデータを元に、顧客分析など、個別のビジネス要件に対応した変換を適用するレイヤー
  - データ分析基盤利用者が個別要件に応じて整備し、利活用する

本リファレンスアーキテクチャでは 3 層構造のデータ配置を採用しているが、組織の規模や要件によっては、より細分化された階層が適切である場合もある。まずは上記 3 層を初期案として、検討を進めるのがおすすめである。また、データ分析基盤の管理者や利用者がアクセス可能なデータ範囲の権限制御についても、上記を参考にしつつ、組織に合った設計を検討すること。

### データ分析基盤のペルソナとアクセス権限管理

データレイクへのアクセス権限は各レイヤーの S3 バケットに対して IAM によって管理される。データ分析基盤の運用に関わるペルソナには一般的にデータ分析基盤管理者、データ分析者、ビジネスユーザーが含まれる。

- データ分析基盤管理者
  - データ分析基盤そのものの開発と運用及び normalized までのデータを提供する
- データ分析者
  - データ分析基盤が提供するツールと、normalized, analytics のデータを使って分析を行う
  - ビジネスユーザー向けにダッシュボードを作成する
- ビジネスユーザー
  - データ分析者が作成したダッシュボードを利活用する

それぞれのペルソナに対して、データレイクへの IAM アクセス権限を適切に設定することでデータ分析基盤のセキュリティを確保する。

本リファレンスアーキテクチャでは、比較的シンプルなアクセス権限管理の方法として各レイヤーのバケットに対してリソースベースで IAM のアクセス権限を設定しているが、大規模な組織での運用を想定する場合は、リソースタグによる ABAC や AWS Lake Formation の LF-Tag を用いた属性ベースの権限管理戦略によってよりスケーラブルな統制を検討できる。また、normalized, analytics レイヤーで一部の利用者にのみ機微情報を提供したい場合は、専用のテーブルを構成してアクセス権限を提供する方式に加えて、Amazon Redshift による Dynamic data masking、AWS Lake Formation による行、列レベルのアクセスコントロールも検討できる。

### データライフサイクル

本リファレンスアーキテクチャでは、上記の 3 層構造のデータ配置戦略の中で具体的にどのようなデータライフサイクルが実現できるかのリファレンスを示すため、架空の銀行である「AWS 銀行」のソースシステムから日次で連携される入出金明細、口座情報、顧客、インターネットバンキング契約データを扱う。データ受渡用の S3 バケットに配置されたデータは、AWS Step Functions によってオーケストレーションされた Glue Job によって raw レイヤー → normalized レイヤー → analytics レイヤーへと変換される。より詳細なライフサイクルについては [サンプルアプリケーションデータ説明](application-data.md) を参照すること。

### Amazon QuickSight による可視化

![QuickSightによる可視化](../assets/images/analitics-app-data-fig031.PNG)

本リファレンスアーキテクチャには、データ分析基盤のユースケース例として AWS 銀行のインターネットバンキングのマーケティングダッシュボードが含まれる。本ダッシュボードは normalized レイヤーと analytics レイヤーのデータを元に作成されており、日次のデータ連携に対する一連の変換フローを通じて、最終的にダッシュボードが更新されるまでを観察できる。

### Glue Job の閉域実行

本リファレンスアーキテクチャで使用している Glue Job は Internet Gateway を持たない VPC に接続されており、アクセス可能なネットワーク空間が制限されている。Glue Job から S3 等のリソースへのアクセスは、VPC Endpoint を経由する。

### Glue Data Catalog によるスキーマ管理

データ分析基盤上のデータは、Glue DataCatalog によってデータソースの場所や形式、スキーマ情報などのメタデータが管理される。DataCatalog を管理することで、ETL 処理やクエリエンジンがデータにアクセスする際の実装、設定をシンプルにできる。

### サーバレス分散処理によるスケーラビリティ

ETL には Glue Spark Job、クエリエンジンとして Amazon Athena を採用している。両者はスケールアウトによってデータを分散処理するため、テラバイト規模を超える巨大なデータであっても効率よく処理することができる。同時に両者はサーバレスなサービスであり、必要な時に必要な分だけリソースが確保されるため、コスト効率も最適化できる。従って、スモールスタートの段階のデータ分析基盤から、中長期的な成長を見据えて利用できる。

## 主要コンポーネント（CDK 実装より）

CDK サンプル（`assets/sample-cdk/`）の実装から確認できる主要コンポーネントは以下の通りである。

- **VPC**: プライベート/隔離サブネットを 2 AZ に配置し、VPC Flow Logs を有効化。VPC Endpoint（S3 Gateway、KMS、Glue）を経由してサービスにアクセスする。Glue Connection 用のセキュリティグループは自己参照のインバウンドルールを持つ。
- **S3 バケット**: origin（オリジナルデータ）、raw（生データ）、normalized（正規化データ）、analytics（分析用データ）、master（マスターデータ）の各バケットを SSE-KMS の CMK で暗号化。Athena 検索結果用バケットは Athena WorkGroup 側で暗号化するため KMS では暗号化しない。バケット名は `bleafsi-analyticsplatform-<レイヤー>-<アカウント ID>` の形式。
- **KMS キー**: S3 バケット暗号化用の共通 CMK と、Athena WorkGroup 暗号化用の CMK を作成。Glue Data Catalog も KMS（SSE-KMS）で暗号化する。
- **AWS Glue**: origin → raw、raw → normalized、normalized → analytics の変換を行う Glue Job 群を作成。Glue SecurityConfiguration で CloudWatch ログ、Job Bookmark、S3 の各暗号化を KMS で設定。Glue Job スクリプトは S3 の Glue Asset バケットにアップロードされる。
- **AWS Step Functions**: `bleafsi-analyticsplatform-glue-job-pipeline` ステートマシンが Glue Job を Parallel（OriginToRaw → RawToNormalize → NormalizeToAnalysis）でオーケストレーション。各タスクは 30 秒間隔でリトライ。`import_date` パラメータの有無を Choice で判定する。ログは全レベルで LogGroup に出力。
- **EventBridge Schedule**: ステートマシンを日次（hour 15, minute 0）で定期実行する。
- **Amazon Athena**: `bleafsi-analyticsplatform-workgroup` WorkGroup（Athena engine version 3）を作成。結果は SSE-KMS で暗号化し、WorkGroup 設定を強制する。
- **CloudWatch アラーム**: Step Functions の実行を監視し、`notifyEmail` に通知する。
- **QuickSight ロール**: QuickSight が normalized/analytics/master/Athena 出力の各バケットと KMS キーにアクセスできるよう IAM ロールポリシーを割り当てる。

## 参考情報

- [データレイクとは](https://aws.amazon.com/jp/big-data/datalakes-and-analytics/what-is-a-data-lake/)
- [AWS のモダンデータアーキテクチャ](https://aws.amazon.com/jp/big-data/datalakes-and-analytics/modern-data-architecture/)
- [AWS の ABAC とは](https://docs.aws.amazon.com/ja_jp/IAM/latest/UserGuide/introduction_attribute-based-access-control.html)
- [Lake Formation のタグベースのアクセス制御](https://docs.aws.amazon.com/ja_jp/lake-formation/latest/dg/tag-based-access-control.html)
