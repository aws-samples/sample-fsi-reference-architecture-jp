---
name: fsi-banking-core
description: >-
  金融リファレンスアーキテクチャ日本版（BLEA for FSI）の勘定系（Core Banking）
  ワークロードの AWS リファレンスアーキテクチャ知識。ミッションクリティカルで高可用な
  マルチリージョン構成（東京・大阪のウォーム・スタンバイ）、Aurora Global Database
  （または実験的な Aurora DSQL の選択肢）、DynamoDB グローバルテーブル、Saga パターンの
  ECS マイクロサービス、Application Recovery Controller と Step Functions による
  リージョンフェイルオーバー、Canary 外形監視、ランサムウェア対策の AWS Backup ボールト
  ロック、FISC 準拠マッピングを扱う。勘定系 / 預金 / 為替 / 融資ワークロードの設計・
  レビュー・デプロイ、リージョン切り替え（RTO 約 5 分）の計画、FISC 安全対策基準への
  マッピングを行う際に使用する。
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI 勘定系 (Core Banking) リファレンスアーキテクチャ

## ワークロード概要

**勘定系システム**は、銀行の基幹業務である預金・為替（国内/外国）・融資を取り扱う。金融機関が運用する最もミッションクリティカルなシステムであり、停止は直接的に業務停止を意味し、金融取引におけるデータの不整合は許容されない。

本スキルは、この勘定系ワークロードに対する AWS リファレンスアーキテクチャを「金融リファレンスアーキテクチャ日本版（BLEA for FSI）」から取り込んだものである。目的は、日本の金融機関に求められる厳格な可用性・データ整合性・災害対策要件を満たす勘定系ワークロードの設計・レビュー・デプロイを SA やアーキテクトが支援できるようにすることである。

主要な業務ドライバー:

- **極めて高い可用性** — 計画停止を含め年間ダウンタイムを最小化し、大規模なリージョン災害でも業務を継続する。
- **強いデータ整合性** — フェイルオーバーや復旧時であっても金融データの不整合を許容しない。
- **規制対応** — FISC 安全対策基準（第 13 版）実務基準への明示的なマッピングを提供する。
- **サイバーレジリエンス** — ランサムウェア耐性のあるイミュータブルなバックアップと、自動隔離・復旧を備える。

勘定系をモデルとしているが、本アーキテクチャは**高可用なミッションクリティカルシステム全般に適用できる汎用パターン**である。スコープは勘定系ドメインに限定され、チャネル系や情報系は範囲外である。詳細は `references/architecture.md` を参照。

## ベストプラクティスと主要コンポーネント

### ベストプラクティス

- MUST: レイテンシとデータ整合性を考慮した**マルチリージョン ウォーム・スタンバイ**構成でデプロイする（サンプルでは プライマリ=東京、セカンダリ=大阪、監視=オレゴン）。
- MUST: リージョン切り替え（アプリケーション閉塞、Aurora Global Database の昇格など）を AWS Step Functions で自動化し、約 5 分もしくはそれ以下の RTO を実現する。
- MUST: 切り替え用の Step Functions ステートマシンは、プライマリリージョンが機能低下していても確実に実行できるよう、**障害の影響を受けていないセカンダリリージョン（大阪）**で実行する。
- MUST: リージョン切り替えは Amazon Application Recovery Controller (ARC) で信頼性高く制御し、切り替えが DNS に依存するためオンプレミス側からの通信は Route 53 の名前解決を利用する。
- MUST: ランサムウェアがデータを暗号化・使用不可能とした場合の復旧手段として、AWS Backup によるバックアップを取得する。
- SHOULD: バックアップのボールトロックは**コンプライアンスモード**で作成し、保持期間終了までイミュータブルとする（サンプルは便宜上、十分な権限を持つ IAM ユーザーであれば削除可能なガバナンスモードで実装）。
- SHOULD: 大阪リージョンとオレゴンリージョンの CloudWatch Synthetics Canary から東京リージョンへ疑似トランザクションを発生させ、応答を確認する外形監視を実装する。
- SHOULD: CloudWatch Application Signals と CloudWatch Agent サイドカーを用いて、アプリケーションコードを変更せずに OpenTelemetry ベースの分散トレーシングを実現する。
- SHOULD: AWS WAF を Application Load Balancer に適用し、VPC エンドポイント、セキュリティグループによるネットワーク制御、IAM 最小権限アクセスを用いる。
- SHOULD: サイバーイベント発生時にワークロードを隔離するワークフローを実装する。
- SHOULD: 障害復旧時のレプリケーションラグは業務要件やアプリケーションの特性を踏まえて別途考慮する（両 DB とも通常は 1 秒以内にレプリケーションされる）。
- PREFER / MAY: 長年の実績と高い PostgreSQL 互換性を持つ Aurora PostgreSQL Global Database を優先する。同期レプリケーション・強整合性・Active-Active マルチリージョンが決定的に重要な場合は Aurora DSQL を実験的に採用してもよい（`references/architecture-dsql.md` を参照）。
- MAY: コンピューティング層は要件に合わせて Amazon ECS の代わりに Amazon EKS や Amazon EC2 を選択してもよい。
- MUST NOT: 提供される 2 つのサンプルアプリケーション（PHP ベースの ECS サンプルとマルチリージョン マイクロサービスアプリ）を同時にデプロイしてはならない。どちらか一方のみをデプロイする。
- WILL: 同一のマイクロサービスアプリが東京と大阪の両方にデプロイされる一方で、競合を避けるためトランザクションワーカーは東京リージョンでのみ稼働する。
- WILL: デプロイ時に（初期状態では無効化された）EventBridge Rule を有効化することで、大阪とオレゴンの監視 Canary がともに失敗となった場合に自動的にリージョン切り替えを行う。
- MUST: このスキルから構築する全ての CDK Stack に cdk-nag の AwsSolutionsChecks を Aspects で適用し、未抑制の AwsSolutions-* 検出が 0 件であることを CI テスト（jest 等）でゲートする。例外は NagSuppressions に reason を明記して抑制する（詳細は references/cdk-nag.md）。

### 主要コンポーネント

#### グローバルトラフィックルーター / DNS
- **コンポーネント概要**: プライマリ／セカンダリリージョン間のトラフィックをルーティングし、DNS ベースのリージョンフェイルオーバーの起点となる。オンプレミスの呼び出し元はこれを通じてアクティブなリージョンを解決する。
- **想定される AWS サービス**: Amazon Route 53（Private Hosted Zone 含む）、Amazon CloudFront、Amazon API Gateway（エッジ/API エントリ。CDK サンプルに全ては含まれない）。

#### リージョン間 / ハイブリッドネットワーク基盤
- **コンポーネント概要**: 3 つのリージョン同士とオンプレミスのデータセンターを閉域接続で結び、マルチリージョン運用と閉域アクセスを可能にする。
- **想定される AWS サービス**: AWS Transit Gateway（クロスリージョンピアリング）、AWS Direct Connect / DXGW（ハイブリッド部分。CDK サンプルには含まれない）、Amazon VPC。

#### アプリケーションコンピューティング（マイクロサービス）
- **コンポーネント概要**: 勘定系の業務ロジック（残高照会、預入れ、引落し、トランザクション制御）をコンテナ化されたマイクロサービスとして実行し、分散トランザクションの整合性を Saga パターンで保持する。
- **想定される AWS サービス**: Amazon ECS（既定）、オプションで Amazon EKS または Amazon EC2、Elastic Load Balancing (ALB)。

#### トランザクション / メインデータストア
- **コンポーネント概要**: 権威ある口座・取引データを格納し、整合性と災害対策のためリージョン間でレプリケーションする。
- **想定される AWS サービス**: Amazon Aurora Global Database (PostgreSQL)、または実験的な選択肢として Amazon Aurora DSQL（サーバーレス・分散・Active-Active）。

#### トランザクションステートストア
- **コンポーネント概要**: 分散トランザクションの状態（Saga オーケストレーション）を管理する。グローバルテーブル使用時はフェイルオーバー時に手動切り替えが不要である。
- **想定される AWS サービス**: Amazon DynamoDB（グローバルテーブル、PITR 有効化）。

#### リージョンフェイルオーバーオーケストレーター
- **コンポーネント概要**: アプリケーション閉塞、Aurora Global Database の昇格、DNS 切り替えという一連のリージョン切り替えを信頼性高く自動実行し、約 5 分の RTO を実現する。
- **想定される AWS サービス**: Amazon Application Recovery Controller (ARC)、AWS Step Functions、AWS Lambda、Amazon EventBridge。

#### 外形監視
- **コンポーネント概要**: プライマリリージョン外から疑似トランザクションによりアプリケーションの正常性を継続的に検証し、自動フェイルオーバーの判断材料とする。
- **想定される AWS サービス**: Amazon CloudWatch Synthetics Canary。

#### オブザーバビリティ
- **コンポーネント概要**: アプリケーションコードを変更することなく、マイクロサービス横断の包括的な監視・サービスマップ・分散トレーシングを提供する。
- **想定される AWS サービス**: Amazon CloudWatch Application Signals、CloudWatch Agent（サイドカー）、Amazon CloudWatch（メトリクス/ログ）。

#### イミュータブルバックアップ & サイバーレジリエンス
- **コンポーネント概要**: ランサムウェア耐性のあるイミュータブルなバックアップと、サイバーイベント向けの自動隔離・復旧機能を提供する。
- **想定される AWS サービス**: AWS Backup（ボールトロック、Logically air-gapped Vault）、Amazon ECR クロスリージョンレプリケーション、DynamoDB PITR、GuardDuty 起点の隔離（サンプルでは EventBridge + Lambda）。

## FISC 準拠サマリー

本ワークロードは FISC 安全対策基準（第 13 版）の実務基準に対してマッピングされている。マッピングでは、共通のガバナンスベーステンプレートがカバーする範囲、勘定系ワークロードテンプレート自体がカバーする範囲、使用者側の責任として残る範囲（主に業務アプリケーションのロジックと運用・開発プロセス）を区別している。

勘定系ワークロードテンプレートが直接対応する主なポイント:

- **可用性・災害対策（実 73〜実 88）**: マルチリージョン/マルチ AZ 構成、セカンダリリージョンの構築、高可用性の AWS マネージドサービスの利用。
- **リージョン切り替え・復旧（実 71、実 104）**: リージョン切り替え方針の解説、Step Functions による自動切り替え・切り戻し、サイバーイベント発生時の復旧方法の解説。
- **バックアップ・イミュータブル保護（実 39、実 73-1、実 106）**: AWS Backup、ボールトロック（サンプルはガバナンスモード）、Logically air-gapped Vault、DynamoDB PITR、ECR クロスリージョンレプリケーション。
- **暗号化（実 3、実 13、実 30、実 89）**: AWS KMS による暗号化と鍵管理。転送時 TLS は使用者側で実装。
- **監視・ロギング（実 10、実 46、実 72、実 101〜実 103）**: VPC フローログ、ALB アクセスログ、CloudWatch モニタリング、Canary 外形監視。
- **脅威・脆弱性対策（実 14、実 20、実 21、実 32）**: ALB への WAF、VPC エンドポイント、セキュリティグループ、ECR ベーシックスキャン、サイバーイベント時の自動隔離。

多くの項目は「対象外」（業務アプリケーション、運用プロセス、開発プロセス、または AWS クラウド側で対策済み）である。実 1 から実 153 まで（欠番の実 127〜実 131 を含む）のすべてのマッピングエントリは `references/fisc-mapping.md` に保持している。管理単位ごとの正式な詳細はそちらを参照。

## リファレンスアーキテクチャ

具体的な構成例を 1 つ示す（詳細は `references/architecture.md`、図は `assets/images/` を参照）:

- **3 リージョン**: 東京（`ap-northeast-1`、プライマリ）、大阪（`ap-northeast-3`、セカンダリ／ウォーム・スタンバイ）、オレゴン（`us-west-2`、監視）。
- **ネットワーク**: 各リージョンに VPC を配置し、Transit Gateway のクロスリージョンピアリングで接続。オンプレミスは Direct Connect で接続（ハイブリッド部分は CDK サンプルに含まれない）。Route 53 で DNS ベースのフェイルオーバーを提供。
- **コンピューティング**: ALB の背後に ECS マイクロサービス。ALB に WAF を適用。
- **データ**: メイン DB として Aurora Global Database (PostgreSQL)、トランザクションステート用に DynamoDB グローバルテーブル。両者とも通常は 1 秒以内にレプリケーション。
- **フェイルオーバー**: ARC + Step Functions が切り替えをオーケストレーションし RTO 約 5 分。ステートマシンは大阪で実行。大阪・オレゴンの Canary が EventBridge Rule を介して自動フェイルオーバーを駆動。
- **レジリエンス**: AWS Backup（ボールトロック）、DynamoDB PITR、ECR クロスリージョンレプリケーション、サイバーイベント向けの自動隔離ワークフロー。

留意すべき設計判断: レイテンシと整合性のバランスを取るため Aurora PostgreSQL による（Active-Active ではなく）ウォーム・スタンバイを採用する。トランザクションワーカーは競合回避のため東京のみで稼働する。切り替え自動化は障害の影響を受けていないリージョンから実行する。実験的な代替として、サーバーレス・分散・同期レプリケーション・Active-Active・強整合性を備える **Aurora DSQL** 版を `references/architecture-dsql.md` に提示し、そのトレードオフ（楽観的同時実行制御、トランザクションのサイズ/行数/実行時間/接続時間の制限、PostgreSQL 機能のサブセット）も併せて解説している。

## CDK サンプル概要

CDK サンプル（TypeScript）は `assets/sample-cdk/` 配下（ディレクトリ `guest-core-banking-sample`）にある。マルチリージョン勘定系のベースをプロビジョニングする: Route 53、Transit Gateway（デプロイ時にクロスリージョンピアリングの承認/ルート追加 CLI が Output される）、ELB、ECS、DynamoDB、Aurora Global Database、AWS Backup に加え、フェイルオーバー機構（ARC、Step Functions、Lambda）と CloudWatch Synthetics Canary の外形監視を含む。さらにサイバーレジリエンス関連スタック（自動隔離、データバンカーアカウント、リストア用 Step Functions）も含む。

2 種類のオプションのサンプルアプリケーションが同梱される（どちらか一方のみをデプロイ）:

1. PHP ベースの `amazon-ecs-sample` コンテナ（オプションの動作確認用 NLB あり）。
2. **マルチリージョン マイクロサービスアプリケーション**（TypeScript）。残高照会・預入れ・引落しを 4 つのサービス（transaction、balance、count、worker）で実装し、Saga パターンの補償トランザクションで整合性を保持する。東京・大阪間で実際にフェイルオーバー可能。

> **サンプルアプリのセキュリティに関する注意**: このマルチリージョン マイクロサービスアプリは、フェイルオーバー機構の動作確認のみを目的としたデモである。口座の識別は未認証の `x_account_id` ヘッダのみで行われ（署名・トークン検証なし）、ALB は平文 HTTP でリスンし、WAF のマネージドルールはブロックしない count モードでデプロイされ、`region-proxy` Lambda は allow-list 無しで任意の AWS API を実行できる。実際のトラフィックや実口座データに晒さないこと。ローカルデモの範囲を超えて流用する場合は、認証・TLS・WAF のブロックモード・入力の allow-list を必ず実装すること。同じ注意書きは CDK ツリー内 `assets/sample-cdk/SECURITY_NOTICE.md` にも同梱され、`cdk synth` / `cdk deploy` のたびに警告として表示される。

CDK は 3 つのスタックを順にデプロイする: `BLEAFSI-CoreBanking-primary-*`、`-secondary-*`、`-monitoring-*`。各スタックはスタック Output として出力される Transit Gateway ピアリングの承認・ルート追加 CLI コマンドの手動実行を要する。手順の全体は `references/deployment.md`、マイクロサービスアプリの詳細は `references/multi-region-app.md`、デプロイ時の Docker エラー対応は `references/sample-app-workaround.md` を参照。コピーされた `assets/sample-cdk/test/*.test.ts` が cdk-nag 強制パターンの一次情報であり、抽出した抑制ルール台帳と下流向けの強制ガイダンスは `references/cdk-nag.md` にまとめている。
