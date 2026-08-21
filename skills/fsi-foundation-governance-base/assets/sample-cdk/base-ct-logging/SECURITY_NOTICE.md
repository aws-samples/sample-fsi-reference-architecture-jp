# ⚠️ Security Notice / セキュリティに関する注意 — fsi-foundation-governance-base logging sample CDK

## English

This is the **aggregated logging baseline** (Log Archive). Its bucket policies,
KMS encryption, and 5-year lifecycle are the product. The item below is a
**residual hardening decision** for environments that require strong log
immutability.

### Residual — decide before production

| STRIDE category | Item | Recommended action |
|-----------------|------|--------------------|
| Tampering | The log bucket policy now denies both `s3:DeleteObject` and `s3:DeleteObjectVersion`, but Object Lock / MFA Delete are still not enabled on their own. | Where strong immutability is required, additionally enable Object Lock (compliance mode) and/or MFA Delete. |

This notice lists residual decisions only; perform your own full threat review
before production use.

---

## 日本語

これは**集約ログ基盤**（Log Archive）です。バケットポリシー・KMS 暗号化・5 年ライフサイクルそのものが
成果物です。以下は、強いログ不変性を要する環境向けの **残存ハードニング判断** です。

### Residual — 本番前に判断すべき残存事項

| STRIDE 分類 | 事項 | 推奨対応 |
|-------------|------|----------|
| 改ざん | ログバケットのポリシーは `s3:DeleteObject` と `s3:DeleteObjectVersion` の両方を Deny 済みだが、Object Lock / MFA Delete 自体は未設定である。 | 強い不変性が必要な場合は、追加で Object Lock（コンプライアンスモード）や MFA Delete を有効化する。 |

本注意書きは残存事項のみを挙げている。本番利用前に、自身の構成に対して脅威分析を実施すること。
