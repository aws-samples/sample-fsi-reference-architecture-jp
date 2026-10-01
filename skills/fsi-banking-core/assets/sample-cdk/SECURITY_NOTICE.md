# ⚠️ Security Notice / セキュリティに関する注意 — fsi-banking-core sample CDK

## English

This CDK sample is a **reference / functional demo, NOT production-ready code.**
It demonstrates multi-region failover mechanics for a core banking (勘定系)
workload. The infrastructure layer (multi-region redundancy, Aurora/DynamoDB
Global, KMS encryption, cyber-resilience) is solid, but the bundled
**multi-region microservice sample application deliberately omits several
security controls** to keep the failover demo simple.

Do **not** expose this sample to real traffic or real account data. Add the
controls below before adapting it beyond a local demo.

### Critical / High — must fix before real use

| STRIDE category | Threat | Required action |
|-----------------|--------|-----------------|
| Spoofing + Information Disclosure | Accounts identified from an unauthenticated `x_account_id` header (no token/signature). | Wire real authentication (signed token / mTLS); verify account ownership on every request. |
| Spoofing + Information Disclosure | ALB listens on plain HTTP (port 80); inter-service traffic is `http://`. | Terminate HTTPS (443) with an ACM certificate; use TLS for inter-service calls. |
| Tampering + Information Disclosure + Elevation of Privilege | `region-proxy` Lambda executes arbitrary AWS API/endpoint with no allow-list (tampering / SSRF / privilege escalation). | Restrict service/action/endpoint to an allow-list; scope the role to least privilege. |
| Denial of Service | WAF managed rules deployed in count-only (non-blocking) mode. | Switch `overrideAction` from `count` to `none` (block) for at least SQLi / KnownBadInputs. |
| Denial of Service | Public port-80 "for-test" NLB enabled by default, bypassing WAF. | Set `createTestResource` to `false` (or remove the public test NLB). |
| Elevation of Privilege | Cyber-resilience Lambda/service roles (Aurora/DynamoDB restore, the backup service role, VPC-zone association, automated isolation) intentionally use broad managed policies (`AdministratorAccess`) and service-wide wildcards (`rds:*`, `dynamodb:*`, `route53:*`, `ec2:*`) to keep the disaster-recovery build flexible across environments. The SNS topics used for restore/isolation notifications are also unencrypted (no CMK). This is opt-in functionality (`CyberResilienceParameter.deploy` / `option` default to disabled) and is not created in a default deployment. | Scope each role to the specific actions and resource ARNs it needs before production use. If you enable `restore`/`isolation`, evaluate and add CMK encryption (`masterKey`) to these SNS topics before production use. |
| Information Disclosure | The monitoring-alarm SNS topic (`MonitorAlarm`) is unencrypted (no CMK); it is created in every deployment. This is a reference-implementation choice (cdk-nag suppressed as "SNS encryption is an option"), not an oversight. | Evaluate and add CMK encryption (`masterKey`) to this SNS topic before production use, based on your own data-sensitivity requirements. |

This notice covers the highest-severity items only; perform your own full threat
review before production use.

---

## 日本語

この CDK サンプルは **リファレンス／動作デモであり、本番利用可能なコードではありません。**
勘定系ワークロードのマルチリージョン フェイルオーバー機構を示すことが目的です。
インフラ層（マルチリージョン冗長・Aurora/DynamoDB Global・KMS 暗号化・サイバーレジリエンス）は
堅牢ですが、同梱の **マルチリージョン マイクロサービス サンプルアプリは、デモを単純にするため
いくつかのセキュリティ統制を意図的に省略** しています。実トラフィック・実口座データに晒さないでください。
ローカルデモの範囲を超えて流用する場合は、以下を必ず実装してください。

### Critical / High — 本番前必須対応

| STRIDE 分類 | 脅威 | 必要な対応 |
|-------------|------|-----------|
| なりすまし + 情報漏えい | 未認証の `x_account_id` ヘッダのみで口座を識別している（トークン／署名の検証なし）。 | 実際の認証（署名付きトークン／mTLS）を配線し、リクエストごとに口座の所有権を検証する。 |
| なりすまし + 情報漏えい | ALB が平文 HTTP（port 80）でリスンし、サービス間通信も `http://`。 | ACM 証明書で HTTPS（443）を終端し、サービス間通信も TLS 化する。 |
| 改ざん + 情報漏えい + 権限昇格 | `region-proxy` Lambda が allow-list 無しで任意の AWS API／エンドポイントを実行する（改ざん／SSRF／権限昇格）。 | service/action/endpoint を allow-list で制限し、ロールを最小権限に絞る。 |
| サービス妨害 | WAF のマネージドルールが count（非ブロック）モードでデプロイされている。 | 少なくとも SQLi / KnownBadInputs について `overrideAction` を `count` から `none`（block）へ変更する。 |
| サービス妨害 | 公開 port80 の「動作確認用」NLB が既定で有効になり、WAF を迂回する。 | `createTestResource` を `false` にする（または公開テスト NLB を撤去する）。 |
| 権限昇格 | サイバーレジリエンス関連の Lambda／サービスロール（Aurora/DynamoDB リストア、バックアップサービスロール、VPC-ゾーン関連付け、自動隔離）が、災害復旧構成の構築自由度を確保するため、意図的に広い管理ポリシー（`AdministratorAccess`）やサービス全体ワイルドカード（`rds:*`、`dynamodb:*`、`route53:*`、`ec2:*`）を使用している。リストア／隔離通知に使う SNS Topic も同様に CMK 未暗号化。これらはオプトイン機能（`CyberResilienceParameter.deploy`／`option` は既定で無効）であり、デフォルトデプロイでは作成されない。 | 本番利用前に、各ロールを実際に必要なアクション・リソース ARN に絞り込む。`restore`／`isolation` を有効化する場合は、本番利用前にこれらの SNS Topic への CMK 暗号化（`masterKey`）の要否を検討し、必要に応じて実装する。 |
| 情報漏えい | 監視アラーム用 SNS Topic（`MonitorAlarm`）が CMK 未暗号化。こちらは毎回のデプロイで必ず作成される。リファレンス実装としての判断（cdk-nag で `SNS encryption is an option` として抑制済み）であり、見落としではない。 | 本番利用前に、自身のデータ機密性の要件に照らして、この SNS Topic への CMK 暗号化（`masterKey`）の要否を検討し、必要に応じて実装する。 |

本注意書きは重大度の高い項目のみを挙げている。本番利用前に、自身の構成に対して脅威分析を実施すること。
