---
name: aws-security-guard
description: >
  AWS操作の事前セキュリティガード。AWS CLI/IaC操作の実行前にセキュリティリスクを検知し、理由と代替案を提示します。
  S3パブリック公開、SG全開放、IAM過剰権限、暗号化なし、CloudTrail無効化等を事前に警告します。
  AWSリソースの作成・変更・削除、AWS CLIコマンド実行、IaCコード生成・適用（CloudFormation/Terraform/CDK）時に発動します。
  トリガーキーワード: "AWS resource creation", "AWS CLI", "CloudFormation", "Terraform", "CDK",
  "S3 bucket", "security group", "IAM policy", "RDS", "EC2",
  "AWSリソース作成", "セキュリティグループ", "IAMポリシー".
license: MIT No Attribution
compatibility: 外部依存なし。プロンプトロジックのみで動作します。
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# AWS Security Guard

## このスキルを使用するタイミング

以下の場合にこのスキルを使用します:
- AWSリソースの作成・変更・削除
- AWS CLIコマンドの実行
- IaCコード（CloudFormation/Terraform/CDK）の生成・適用

## ワークフロー

### Step 1: 操作意図の解析

ユーザーの依頼から以下を特定します:
- 対象AWSサービス
- 操作の種類（作成/変更/削除）
- 影響を受けるリソースの範囲
- データの機密性レベル（個人情報・決済情報・機密情報の有無）

### Step 2: セキュリティリスク評価

以下のカテゴリでリスクを評価します:

**1. ネットワーク露出** [Critical/High]
- パブリックアクセス（0.0.0.0/0のインバウンド、インターネット公開）
- デフォルトSGの全ポート開放、NACLの過剰許可
- VPCピアリング/Transit Gatewayの無制限ルーティング
- SSH/RDP直接公開（踏み台/SSM未使用）
- EC2/ECS/EKSへのパブリックIP自動割り当て
- サブネットのパブリックIP自動割り当て有効
- IMDSv2未強制（IMDSv1許可）

**2. IAM・認証** [Critical]
- AdministratorAccess/PowerUserAccessの付与
- ワイルドカード（*）リソース指定のポリシー
- MFA未設定でのコンソールアクセス許可
- ルートアカウントのアクセスキー作成・使用
- 外部ID未設定のクロスアカウントAssumeRole
- IAMユーザーへの直接ポリシーアタッチ（グループ/ロール未使用）
- 全KMSキーへの復号アクションを許可するポリシー

**3. 暗号化・鍵管理** [High]
- 保存時暗号化なし（EBS/RDS/S3/EFS/DynamoDB/Kinesis/SQS/OpenSearch/Redshift）
- 転送時暗号化なし（SSL/TLS未強制）
- KMSキーローテーション無効
- KMSキーポリシーのワイルドカード/パブリックアクセス
- Secrets Manager未使用での平文シークレット管理
- シークレットの自動ローテーション未設定

**4. データ保護・共有** [Critical]
- S3バケットのパブリック公開（Block Public Access無効）
- S3バケットポリシーのワイルドカードPrincipal
- EBSスナップショット/AMIのパブリック共有
- RDS/DocumentDB/Neptuneスナップショットのパブリック共有
- バージョニング無効、MFA Delete未設定
- SSMドキュメントのパブリック共有
- SNS/SQSポリシーのパブリックアクセス許可

**5. ログ・監査** [High]
- CloudTrail無効化・削除
- マルチリージョンCloudTrail未設定
- CloudTrailログファイル検証無効
- S3サーバーアクセスログ未設定
- VPCフローログ無効化
- ALB/CLBアクセスログ未設定
- API Gatewayの実行ログ未設定
- RDS/Aurora監査ログのCloudWatch連携未設定

**6. 可用性・耐障害性** [Medium/High]
- Single-AZ構成（本番環境）
- バックアップ未設定/保持期間不足
- 削除保護（DeletionProtection）無効
- Auto Scalingでの単一インスタンスタイプ・単一AZ
- CloudFormationスタックの終了保護無効

**7. コンテナ・サーバーレス** [High]
- ECRイメージスキャン未設定
- ECRタグイミュータビリティ未設定
- Lambda環境変数に平文シークレット（Secrets Manager未使用）
- ECSタスクロールの過剰権限
- ECSコンテナのroot実行/特権モード
- ECSコンテナのルートファイルシステムが書き込み可能
- ECSタスク定義でのホストプロセス名前空間共有
- Lambda関数のパブリックURL公開（認証なし）
- Lambda関数の非サポートランタイム使用

**8. データベース** [High/Critical]
- RDS/Auroraのパブリックアクセス有効
- RDSのSSL/TLS未強制
- RDSのデフォルトポート使用
- RDSのデフォルト管理者ユーザー名使用
- RDSのIAM認証未設定
- RDSのパブリックサブネット配置（IGWルートあり）
- DynamoDBのポイントインタイムリカバリ無効
- ElastiCacheの認証なし・暗号化なし・デフォルトサブネットグループ使用
- OpenSearch/Elasticsearchのパブリックアクセス・fine-grained access control未設定
- Redshiftのデフォルト管理者ユーザー名・Enhanced VPC routing未設定

**9. API・エンドポイント** [High]
- API Gatewayの認証なしエンドポイント
- API Gatewayキャッシュデータの暗号化なし
- CloudFrontのHTTP許可（HTTPS未強制）
- CloudFrontのOAC未使用（OAI使用またはダイレクトS3アクセス）
- CloudFrontの非推奨TLSポリシー/SSLプロトコル使用
- WAF未設定でのパブリックAPI/CloudFront公開
- ALBのHTTP→HTTPSリダイレクト未設定
- CORS設定のワイルドカードオリジン
- Transfer FamilyでのFTPプロトコル使用（SFTP/FTPS未使用）



### Step 3: 出力フォーマット

重大度は以下の4段階で判定します:
- **Critical**: データ漏洩・全世界公開・ルートアカウント操作など、即座に重大インシデントに繋がるもの
- **High**: 暗号化欠如・過剰権限・監査証跡消失など、攻撃者に悪用されうるもの
- **Medium**: 可用性リスク・コスト爆発・ベストプラクティス逸脱など、運用上の問題
- **Low**: 推奨設定との差異・最適化余地など、即座の危険はないが改善すべきもの

リスクが検出された場合:

```
⚠️ セキュリティリスク検出

【リスク】[リスクの概要を1行で]
【理由】[なぜ危険かを具体的に説明]
【影響】[このまま実行した場合に起こりうる最悪のシナリオ]
【重大度】Critical / High / Medium / Low

✅ 代替案
[セキュリティを維持しつつ、ユーザーの目的を達成する代替構成を提案]

続行しますか？
1. 代替案で実行する
2. リスクを承知の上で元の操作を実行する
3. キャンセルする
```

リスクが検出されなかった場合:
```
✅ セキュリティチェック通過。この操作にリスクは検出されませんでした。実行します。
```

### Step 4: ユーザー判断の尊重

- ユーザーが「リスク承知で実行」を選んだ場合は、以下のログをファイル `security-guard.log` に追記した上で実行します
- 強制ブロックはしません。情報提供と判断支援を行います。
- ログファイルが存在しない場合は新規作成します。

ログフォーマット:
```
[RISK ACCEPTED] [日時] | 重大度: [Critical/High/Medium/Low] | リスク: [リスク概要] | 操作: [実行した操作の要約]
```




