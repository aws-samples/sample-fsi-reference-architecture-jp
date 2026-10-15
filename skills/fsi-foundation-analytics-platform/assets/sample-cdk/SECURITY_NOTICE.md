# ⚠️ Security Notice / セキュリティに関する注意 — fsi-foundation-analytics-platform sample CDK

## English

This CDK sample is a **reference / functional demo, NOT production-ready code.**
The infrastructure layer (IAM least-privilege scoping, SSE-KMS encryption, VPC,
CloudTrail/logging) is solid, but the bundled **Glue PySpark ETL scripts contain
a deliberately simplified data-masking approach** that does not meet a financial
data lake's requirements. Do not run this against real customer data before
addressing the items below.

### High / Critical — must fix before real use

| STRIDE category | Threat | Required action |
|-----------------|--------|-----------------|
| Information Disclosure | `reverse()` used as PII "masking" for CIF / account numbers is trivially reversible; masked values propagate to the BI-readable normalized/analytics layers and can be re-identified. | Replace `reverse()` with salted cryptographic hashing / deterministic tokenization / KMS encryption, or use Lake Formation column-level controls. Do not call `reverse()` "masking". |
| Tampering + Denial of Service | ETL deletes S3 prefixes unconditionally (no target allow-list, no idempotency, non-paginated list), risking mass deletion / inconsistency. | Validate target bucket/prefix against an allow-list, enable S3 versioning + lifecycle/backup, and make deletes idempotent. |
| Spoofing + Elevation of Privilege | Glue job args (`target_bucket_name` etc.) are used without validation and the Glue role grants `s3:DeleteObject` on the whole bucket. | Allow-list job args and scope `s3:DeleteObject` to the required prefix/condition. |
| Spoofing | QuickSight IAM/SAML auth and IP restriction are recommended (SHOULD) but not enforced by the sample. | Enforce QuickSight IAM/SAML auth, IP restrictions, and password rules for production. |
| Information Disclosure | The Glue-pipeline SNS topic (`CloudWatchAlarm`) is unencrypted (no CMK); it is created in every deployment. `CloudWatchAlarm` supports an optional `kmsKey` prop, but the caller does not pass one, so the unencrypted branch always runs. This is a reference-implementation choice (cdk-nag suppressed as "SNS encryption is an option"), not an oversight. | Pass an existing CMK (e.g. the Glue Data Catalog key) as `kmsKey`, or evaluate and add CMK encryption before production use. |

This notice covers the highest-severity items only; perform your own full threat
review before production use.

---

## 日本語

この CDK サンプルは **リファレンス／動作デモであり、本番利用可能なコードではありません。**
インフラ層（IAM 最小権限・SSE-KMS 暗号化・VPC・CloudTrail/ログ）は堅牢ですが、同梱の
**Glue PySpark ETL スクリプトのデータマスキングは意図的に簡略化** されており、金融データレイクの
要求水準を満たしません。以下を解消するまで実顧客データに対して実行しないでください。

### High / Critical — 本番前必須対応

| STRIDE 分類 | 脅威 | 必要な対応 |
|-------------|------|-----------|
| 情報漏えい | `reverse()` による CIF/口座番号の「マスキング」は自明に可逆で、BI が読み取れる normalized/analytics 層へ伝播し再識別される。 | `reverse()` を不可逆方式（ソルト付きハッシュ／決定性トークナイゼーション／KMS 暗号化）へ置換、または Lake Formation の列レベル制御を使用する。`reverse()` を「マスキング」と呼ばない。 |
| 改ざん + サービス妨害 | ETL がターゲット検証なしに S3 プレフィックスを無条件で一括削除する（allow-list・冪等性・ページネーションなし）。大量削除／不整合のリスク。 | ターゲットのバケット／プレフィックスを allow-list 検証し、S3 バージョニング＋ライフサイクル／バックアップを有効化し、削除を冪等にする。 |
| なりすまし + 権限昇格 | Glue ジョブ引数（`target_bucket_name` など）が未検証で、Glue ロールが `s3:DeleteObject` をバケット全体に許可している。 | ジョブ引数を allow-list 検証し、`s3:DeleteObject` を必要なプレフィックス／条件へ限定する。 |
| なりすまし | QuickSight の IAM/SAML 認証・IP 制限が推奨（SHOULD）止まりで、サンプルでは強制されていない。 | 本番では QuickSight の IAM/SAML 認証・IP 制限・パスワードルールを必須化する。 |
| 情報漏えい | Glue パイプライン用 SNS Topic（`CloudWatchAlarm`）が CMK 未暗号化。毎回のデプロイで必ず作成される。`CloudWatchAlarm` はオプションの `kmsKey` プロパティに対応しているが、呼び出し元が渡していないため常に非暗号化の分岐が実行される。リファレンス実装としての判断（cdk-nag で `SNS encryption is an option` として抑制済み）であり、見落としではない。 | 既存の CMK（例: Glue Data Catalog 用のキー）を `kmsKey` として渡す、または本番利用前に CMK 暗号化の要否を検討し実装する。 |

本注意書きは重大度の高い項目のみを挙げている。本番利用前に、自身の構成に対して脅威分析を実施すること。
