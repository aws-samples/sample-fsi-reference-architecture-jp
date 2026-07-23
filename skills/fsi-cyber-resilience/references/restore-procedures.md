# サイバーレジリエンス 復旧手順書

本書は BLEA for FSI「サイバーレジリエンス」アセットの復旧手順書である。

## 概要

本ドキュメントは、サイバーインシデント発生時のシステム復旧手順を説明する。
復旧は 3 つの段階で実施される。

1. **Resource Access Manager (RAM) 共有設定**（手作業）
2. **データベース復旧**（CDK StepFunctions 自動化）
3. **ワークロード再接続**（手作業）

## 前提条件

### 必要なソフトウェア

- AWS CLI v2
- Node.js 18.0.0 以上
- AWS CDK v2.95.1 以上

### アカウント構成

- **データバンカーアカウント**: バックアップデータを保管
- **リストアアカウント**: 復旧作業を実行

### 必要な権限

- データバンカーアカウント: RAM 共有権限
- リストアアカウント: 必要最小権限

## 初期セットアップ

### 1. パラメータ設定

fsi-banking-core スキルの `assets/sample-cdk/bin/parameter.ts`（作業ディレクトリにコピーしたもの）を
編集して、以下の項目を環境に合わせて変更すること。

```typescript
export const CyberResilienceParameter = {
  // デプロイする場合は true に指定
  deploy: true,
  // どの機能をデプロイか選択
  option: ['restore'] as ('backup' | 'restore' | 'isolation')[],

  // リストアアカウントの設定
  restoreAccount: {
    // リストアアカウントID
    id: '123456789012',
    // リストアリージョン
    region: 'ap-northeast-1',
  },
};
```

### 2. CDK 復旧システムデプロイ

```bash
# fsi-banking-core スキルの assets/sample-cdk を作業ディレクトリにコピーした場所へ移動
cd <fsi-banking-core>/assets/sample-cdk
npm install
npx cdk deploy BLEAFSI-CoreBanking-restore-Dev
```

**注意**: 初回デプロイ時は勘定系ワークロードは含まれない（復旧用 Step Functions のデプロイのみ）。

### データバンカーアカウントで RAM 共有リクエスト

データバンカーアカウントのマネジメントコンソールにて **AWS Resource Access Manager** を開き、
**リソースの共有** を選択する。

**リソース共有を作成** 画面にて、リソース共有の名前を入力する。また、リソースタイプとして
**バックアップボールト** を選択し、リストアアカウントへ共有する AWS Backup の Logically air-gapped
vault を、そして選択されたリソースに共有するリソース ID を選択する。（バックアップ手順書参照）

![restore-procedures1](../assets/images/restore-procedures1.png)

アクセス許可はデフォルトのものを設定した上で、ステップ 3 にて共有先アカウントを設定する。
共有するリストアアカウントが同じ Organizations 内であれば、「自分の組織内でのみ共有を許可」を
プリンシパルとして設定し、アカウント ID を入力する。

![restore-procedures2](../assets/images/restore-procedures2.png)

確認まで完了したら、「自分と共有」というリソース内の共有ステータスが「保留中」となる。

![restore-procedures3](../assets/images/restore-procedures3.png)

### リストアアカウントで RAM 共有承認

リストアアカウントのマネジメントコンソールにて **AWS Resource Access Manager** を開き、「自分と
共有」リソース内に承認待ちステータスのリソースがあるため、「リソース共有を承認」をクリックする。
これで、RAM による共有が完了した。

![restore-procedures4](../assets/images/restore-procedures4.png)

## 復旧手順

### データベース復旧

初期セットアップにてデプロイした StepFunctions によるデータベースの復旧を行う。

#### 1-1. 復旧開始

```bash
# 環境変数設定
export ENVIRONMENT="Development"  # または Production
export STATE_MACHINE_NAME="cyber-resilience-restore-${ENVIRONMENT}"

# StepFunctions実行
EXECUTION_ARN=$(aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:ap-northeast-1:$(aws sts get-caller-identity --query Account --output text):stateMachine:${STATE_MACHINE_NAME}" \
  --name "restore-$(date +%Y%m%d-%H%M%S)" \
  --input '{
    "aurora_recovery_point_arn": "YOUR_AURORA_RECOVERY_POINT_ARN",
    "aurora_target_cluster_name": "restored-aurora-cluster",
    "dynamodb_recovery_point_arn": "YOUR_DYNAMODB_RECOVERY_POINT_ARN",
    "dynamodb_target_table_name": "restored-dynamodb-table"
  }' \
  --query 'executionArn' --output text)
```

### ワークロード再接続（手作業）

#### 2-1. 復旧リソース情報確認

```bash
# リストアされたDB情報を確認
aws rds describe-db-clusters \
  --db-cluster-identifier restored-aurora-cluster \
  --query 'DBClusters[0].{Endpoint:Endpoint,Status:Status}' \
  --output table

aws dynamodb describe-table \
  --table-name restored-dynamodb-table \
  --query 'Table.{TableName:TableName,Status:TableStatus}' \
  --output table
```

#### 2-2. 勘定系ワークロードデプロイ設定変更

```bash
# parameter.tsのバックアップ作成
cp <fsi-banking-core>/assets/sample-cdk/bin/parameter.ts \
   <fsi-banking-core>/assets/sample-cdk/bin/parameter.ts.backup

# 手動編集: <fsi-banking-core>/assets/sample-cdk/bin/parameter.ts
# SampleEcsAppParameter.deploy を false から true に変更
```

#### 2-3. 勘定系ワークロード新規デプロイ

```bash
# parameter.ts更新確認
# fsi-banking-core スキルの assets/sample-cdk を作業ディレクトリにコピーした場所へ移動
cd <fsi-banking-core>/assets/sample-cdk
npx cdk deploy --all

# ALBエンドポイント確認
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(LoadBalancerName,`CoreBanking`)].DNSName' \
  --output text
```

#### 2-4. 接続確認

```bash
ALB_ENDPOINT=$(aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(LoadBalancerName,`CoreBanking`)].DNSName' \
  --output text)

curl -I http://$ALB_ENDPOINT/
```
