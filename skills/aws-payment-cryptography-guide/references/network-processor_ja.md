# ネットワークスイッチ / 決済プロセッサーガイド

## 概要

ネットワークスイッチおよび決済プロセッサーは、アクワイアラとイシュアの間で
大量のトランザクションをルーティングします。AWS Payment Cryptography は、
PIN変換、MAC検証/生成、鍵管理を、オンプレミスHSMフリートの管理負担なしに
提供します。

---

## Zone PIN 変換

### コンセプト

Zone PIN変換は決済スイッチの中核暗号化オペレーションです。PINブロックは
受信側Zone PIN Key（ZPK）で復号し、送信側ZPKで再暗号化します。
クリアテキストのPINは一切露出しません。

```
アクワイアラ → [ZPK-A暗号化PIN] → スイッチ → [ZPK-I暗号化PIN] → イシュア
```

**API呼び出し: TranslatePinData**

```json
{
  "IncomingWrappedKey": {
    "WrappedKeyMaterial": {
      "Tr31KeyBlock": "<KEK-Aでラップされたアクワイアラ側ZPK>"
    }
  },
  "OutgoingWrappedKey": {
    "WrappedKeyMaterial": {
      "Tr31KeyBlock": "<KEK-Iでラップされたイシュア側ZPK>"
    }
  },
  "IncomingTranslationAttributes": {
    "IsoFormat0": { "PrimaryAccountNumber": "4111111111111111" }
  },
  "OutgoingTranslationAttributes": {
    "IsoFormat4": { "PrimaryAccountNumber": "4111111111111111" }
  },
  "EncryptedPinBlock": "AC3B4C2E1F5D6A7B"
}
```

### 大規模Zone鍵管理

| 課題 | 解決策 |
|------|--------|
| 数千のZPKペア | 命名規則に基づくエイリアス（`alias/zpk-acquirer-{id}-{direction}`） |
| 頻繁な鍵ローテーション | EventBridge + Lambda による有効期限トリガー自動化 |
| 鍵同期 | 接続エンティティとのローテーションウィンドウ調整 |
| 鍵階層 | 接続エンティティごとのKEK関係維持 |

---

## MACスイッチング

### 検証後生成パターン

```python
import boto3
client = boto3.client('payment-cryptography-data')

def switch_mac(incoming_msg, incoming_mac, incoming_key_id, outgoing_key_id):
    # ステップ1: 受信MACの検証
    try:
        client.verify_mac(
            KeyIdentifier=incoming_key_id,
            MessageData=incoming_msg,
            Mac=incoming_mac,
            VerificationAttributes={'Algorithm': 'ISO9797_ALGORITHM3', 'MacLength': 8}
        )
    except client.exceptions.VerificationFailedException:
        raise Exception("MAC検証失敗 - メッセージ完全性が損なわれています")
    
    # ステップ2: 送信MACの生成
    response = client.generate_mac(
        KeyIdentifier=outgoing_key_id,
        MessageData=incoming_msg,
        GenerationAttributes={'Algorithm': 'ISO9797_ALGORITHM3', 'MacLength': 8}
    )
    return response['Mac']
```

### MAC鍵の構成

N個のエンティティに接続するスイッチの場合：
- N個のインバウンドMAC鍵（送信者ごとに1つ）
- N個のアウトバウンドMAC鍵（受信者ごとに1つ）
- 命名規則: `alias/mac-{entity-id}-{inbound|outbound}`

---

## 高スループット設計

### デフォルトクォータ

| オペレーション | デフォルトTPS | 備考 |
|--------------|-------------|------|
| データプレーン（対称鍵） | 500 | 対称鍵を使うデータプレーン操作全体の合算（例: TranslatePinData, GenerateMac, VerifyMac） |
| データプレーン（非対称鍵） | 20 | 非対称鍵を使うデータプレーン操作全体の合算 |
| コントロールプレーン操作 | 5 | コントロールプレーン操作全体の合算（例: CreateKey, ImportKey, DeleteKey） |

クォータはアカウント・リージョンごとに適用され、Service Quotas で引き上げを申請できます。最新の値は [Quotas for AWS Payment Cryptography](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/quotas.html) で確認してください。

### リージョン間の水平スケーリング

```
              ┌──────────────┬──────────────┐
              │              │              │
     ┌────────▼───┐  ┌──────▼─────┐  ┌────▼────────┐
     │ us-east-1  │  │ eu-west-1  │  │ap-northeast-1│
     │  500 TPS   │  │  500 TPS   │  │  500 TPS    │
     └────────────┘  └────────────┘  └─────────────┘
                   合計: 1,500 TPS
```

### レイテンシー最適化

- **VPCエンドポイント**: PrivateLinkでインターネットホップを排除
- **コネクションプーリング**: HTTPS接続の再利用（keep-alive）
- **リージョンアフィニティ**: 最寄りリージョンへのルーティング
- **ペイロード最小化**: 必要なフィールドのみ送信

```python
from botocore.config import Config
config = Config(
    max_pool_connections=50,
    connect_timeout=5,
    read_timeout=10,
    retries={'max_attempts': 2, 'mode': 'adaptive'}
)
client = boto3.client('payment-cryptography-data', config=config)
```

---

## マルチリージョンアーキテクチャ

### マルチリージョンキーによるアクティブ-アクティブ

```
リージョンA（プライマリ）               リージョンB（セカンダリ）
┌──────────────────────┐             ┌──────────────────────┐
│  APC エンドポイント    │             │  APC エンドポイント    │
│  MRK: mrk-abc123    │◄───同期────►│  MRK: mrk-abc123    │
│  (同一鍵マテリアル)    │             │  (同一鍵マテリアル)    │
└──────────────────────┘             └──────────────────────┘
```

### フェイルオーバー設計

1. **ヘルスチェック**: CloudWatch経由でリージョンごとのAPCエンドポイント監視
2. **自動フェイルオーバー**: Route 53ヘルスベースルーティングでトラフィック切替
3. **鍵の可用性**: MRKはフェイルオーバー中の暗号化の継続性を維持するよう設計されています
4. **状態管理**: DynamoDB Global Tablesにトランザクション状態を保存

### データ主権に関する考慮事項

- データ主権の義務がある場合は単一リージョン鍵を使用
- 接続エンティティごとの鍵所在地要件を文書化
- 規制対象/非対象トラフィックに対して別個の鍵階層を検討

---

## 大規模鍵管理

### スケールプロファイル

500接続のスイッチの場合：**約2,000以上のアクティブ鍵**
- アクワイアラ/イシュア接続ごとに1つのZPKペア
- 接続エンティティごとに1つのMAC鍵ペア
- 接続エンティティごとに1つのKEK

### 鍵ローテーション自動化

```python
import boto3, json
events = boto3.client('events')

def schedule_key_rotation(key_alias, rotation_days=90):
    rule_name = f"key-rotation-{key_alias.replace('/', '-')}"
    events.put_rule(
        Name=rule_name,
        ScheduleExpression=f"rate({rotation_days} days)",
        State='ENABLED'
    )
    events.put_targets(Rule=rule_name, Targets=[{
        'Id': 'rotation-handler',
        'Arn': 'arn:aws:lambda:region:account:function:key-rotator',
        'Input': json.dumps({'key_alias': key_alias})
    }])
```

### エイリアス管理と鍵ライフサイクル

```
alias/zpk-{entity_type}-{entity_id}-{direction}-{version}
  例: alias/zpk-acquirer-network-a-inbound-v2
      alias/mac-processor-partner-a-inbound-v3
```

| フェーズ | アクション | 自動化 |
|---------|----------|--------|
| 生成 | 適切な属性で鍵を作成 | Lambda + Step Functions |
| 配布 | TR-31ラップブロックで交換 | セキュアAPI / SFTP連携 |
| 有効化 | エイリアスを新しい鍵に更新 | 協調カットオーバーウィンドウ |
| ローテーション | 代替鍵を生成、交換を調整 | EventBridgeスケジュール |
| 無効化 | エイリアス削除、`StopKeyUsage` | 猶予期間（24-48時間） |
| 削除 | `DeleteKey`（待機期間3〜180日、デフォルト7日） | コンプライアンス駆動、承認必須 |

> **注意 — 削除は元に戻せません**: 待機期間が終了すると鍵とエイリアスは完全に削除され、
> 別のソースから再インポートできない限り、その鍵で保護されたデータ（保管中の PIN ブロックや暗号文など）は
> 復号・検証できなくなります。
> - 削除前に、その鍵に依存するデータ、エイリアス、利用中のパートナーを棚卸ししてください。
> - まず `StopKeyUsage` で鍵を無効化し、観察期間中に障害が発生しないことを確認してください。
> - 待機期間中（`DELETE_PENDING`）は `RestoreKey` で削除を取り消せます。
> - マルチリージョンのプライマリキーの削除をスケジュールすると、レプリカキーも削除されます。プライマリキーを復元した場合は、レプリケーションリージョンを再設定する必要があります。

---

## スロットリング緩和

### 指数バックオフによるリトライ戦略

```python
import time, random
from botocore.exceptions import ClientError

def call_with_retry(func, max_retries=5, base_delay=0.1):
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                time.sleep(random.uniform(0, delay))
            else:
                raise
```

### CloudWatch によるクォータ監視

**監視すべき主要メトリクス:**
- `ThrottledRequests` — クォータ上限への接近
- `SuccessfulRequests` — ベースライントランザクション量
- `Latency`（p50, p99）— パフォーマンス低下の兆候

**プレウォーミング:** 新リージョンではトラフィックを段階的に増加。
メンテナンス後の突発バーストを回避。鍵操作を時間ウィンドウに分散。

---

## まとめ

| 機能 | APC機能 | スケール考慮事項 |
|------|---------|----------------|
| PIN変換 | TranslatePinData | デフォルト500 TPS、マルチリージョン |
| MACスイッチング | VerifyMac + GenerateMac | トランザクションごとデュアルコール |
| 鍵管理 | エイリアス + TR-31 | 自動化ライフサイクル付き数千鍵 |
| 高可用性 | マルチリージョンキー | 自動フェイルオーバー付きアクティブ-アクティブ |
