# ⚠️ Security Notice / セキュリティに関する注意 — fsi-banking-mobile sample CDK

## English

This CDK sample is a **reference / functional demo, NOT production-ready code.**
The infrastructure layer (WAF, KMS, Secrets Manager, private S3, PITR, bcrypt) is
hardened, but the **application layer contains Critical authorization defects.**
Do not deploy this for real accounts before addressing the items below.

### Critical / High — must fix before real use

| STRIDE category | Threat | Required action |
|-----------------|--------|-----------------|
| Tampering + Information Disclosure + Elevation of Privilege | Money transfer and balance/transaction queries trust a client-supplied accountId without verifying ownership (IDOR) — funds theft and mass PII disclosure. | On every account access, compare the input accountId against the authorizer context's owned account; reject mismatches. |
| Spoofing + Information Disclosure | The admin API uses `authorizationType: NONE` + an API key that is published in the frontend `config.json`; temporary passwords are stored in plaintext and returned by the API. | Add a real authorizer (IAM/Cognito) to admin routes, remove the API key from the client, and stop storing/returning plaintext temporary passwords. |
| Spoofing | The shared JWT util has a hardcoded default-secret fallback and the authorizer's `jwt.verify` does not pin the algorithm (algorithm-confusion). | Remove the default-secret fallback (fail closed) and pin `algorithms: ['HS256']`. |
| Information Disclosure | Handlers log bearer tokens, bcrypt hashes, and full events (PII) to CloudWatch. | Remove or mask sensitive fields from logs. |
| Spoofing | When a Core Banking System stack is deployed, `insertDefaultUsers` creates two demo users (USER001/USER002) with a hardcoded bcrypt hash for the known password `password123`, so anyone with the source can log in as them. | Remove `insertDefaultUsers` (or randomize/rotate the credentials) before any deployment reachable by real users. |

This notice covers the highest-severity items only; perform your own full threat
review before production use.

---

## 日本語

この CDK サンプルは **リファレンス／動作デモであり、本番利用可能なコードではありません。**
インフラ層（WAF・KMS・Secrets Manager・private S3・PITR・bcrypt）は堅牢ですが、**アプリケーション層に
Critical 級の認可欠陥** があります。以下を解消するまで実口座に対してデプロイしないでください。

### Critical / High — 本番前必須対応

| STRIDE 分類 | 脅威 | 必要な対応 |
|-------------|------|-----------|
| 改ざん + 情報漏えい + 権限昇格 | 送金と残高／取引照会が、クライアント指定の accountId を所有権検証せずに信頼している（IDOR）。資金の窃取と大量の PII 漏えいに直結。 | すべての口座アクセスで、入力された accountId を authorizer コンテキストの所有口座と照合し、不一致を拒否する。 |
| なりすまし + 情報漏えい | 管理 API が `authorizationType: NONE` ＋ フロントの `config.json` に露出した API キーで保護され、仮パスワードが平文で保存・API 返却される。 | 管理系ルートに実際の authorizer（IAM/Cognito）を付与し、API キーをクライアントから除去し、平文仮パスワードの保存・返却を廃止する。 |
| なりすまし | 共有 JWT ユーティリティに既定鍵フォールバックがハードコードされ、authorizer の `jwt.verify` がアルゴリズムを固定していない（アルゴリズム混同）。 | 既定鍵フォールバックを削除して fail-closed 化し、`algorithms: ['HS256']` を明示する。 |
| 情報漏えい | ハンドラが bearer トークン・bcrypt ハッシュ・全 event（PII）を CloudWatch に出力している。 | 機微なフィールドをログから除去またはマスクする。 |
| なりすまし | Core Banking System スタックをデプロイすると、`insertDefaultUsers` が既知パスワード `password123` の bcrypt ハッシュをハードコードしたデモユーザー（USER001/USER002）を作成するため、ソースを知る誰でもこれらのユーザーでログインできる。 | 実ユーザーがアクセス可能な環境にデプロイする前に `insertDefaultUsers` を削除する（または認証情報をランダム化・ローテーションする）。 |

本注意書きは重大度の高い項目のみを挙げている。本番利用前に、自身の構成に対して脅威分析を実施すること。
