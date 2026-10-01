# ⚠️ Security Notice / セキュリティに関する注意 — fsi-foundation-governance-base guest sample CDK

## English

This is the **security governance baseline** (Control Tower / Organizations) — its
detective controls, audit logging, and guardrails are the product, and most
threats are already mitigated. The items below are **residual, downstream-owned
decisions**, not defects in the baseline itself. Treat the bundled IAM roles as a
**starting point to be narrowed**, not as production roles.

### Residual — decide before production

| STRIDE category | Item | Recommended action |
|-----------------|------|--------------------|
| Information Disclosure + Elevation of Privilege | IAM sample roles are intentionally broad (SysAdmin `NotAction: iam:*`, InstanceOps `ec2:*` without an MFA condition, ReadOnlyAdmin `s3:Get*`/`dynamodb:*` on `Resource:*`). | Narrow to least privilege and add an MFA condition to InstanceOps before production. |
| Repudiation | CloudTrail S3 data-event recording is commented out (off) by default. | Enable S3 data events for buckets holding user data (FISC practical-standard expectation). |
| Denial of Service | The default-SG auto-remediation runs with `automatic: true` and can cause connectivity loss if mis-triggered. | Consider manual remediation or environment-specific gating. |
| Spoofing + Denial of Service | The security notification email defaults to a placeholder and requires SNS subscription confirmation; the `AWSControlTowerBlueprintAccess` role must be created only under `AWSControlTowerExecution`. | Set and confirm a real email; follow the AFC blueprint-role MUST NOT rule. |
| Information Disclosure | The security-alarm SNS topic (`SecurityAlarm`) is unencrypted (no CMK); it is created in every deployment. This is a reference-implementation choice (cdk-nag suppressed as "SNS encryption is an option"), not an oversight. | Evaluate and add CMK encryption (`masterKey`) to this SNS topic before production use, based on your own data-sensitivity requirements. |

This notice lists residual decisions only; perform your own full threat review
before production use.

---

## 日本語

これはセキュリティ**ガバナンスベース**（Control Tower / Organizations）であり、検出的統制・監査ログ・
ガードレールそのものが成果物で、脅威の多くは既に緩和済みです。以下は基盤の欠陥ではなく、**下流で
判断すべき残存事項** です。同梱の IAM ロールは本番ロールではなく **絞り込むための出発点** として扱ってください。

### Residual — 本番前に判断すべき残存事項

| STRIDE 分類 | 事項 | 推奨対応 |
|-------------|------|----------|
| 情報漏えい + 権限昇格 | IAM サンプルロールが意図的に広い（SysAdmin の `NotAction: iam:*`、MFA 条件の無い InstanceOps の `ec2:*`、ReadOnlyAdmin の `s3:Get*`/`dynamodb:*` を `Resource:*` で許可）。 | 本番前に最小権限へ絞り、InstanceOps に MFA 条件を追加する。 |
| 否認 | CloudTrail の S3 データイベント記録が既定でコメントアウト（オフ）になっている。 | ユーザーデータを格納するバケットで S3 データイベントを有効化する（FISC 実務基準の想定）。 |
| サービス妨害 | デフォルト SG の自動修復が `automatic: true` で実行され、誤発火時に通信断を招きうる。 | 手動修復、または環境別のゲートを検討する。 |
| なりすまし + サービス妨害 | セキュリティ通知メールが既定でプレースホルダであり SNS 購読確認が必要。また `AWSControlTowerBlueprintAccess` ロールは `AWSControlTowerExecution` 配下でのみ作成する必要がある。 | 実在のメールを設定・確認し、AFC ブループリントロールの MUST NOT 規約を遵守する。 |
| 情報漏えい | セキュリティアラーム用 SNS Topic（`SecurityAlarm`）が CMK 未暗号化。毎回のデプロイで必ず作成される。リファレンス実装としての判断（cdk-nag で `SNS encryption is an option` として抑制済み）であり、見落としではない。 | 本番利用前に、自身のデータ機密性の要件に照らして、この SNS Topic への CMK 暗号化（`masterKey`）の要否を検討し、必要に応じて実装する。 |

本注意書きは残存事項のみを挙げている。本番利用前に、自身の構成に対して脅威分析を実施すること。
