# ⚠️ Security Notice / セキュリティに関する注意 — fsi-channel-contact-center sample CDK

## English

This CDK sample is a **reference / functional demo, NOT production-ready code.**
The infrastructure layer (private S3, HTTPS-only CloudFront, CloudFront WAF,
Cognito with self-signup disabled and a strong password policy) is reasonable,
but the bundled **call-monitoring sample deliberately omits object-level
authorization**. Do not expose it to real customer call data before addressing
the items below.

### High / Medium — must fix before real use

| STRIDE category | Threat | Required action |
|-----------------|--------|-----------------|
| Repudiation + Information Disclosure | No object-level authorization (BOLA/IDOR): any one authenticated agent can read ALL customers' transcripts, AI summaries, and compliance findings (known developer TODO). | Implement per-caller row-level authorization in the GraphQL resolvers (bind Cognito user ↔ agentId ↔ contactId); add access audit logging. |
| Elevation of Privilege | `bedrock:invokeModel` granted on `Resource:'*'` (any model). | Scope `invokeModel` to the specific model ARN(s) actually used. |
| Spoofing | Cognito MFA is not enforced; AppSync has an extra IAM auth mode that can bypass Cognito. | Enforce MFA (`Mfa.REQUIRED`) and remove the unused AppSync IAM auth mode. |
| Information Disclosure | DEBUG logs can emit transcripts/PII; the WAF default allow-list covers the entire IPv4/IPv6 space; DynamoDB/Cognito use `RemovalPolicy.DESTROY`. | Mask PII in logs, restrict the WAF allow-list to real CIDRs, and set `RemovalPolicy.RETAIN` for production. |

This notice covers the highest-severity items only; perform your own full threat
review before production use.

---

## 日本語

この CDK サンプルは **リファレンス／動作デモであり、本番利用可能なコードではありません。**
インフラ層（private S3・HTTPS-only CloudFront・CloudFront WAF・自己サインアップ無効かつ強パスワード
ポリシーの Cognito）は妥当ですが、同梱の **call-monitoring サンプルはオブジェクトレベル認可を
意図的に省略** しています。以下を解消するまで実際の顧客通話データに晒さないでください。

### High / Medium — 本番前必須対応

| STRIDE 分類 | 脅威 | 必要な対応 |
|-------------|------|-----------|
| 否認 + 情報漏えい | オブジェクトレベル認可が無い（BOLA/IDOR）。認証済みエージェント 1 人で全顧客の通話記録・AI 要約・コンプラ所見を閲覧できる（開発者 TODO に明記済み）。 | GraphQL resolver で呼び出し元 identity に基づく行レベル認可を実装する（Cognito ユーザー ↔ agentId ↔ contactId を紐付け）。閲覧監査ログも追加する。 |
| 権限昇格 | `bedrock:invokeModel` が `Resource:'*'`（全モデル）で付与されている。 | `invokeModel` を実際に利用するモデルの ARN に限定する。 |
| なりすまし | Cognito の MFA が強制されておらず、AppSync に Cognito を迂回しうる IAM 認証モードがある。 | MFA（`Mfa.REQUIRED`）を必須化し、不要な AppSync IAM 認証モードを削除する。 |
| 情報漏えい | DEBUG ログにトランスクリプト／PII が出力されうる。WAF の既定 allow-list が全 IPv4/IPv6 空間を許可し、DynamoDB/Cognito が `RemovalPolicy.DESTROY`。 | ログの PII をマスクし、WAF の allow-list を実 CIDR へ限定し、本番では `RemovalPolicy.RETAIN` にする。 |

本注意書きは重大度の高い項目のみを挙げている。本番利用前に、自身の構成に対して脅威分析を実施すること。
