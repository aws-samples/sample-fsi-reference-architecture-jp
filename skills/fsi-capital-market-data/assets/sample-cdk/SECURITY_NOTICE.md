# ⚠️ Security Notice / セキュリティに関する注意 — fsi-capital-market-data sample CDK

## English

This CDK sample is a **reference / functional demo, NOT production-ready code.**
It demonstrates a low-latency market-data pipeline (Handler / Composer /
Distributor over Kinesis). At-rest encryption (KMS CMK), Multi-AZ, and a cdk-nag
CI gate are in place, but the **sample deliberately leaves authentication, TLS,
entitlement, and least-privilege roles to the implementer.** Because false or
stale prices can cause erroneous trades and financial loss, do not use this
sample for real feeds before addressing the items below.

### Critical / High — must fix before real use

| STRIDE category | Threat | Required action |
|-----------------|--------|-----------------|
| Spoofing | No provider/subscriber peer authentication; the described authentication Lambda is not wired; the Distributor ALB listens on plain HTTP with `open:true`. | Implement mutual auth (mTLS / API key / FIX Logon SenderCompID) and wire the Authorization-header validation Lambda. |
| Tampering + Information Disclosure | Plain-HTTP edge and broad `0.0.0.0/0` egress allow tampering and disclosure of proprietary feeds in transit. | Terminate HTTPS (443) with ACM, restrict listener source, and minimize egress to required destinations. |
| Information Disclosure | No per-subscriber entitlement (authz): any reachable client can retrieve feeds/symbols it is not licensed for. | Enforce per-subscriber symbol/feed authorization and consumer access logging. |
| Repudiation + Elevation of Privilege | All three tiers share one task role granting `kinesis:PutRecord`/read on `stream/*`; a compromised Distributor can write upstream. | Split into per-tier roles scoped to each stream ARN; give the Distributor `GetRecords` only. |
| Tampering + Elevation of Privilege | Container base image is pulled without a pinned digest, the ECR tag is mutable, and CodeBuild runs privileged. | Pin the base image by digest, use an immutable version tag, enable ECR scanning, and run tasks non-root/read-only. |
| Denial of Service | No input rate control / freshness SLA; Kinesis shard & DynamoDB capacity can be exhausted, stalling feeds. | Add rate limiting, shard/capacity scaling, and feed-freshness monitoring with integrity-checked fallbacks. |

This notice covers the highest-severity items only; perform your own full threat
review before production use.

---

## 日本語

この CDK サンプルは **リファレンス／動作デモであり、本番利用可能なコードではありません。**
低レイテンシのマーケットデータ配信（Handler / Composer / Distributor を Kinesis で疎結合）を示します。
保存時暗号化（KMS CMK）・Multi-AZ・cdk-nag CI ゲートは備わりますが、**認証・TLS・エンタイトルメント・
最小権限ロールは意図的に実装者に委ねられています。** 誤った/陳腐化した価格は誤発注・取引損失に直結する
ため、以下を解消するまで実フィードに使用しないでください。

### Critical / High — 本番前必須対応

| STRIDE 分類 | 脅威 | 必要な対応 |
|-------------|------|-----------|
| なりすまし | プロバイダ／サブスクライバのピア認証が無く、記載されている認証 Lambda が未配線で、Distributor の ALB が平文 HTTP `open:true` でリスンしている。 | 相互認証（mTLS／API キー／FIX Logon の SenderCompID 検証）を実装し、Authorization ヘッダを検証する認証 Lambda を実際に配線する。 |
| 改ざん + 情報漏えい | 平文 HTTP のエッジと広域な `0.0.0.0/0` egress により、転送中の配信データの改ざん・漏えいが可能。 | ACM 証明書で HTTPS（443）を終端し、リスナの接続元を限定し、egress を必要な宛先へ最小化する。 |
| 情報漏えい | サブスクライバ単位のエンタイトルメント（認可）が無く、到達できるクライアントは契約外のフィード／銘柄も取得できる。 | サブスクライバ単位で銘柄／フィードの認可を強制し、消費者アクセスログを取得する。 |
| 否認 + 権限昇格 | 全 3 tier が `stream/*` に対し `kinesis:PutRecord`／読み取りを許可する単一のタスクロールを共有しており、侵害された Distributor が上流へ書き込める。 | tier ごとにロールを分離して各ストリーム ARN に限定し、Distributor には `GetRecords` のみを付与する。 |
| 改ざん + 権限昇格 | コンテナのベースイメージがダイジェスト未固定で取得され、ECR タグが可変、CodeBuild が privileged で実行される。 | ベースイメージをダイジェスト固定し、不変な version タグを使い、ECR スキャンを有効化し、タスクを非 root／読み取り専用で実行する。 |
| サービス妨害 | 入力レート制御／鮮度 SLA が無く、Kinesis シャードや DynamoDB キャパシティが枯渇して配信が停滞しうる。 | レート制御、シャード／キャパシティのスケーリング、完全性検証付きフォールバックによるフィード鮮度監視を実装する。 |

本注意書きは重大度の高い項目のみを挙げている。本番利用前に、自身の構成に対して脅威分析を実施すること。
