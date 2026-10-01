# ⚠️ Security Notice / セキュリティに関する注意 — fsi-foundation-openapi FAPI sample CDK

## English

This CDK sample (FAPI 1.0 Advanced profile: Keycloak on ECS Fargate + Aurora
MySQL + NLB) is a **reference / development-and-test demo, NOT production-ready
code.** At-rest encryption (KMS), Secrets Manager, and VPC Flow Logs are in
place, but — notably for a high-security open-banking profile — several
in-transit and authorization controls are relaxed. Do not use it for real
open-banking traffic before addressing the items below.

### High / Medium — must fix before real use

| STRIDE category | Threat | Required action |
|-----------------|--------|-----------------|
| Tampering + Information Disclosure | The Keycloak-to-Aurora DB link is plaintext (`useSSL=false`), so credentials/tokens/realm data can be sniffed or altered in-VPC — especially serious for a FAPI profile. | Set `useSSL=true` (with CA validation) and require TLS at the Aurora parameter group. |
| Information Disclosure | The DB security group allows the entire VPC CIDR on port 3306. | Restrict the SG source to the ECS task security group only. |
| Elevation of Privilege | mTLS / FAPI client authentication uses a loose Subject DN match and does not enforce `tls_client_auth` / strong signing, so certificate binding is nominal. | Enforce strict Subject DN matching, `tls_client_auth`, and PS256/ES256 signing with revocation checks. |
| Repudiation + Denial of Service | NLB does not preserve client IP and the public NACL allows all traffic, weakening attribution and the network attack surface. | Set `preserveClientIp: true` and restrict the public NACL to required ports/CIDRs. |
| Spoofing | `KC_HOSTNAME_STRICT=false` makes Keycloak derive its issuer/redirect URLs dynamically from the request's Host header (required because production mode refuses to start without either a fixed hostname or this flag, and no fixed public domain is known at synth time in this sample). A forged Host header could cause Keycloak to issue tokens/links bound to an attacker-controlled hostname. | Once the real public domain is set, set `KC_HOSTNAME` to that domain and `KC_HOSTNAME_STRICT=true` (or remove the override, since `true` is the default) so the hostname is fixed instead of derived from client input. |

This notice covers the highest-severity items only; perform your own full threat
review before production use.

---

## 日本語

この CDK サンプル（FAPI 1.0 Advanced プロファイル: Keycloak on ECS Fargate + Aurora MySQL + NLB）は
**リファレンス／開発・検証用デモであり、本番利用可能なコードではありません。** 保存時暗号化（KMS）・
Secrets Manager・VPC Flow Logs は備わりますが、高セキュリティのオープンバンキング profile であるにも
かかわらず、転送時・認可の統制がいくつか緩められています。以下を解消するまで実トラフィックに使用しないでください。

### High / Medium — 本番前必須対応

| STRIDE 分類 | 脅威 | 必要な対応 |
|-------------|------|-----------|
| 改ざん + 情報漏えい | Keycloak↔Aurora 間の DB リンクが平文（`useSSL=false`）で、資格情報・トークン・レルム設定が VPC 内で盗聴・改ざんされうる。FAPI profile では特に重大。 | `useSSL=true`（CA 検証付き）に設定し、Aurora パラメータグループで TLS を必須化する。 |
| 情報漏えい | DB セキュリティグループが VPC CIDR 全体からの 3306 番接続を許可している。 | 許可元を ECS タスクのセキュリティグループのみに限定する。 |
| 権限昇格 | mTLS / FAPI のクライアント認証が緩い Subject DN 照合を用い、`tls_client_auth`／強い署名を強制しないため、証明書バインディングが名目化している。 | 厳密な Subject DN 照合、`tls_client_auth`、PS256/ES256 署名と失効検証を強制する。 |
| 否認 + サービス妨害 | NLB が実クライアント IP を保持せず、public NACL が全トラフィックを許可しており、帰属特定を弱め攻撃面を広げている。 | `preserveClientIp: true` に設定し、public NACL を必要なポート／CIDR に限定する。 |
| なりすまし | `KC_HOSTNAME_STRICT=false` により、Keycloak はリクエストの Host ヘッダーから発行者（issuer）／リダイレクト URL を動的に導出する（本番モードは固定 hostname かこのフラグのいずれかが無いと起動できず、本サンプルでは synth 時点で確定した Public ドメインが存在しないため設定している）。Host ヘッダーを偽装されると、攻撃者が制御するホスト名に紐づいたトークン／リンクを Keycloak が発行してしまう可能性がある。 | 実際の Public ドメインが確定したら、`KC_HOSTNAME` にそのドメインを設定し、`KC_HOSTNAME_STRICT=true`（既定値のため、この上書き自体を削除してもよい）として、hostname をクライアント入力から導出せず固定する。 |

本注意書きは重大度の高い項目のみを挙げている。本番利用前に、自身の構成に対して脅威分析を実施すること。
