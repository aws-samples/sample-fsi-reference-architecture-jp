# ⚠️ Security Notice / セキュリティに関する注意 — fsi-foundation-openapi base sample CDK

## English

This CDK sample (Cognito + API Gateway + CloudFront + WAF) is a **reference /
verification demo, NOT production-ready code.** In-transit edge encryption
(CloudFront HTTPS-only, S3 enforceSSL) and Secrets Manager usage are in place,
but several controls are deliberately relaxed for verification convenience. Do
not use it for a real open API before addressing the items below.

### High / Medium — must fix before real use

| STRIDE category | Threat | Required action |
|-----------------|--------|-----------------|
| Tampering + Denial of Service | All WAF managed rules run in count-only (non-blocking) mode and there is no rate-based rule, so SQLi / KnownBadInputs pass through and the app layer is exposed to DoS. | Change each `overrideAction` from `count` to `none` (block) and add a `rateBasedStatement`. |
| Spoofing + Elevation of Privilege | Cognito enables `USER_PASSWORD_AUTH` / `adminUserPassword` with MFA optional, enabling password brute-force and admin password override. | Disable those flows (use SRP), require MFA, and avoid `admin-set-user-password --permanent` in production. |
| Spoofing | When API Gateway is the resource server, mTLS client-certificate revocation (CRL/OCSP) is not checked. | Add a Lambda Authorizer that validates certificate revocation. |
| Information Disclosure | The verification script `tool/get_token.sh` echoes ID tokens to stdout with unquoted variables. | Avoid printing tokens, quote variables, and use temporary (not permanent) passwords. |

This notice covers the highest-severity items only; perform your own full threat
review before production use.

---

## 日本語

この CDK サンプル（Cognito + API Gateway + CloudFront + WAF）は **リファレンス／検証用デモであり、
本番利用可能なコードではありません。** エッジの転送時暗号化（CloudFront HTTPS-only・S3 enforceSSL）や
Secrets Manager 利用は備わりますが、いくつかの統制は検証容易性のため意図的に緩められています。
以下を解消するまで実際のオープン API に使用しないでください。

### High / Medium — 本番前必須対応

| STRIDE 分類 | 脅威 | 必要な対応 |
|-------------|------|-----------|
| 改ざん + サービス妨害 | WAF のマネージドルールが全て count（非ブロック）モードで、レートベースルールも無いため、SQLi / KnownBadInputs が素通りし、アプリ層が DoS に晒される。 | 各 `overrideAction` を `count` から `none`（block）へ変更し、`rateBasedStatement` を追加する。 |
| なりすまし + 権限昇格 | Cognito が `USER_PASSWORD_AUTH` / `adminUserPassword` を有効化し MFA が任意のため、パスワード総当たりや管理者によるパスワード上書きが可能。 | これらのフローを無効化（SRP を使用）し、MFA を必須化し、本番では `admin-set-user-password --permanent` を避ける。 |
| なりすまし | API Gateway をリソースサーバーとする場合、mTLS のクライアント証明書失効（CRL/OCSP）が検証されない。 | 証明書失効を検証する Lambda Authorizer を追加する。 |
| 情報漏えい | 検証用スクリプト `tool/get_token.sh` が ID トークンを非クオートの変数で stdout に出力する。 | トークンの出力を避け、変数をクオートし、恒久ではなく一時パスワードを使用する。 |

本注意書きは重大度の高い項目のみを挙げている。本番利用前に、自身の構成に対して脅威分析を実施すること。
