# AWS Payment Cryptography — よくある質問（FAQ）

## 1. 概要

### Q1: AWS Payment Cryptography（APC）とは何ですか？

AWS Payment Cryptography は、専用の決済用 HSM（Hardware Security Module）ハードウェアをプロビジョニング・管理・保守することなく、決済用 HSM の機能を提供するフルマネージドサービスです。カード発行系の処理（PIN 生成、CVV 生成、ARQC 検証）、アクワイアリング系の処理（PIN 変換、MAC 検証）、および鍵管理を、オンプレミスの決済用 HSM と同じ暗号アルゴリズムを用いて、すべて API 呼び出しで実行します。

> 📖 [AWS Payment Cryptography ドキュメント](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/what-is.html)

---

### Q2: APC は AWS CloudHSM や AWS KMS とどう違いますか？

| 観点 | APC | CloudHSM | KMS |
|--------|-----|----------|-----|
| **目的** | 決済特化の暗号操作（PIN、CVV、ARQC、MAC） | 汎用 HSM（PKCS#11、JCE、CNG） | 汎用のエンベロープ暗号化と鍵管理 |
| **コンプライアンス** | PCI PIN、PCI P2PE、PCI DSS | FIPS 140-2 Level 3 | FIPS 140-2 Level 3 |
| **鍵タイプ** | TDES、AES、RSA、ECC（決済特化フォーマット） | 幅広いアルゴリズムをサポート | 対称・非対称（AES、RSA、ECC） |
| **管理** | フルマネージド（ハードウェアのプロビジョニング不要） | お客様管理のクラスタ | フルマネージド |
| **ユースケース** | カード決済、POS トランザクション | カスタム暗号アプリ、TLS オフロード、PKI | アプリケーションレベルの暗号化、S3/EBS/RDS |

APC は決済業界向けに特化して設計されており、KMS や CloudHSM がネイティブにサポートしない決済標準の操作（ISO 9564、ISO 16609、EMV）を実装しています。

---

### Q3: APC はどの暗号アルゴリズムと操作をサポートしていますか？

**対称鍵アルゴリズム:**
- TDES（2 鍵および 3 鍵）— PIN ブロック、MAC、レガシー鍵交換
- AES-128、AES-192、AES-256 — PIN ブロック（ISO フォーマット 4）、CMAC、鍵ラッピング

**非対称鍵アルゴリズム:**
- RSA 2048/3072/4096 — TR-34 鍵交換、鍵ラッピング
- ECC（NIST P-256、P-384、P-521）— Select PIN フロー向けの ECDH 鍵合意

**操作:**
- PIN の生成・検証・変換（ISO フォーマット 0〜4）
- CVV/CVV2/iCVV の生成・検証
- ARQC/ARPC（EMV）の生成・検証
- MAC の生成・検証（ISO 9797、CMAC）
- カードデータ検証（AMEX CSC、Discover CID）

---

## 2. コスト

### Q5: APC の料金モデルはどうなっていますか？

APC の料金は 2 つのコンポーネントで構成されます。

**1. API 呼び出し料金（段階制）:**
| 月間ボリューム | 10,000 API 呼び出しあたりの料金 |
|---|---|
| 最初の 2,000 万回 [0 - 20,000,000] | $2.00 |
| 次の 2 億回 [20,000,001 - 220,000,000] | $0.75 |
| 次の 3 億回 [220,000,001 - 520,000,000] | $0.25 |
| 追加分 [520,000,001+] | $0.10 |

**2. アクティブ鍵の料金:**
- 鍵 1 つあたり月額 $1.00（日割り計算）

| 鍵リソース | アクティブ鍵 1 つあたりの料金 |
|---|---|
| 最初の 500 鍵 [0-500] | $1.00 |
| 次の 500 鍵 [501-1000] | $0.10 |
| 次の 5 万鍵 [1001-51,000] | $0.01 |
| 追加分 [51,001+] | $0.001 |


前払い費用、最低利用のコミットメント、ハードウェアのプロビジョニング費用はありません。

> 📖 [AWS Payment Cryptography 料金](https://aws.amazon.com/payment-cryptography/pricing/)

---

## 3. 可用性・パフォーマンス

### Q8: AWS Payment Cryptography の SLA はどうなっていますか？

AWS Payment Cryptography は **99.99% の可用性 SLA** を提供します。本サービスは各リージョン内の複数のアベイラビリティゾーンにデプロイされ、自動フェイルオーバーを提供します。月間稼働率が SLA のコミットメントを下回った場合、お客様はサービスクレジットの対象となります。

> 📖 [AWS Payment Cryptography SLA](https://aws.amazon.com/payment-cryptography/sla/)

---

### Q9: デフォルトのスループット上限（TPS）はいくつですか？

| 操作タイプ | デフォルト TPS | 備考 |
|---|---|---|
| 対称鍵の暗号操作（PIN、CVV、MAC、ARQC） | 500 TPS | アカウント・リージョンごと |
| 非対称鍵の暗号操作（RSA、ECDH） | 20 TPS | アカウント・リージョンごと |
| コントロールプレーン操作（CreateKey、ImportKey） | 5 TPS | アカウント・リージョンごと |

これらは **デフォルトのクォータ** であり、バースト時には実際のスループットがこれを上回る場合があります。

---

### Q10: TPS のクォータは引き上げできますか？

はい。すべての APC クォータは AWS Service Quotas から調整可能です。引き上げを申請するには:

1. **Service Quotas** → **AWS Payment Cryptography** に移動します
2. 該当するクォータ（例: 「Symmetric cryptographic operations rate」）を選択します
3. 「引き上げをリクエスト」をクリックし、希望する上限を指定します

処理時間は通常 1〜3 営業日です。高いトランザクション量が見込まれる本番ワークロード（例: 繁忙期のピーク）では、事前に引き上げを申請してください。

> 📖 [APC Service Quotas](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/quotas.html)

---

### Q11: APC は Multi-Region Keys をサポートしていますか？

はい。APC はネイティブの **Multi-Region 鍵レプリケーション** を提供します。プライマリリージョン（PRK）で作成された鍵は、同一の AWS パーティションおよびアカウント内の 1 つ以上のレプリカリージョン（RRK）にレプリケートできます。レプリケートされた鍵はリージョン間で **同一の鍵 ID** を保持し（ARN のうち変わるのはリージョン部分のみ）、PRK と RRK の両方がそれぞれのリージョンで暗号操作を実行できます。

要点:
- レプリケーションは `AddKeyReplicationRegions`、`RemoveKeyReplicationRegions`、`EnableDefaultKeyReplicationRegions`、`GetDefaultKeyReplicationRegions` で管理します。
- プライマリリージョンの鍵（`MultiRegionKeyType: PRIMARY`）が鍵管理の正となり、レプリカは `MultiRegionKeyType: REPLICA` とマークされます。
- レプリケーションは非同期で、削除はプライマリからレプリカへカスケードします。

これにより、手動の鍵エクスポート/インポートなしで、低レイテンシのマルチリージョン処理と災害復旧が可能になります。手動の TR-31/TR-34 交換は、自社の AWS アカウント/パーティション外の *外部* システムと共有する鍵に対して引き続き使用します。

> 📖 [AWS Payment Cryptography の鍵のレプリケーション](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/keys-multi-region-replication.html)

---

## 4. イシュア系ユースケース

### Q12: APC で Select PIN フローは ECDH を使ってどのように動作しますか？

Select PIN フローは、カード会員がカード有効化時に（PIN メーラーを受け取るのではなく）自分で PIN を選択できるようにするものです。APC はこれを **楕円曲線ディフィー・ヘルマン（ECDH）** 鍵合意を用いて実装します。

**フロー:**
1. **証明書のセットアップ** — AWS Private CA を使用して、モバイルアプリと APC の双方に短命の ECC 証明書（P-256/P-384）を発行します
2. **鍵合意** — モバイルアプリと APC がそれぞれ一時的な ECC 鍵ペアを生成します。ECDH は秘密情報を一切送信せずに共有秘密を導出します
3. **PIN 暗号化** — カード会員が選択した PIN は、モバイルデバイス上で ECDH 由来の鍵により暗号化されます
4. **PIN ブロック処理** — APC は暗号化された PIN ブロックを受け取り、共有秘密を用いてアンラップし、イシュアの PIN 暗号化鍵（PEK）で再暗号化して、PIN 検証値（PVV/PIN オフセット）を生成します

**主なメリット:**
- モバイルデバイスとの事前共有対称鍵が不要
- 短命の証明書により露出期間を限定
- 一時鍵ペアによる前方秘匿性

> 📖 [ECDH Select PIN サンプルコード](https://github.com/aws-samples/samples-for-payment-cryptography-service/blob/main/python_sdk_example/ecdh_flows/README.md)

---

### Q13: ECDH フローで短命証明書に AWS Private CA を使うのはなぜですか？

AWS Private CA は以下を提供します。

- **短命の証明書**（数時間〜数日）— モバイルデバイスが侵害された場合のリスク期間を最小化
- **自動発行** — カード会員セッションごとの手動証明書管理が不要
- **コスト効率** — 短命証明書モードは低価格（下位 CA で月額 $50）
- **統合** — 外部 PKI に依存しないネイティブな AWS サービス間認証

モバイルバンキングアプリは PIN 選択セッションごとに短命の ECC 証明書を要求するため、仮に傍受されても証明書（および導出された鍵素材）は速やかに失効します。

---

### Q14: APC は PIN Reset、PIN Set、PIN Reveal の操作を扱えますか？

はい。APC は PIN のライフサイクル全体をサポートします。

| 操作 | API | 説明 |
|-----------|-----|-------------|
| **PIN Set**（Select PIN） | `GeneratePinData` | カード会員が新しい PIN を選択し、APC が PVV/オフセットを生成 |
| **PIN Reset** | `GeneratePinData` | Set と同様。通常はカスタマーサービスのフローから起動 |
| **PIN Reveal** | `TranslatePinData` | 既存の PIN をセッション鍵で再暗号化し、カード会員へ安全に表示 |
| **PIN Verify** | `VerifyPinData` | カード会員が入力した PIN を、保存された PVV/オフセットと照合 |

すべての操作は ISO PIN ブロックフォーマット 0〜4 をサポートし、モバイル/Web クライアントとのエンドツーエンド暗号化に ECDH 由来の鍵を使用できます。

---

### Q15: APC で ARQC 検証はどのように動作しますか？

ARQC（Authorization Request Cryptogram）は EMV チップカードの認証メカニズムです。カード会員がチップカードをタップまたは挿入すると:

1. カードが、そのカードの一意導出鍵（UDK）とトランザクションデータを用いて ARQC を生成します
2. イシュアがオーソリゼーションリクエストで ARQC を受信します
3. APC の `VerifyAuthRequestCryptogram` API が、イシュアマスターキー（IMK）からセッション鍵を導出して暗号文を検証し、必要に応じてレスポンスで ARPC（Authorization Response Cryptogram）を生成します

**サポートされる導出方式:**
- Visa（CVN 10、18）
- Mastercard（CSK、Session Key）
- EMV Common Session Key 導出
- TDES および AES ベースの ARQC

---

### Q16: CVV/CVV2 の生成はどのように動作しますか？

APC は `GenerateCardValidationData` および `VerifyCardValidationData` API を用いてカード検証値を生成・検証します。

- **CVV**（磁気ストライプ）— PAN、有効期限、サービスコード、CVK ペアから導出される 3 桁の値
- **CVV2**（カード非提示）— 同様に導出されるが、異なるデータ入力を使用
- **iCVV**（チップトランザクション）— EMV チップ向けの動的 CVV
- **dCVV**（非接触）— 非接触決済向けの動的 CVV

イシュアのカード検証鍵（CVK）は APC に保管され、生成（カードパーソナライゼーション時）と検証（オーソリゼーション時）の両方に使用されます。

---

## 5. 鍵交換

### Q17: 外部パートナー（例: カードパーソナライゼーションビューロー）が TR-31 や TR-34 のインポートをサポートしていない場合はどうすればよいですか？

これは移行時によくある課題です。優先度の高い順に、いくつかの回避策があります。

**オプション 1: ブリッジ HSM アプローチ**
- 従来型の HSM（例: Thales payShield）を「ブリッジ」として維持する
- パートナーがサポートする方式（例: デュアルコントロール下のクリアコンポーネント）でパートナーからブリッジ HSM に鍵をインポートする
- ブリッジ HSM から TR-31 鍵ブロックとしてエクスポートする
- その TR-31 鍵ブロックを APC にインポートする
- すべての鍵を移行し終えたらブリッジ HSM を廃止する

**オプション 2: パートナーへの採用要請**
- パートナーに TR-31/TR-34 の採用を働きかける — 最新の HSM ファームウェアの多くがサポートしている
- TR-34（RSA ベース）はベンダーが特に実装しやすい
- [ASC X9 TR-31](https://x9.org/) および [TR-34](https://x9.org/) の仕様書を提供する

**オプション 3: クリアテキストコンポーネント（最終手段 — 非推奨）**
- `ImportKey` API と `RootCertificatePublicKey` ラッピングを用いて、鍵コンポーネントをクリアテキストでインポートする
- 厳格なデュアルコントロール手順が必要
- リスクが高い — 他に手段がない場合のみ、追加の代替統制とともに使用する

> ⚠️ 鍵交換方式を選択する前に、PCI コンプライアンスを確保するため必ず QSA（Qualified Security Assessor）に相談してください。

---

### Q18: APC がネイティブにサポートする鍵交換標準は何ですか？

| 標準 | 方向 | ユースケース |
|----------|-----------|----------|
| **TR-31** | インポート・エクスポート | 対称鍵ブロック交換（業界標準） |
| **TR-34** | インポート・エクスポート | 初期鍵ローディング向けの非対称（RSA）鍵配布 |
| **RSA Wrap/Unwrap** | インポート・エクスポート | RSA 公開鍵による鍵ラッピング |
| **ECDH 鍵合意** | 導出 | Select PIN 向けのセッション鍵確立 |

TR-31 は、APC と外部システム間の継続的な鍵交換に推奨される方式です。TR-34 は通常、初期鍵ローディング時、または事前共有鍵が存在しない場合に使用します。

> 📖 [鍵のインポート](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/keys-import.html)

---

## 6. アクワイアラ系ユースケース

### Q19: アクワイアラ向けの PIN 変換はどのように動作しますか？

PIN 変換は、ある鍵（例: 端末の PIN 暗号化鍵）で暗号化された PIN ブロックを、平文 PIN を一切露出させることなく別の鍵（例: ネットワーク/イシュアのゾーン鍵）による暗号化へ変換します。

**API:** `TranslatePinData`

**典型的なフロー:**
1. POS 端末が端末 PEK でカード会員の PIN を暗号化 → PIN ブロック（Format 0/ISO 9564）
2. アクワイアラが PIN ブロックを APC へ送信
3. APC が端末 PEK で復号し、ネットワークゾーン鍵で再暗号化
4. 変換された PIN ブロックがカードネットワーク/イシュアへ転送される

**サポートされる変換:**
- Format 0 ↔ Format 0（TDES から TDES）
- Format 0 → Format 4（TDES から AES）
- Format 4 ↔ Format 4（AES から AES）
- 送信元/送信先の鍵タイプの任意の組み合わせ

---

### Q20: APC は P2PE（Point-to-Point Encryption）の復号を扱えますか？

はい。APC は決済端末からの P2PE 暗号化トランザクションデータの復号をサポートします。

1. **DUKPT 鍵管理** — APC が Base Derivation Key（BDK）を保管し、端末の Key Serial Number（KSN）を用いてトランザクションごとの鍵を導出します
2. **復号** — `DecryptData` API が端末で暗号化された決済データを復号します
3. **再暗号化** — 必要に応じて、下流処理向けに別の鍵で機微データを再暗号化します

TDES-DUKPT と AES-DUKPT の両方の導出方式をサポートします。

---

### Q21: APC はアクワイアラ向けにどの MAC 操作をサポートしていますか？

APC は、トランザクションの完全性に不可欠な MAC（Message Authentication Code）操作をサポートします。

**API:** `GenerateMac` / `VerifyMac`

| アルゴリズム | 鍵タイプ | ユースケース |
|-----------|----------|----------|
| ISO 9797 Algorithm 1 | TDES | レガシー端末 MAC |
| ISO 9797 Algorithm 3 | TDES | リテール MAC（最も一般的） |
| CMAC | AES | 最新の端末/ネットワーク MAC |
| HMAC | AES/TDES | アプリケーション層の完全性 |

アクワイアラは通常、受信するオーソリゼーションメッセージの MAC を検証し、送信するレスポンスメッセージに MAC を生成して、決済ネットワーク全体でメッセージの完全性を担保します。

---

## 7. コンプライアンス

### Q22: APC はどの PCI 認証を取得していますか？

AWS Payment Cryptography は以下の PCI コンプライアンス認証を維持しています。

| 認証 | 対象範囲 |
|---------------|-------|
| **PCI PIN** | PIN 処理、鍵管理、PIN 変換操作 |
| **PCI P2PE** | 復号管理コンポーネントプロバイダー（DMCP）、鍵管理コンポーネントプロバイダー（KMCP）、鍵ローディングコンポーネントプロバイダー（KLCP） |
| **PCI DSS** | レベル 1 サービスプロバイダー（AWS 全体の PCI DSS 認証の一部として） |

これらの認証により、お客様は暗号操作レイヤーについて APC の PCI コンプライアンスを継承でき、自社の監査範囲を大幅に削減できます。

> 📖 [AWS PCI コンプライアンス](https://aws.amazon.com/compliance/pci-dss-level-1-faqs/)

---

### Q23: APC における決済コンプライアンスの責任共有モデルはどうなっていますか？

| 責任 | AWS（APC） | お客様 |
|---------------|-----------|----------|
| HSM ハードウェアのセキュリティ | ✅ | |
| 物理的な鍵の保管 | ✅ | |
| 暗号アルゴリズムの実装 | ✅ | |
| PCI PIN/P2PE のデバイス認証 | ✅ | |
| 鍵アクセスポリシー（IAM） | | ✅ |
| アプリケーションレベルのセキュリティ | | ✅ |
| 鍵ローテーション手順 | | ✅ |
| トランザクションデータの取り扱い | | ✅ |
| カード会員データ環境の PCI DSS | | ✅ |
| APC との間のネットワークセキュリティ | 共有 | 共有 |

AWS は暗号インフラストラクチャを管理し、お客様はサービスの呼び出し方、アクセス管理、暗号操作前後のデータの取り扱いについて責任を負います。

---

### Q24: APC のコンプライアンス文書にはどのようにアクセスしますか？

コンプライアンス成果物は **AWS Artifact** から入手できます。

1. AWS コンソールにサインインします
2. **AWS Artifact** → **レポート** に移動します
3. 「Payment Cryptography」または「PCI PIN」で検索します
4. 該当するアテステーション文書（AOC、ROC）をダウンロードします

入手可能な文書には以下が含まれます。
- PCI PIN Attestation of Compliance（AOC）
- PCI P2PE Component Listing
- PCI DSS Attestation of Compliance
- SOC 2 Type II レポート（APC を対象）

> 📖 [AWS Artifact](https://aws.amazon.com/artifact/)

---

## 8. 移行

### Q25: Thales payShield HSM から APC へ鍵を移行するにはどうすればよいですか？

**手順:**

1. **payShield からのエクスポート** — payShield のコンソール/API を使用して鍵を TR-31 鍵ブロックとしてエクスポートします（ファームウェア 3.x 以降が TR-31 をネイティブサポート）
2. **鍵暗号化鍵（KEK）の確立** — TR-34 プロトコルを用いて payShield と APC の間で共有 KEK を作成します
3. **APC へのインポート** — `ImportKey` API で TR-31 鍵ブロックと KEK の参照を用いてインポートします
4. **検証** — 既知のテストベクトルで暗号操作を実行し、鍵素材が一致することを確認します
5. **並行稼働** — 確信が得られるまで両システムを同時に稼働させます

> 📖 [AWS ブログ: AWS Payment Cryptography への移行](https://aws.amazon.com/blogs/security/migrate-from-on-premises-payment-hsms-to-aws-payment-cryptography/)

---

### Q26: Atalla や Futurex の HSM から移行できますか？

はい。ただしアプローチはプラットフォームによって異なります。

**Atalla（Utimaco）:**
- Atalla は TR-31 鍵ブロックのエクスポートをサポートします（ファームウェア依存）
- TR-31 が利用できない場合は、ブリッジ HSM アプローチを使用します
- Atalla のバリアント鍵導出方式は、APC の相当する方式にマッピングする必要があります

**Futurex:**
- Futurex Vectera Plus と KMES Series 3 は TR-31 をネイティブサポートします
- 鍵を TR-31 でエクスポートし、TR-34 で KEK を確立して APC にインポートします
- 古いモデルでは Futurex Guardian を仲介として利用できます

すべての移行において、まず **鍵インベントリ** を作成してください。
- すべての鍵をカタログ化する（タイプ、用途、アルゴリズム、有効期限）
- 各鍵を相当する APC の鍵タイプおよび用途属性にマッピングする
- 外部パートナーと共有している鍵を特定する（これらは協調的な交換が必要）

---

### Q27: 移行時に推奨されるハイブリッド運用のアプローチは何ですか？

ハイブリッド（並行稼働）アプローチは移行時のリスクを最小化します。

**フェーズ 1: 準備（2〜4 週間）**
- 対象リージョンに APC をデプロイする
- すべての鍵をインポート/同期する
- アプリケーション統合を構築・テストする

**フェーズ 2: シャドーモード（2〜4 週間）**
- 本番トラフィックを既存 HSM（プライマリ）へルーティングする
- リクエストを APC にもミラーリングする（シャドー）
- 暗号出力を比較して正しさを検証する
- レイテンシとエラー率を監視する

**フェーズ 3: 段階的カットオーバー（2〜8 週間）**
- 一定割合のトラフィックを APC へルーティングする（5〜10% から開始）
- 確信が高まるにつれて徐々に増やす
- オンプレミス HSM をフォールバックとして維持する

**フェーズ 4: 廃止（2〜4 週間）**
- トラフィックの 100% を APC へルーティングする
- オンプレミス HSM を 30〜90 日間スタンバイで維持する
- 安定期間の後にハードウェアを廃止する

**主な考慮事項:**
- ハイブリッド期間中は鍵を同期し続ける（鍵ローテーションは両システムを更新する必要がある）
- 自動フォールバックのためにサーキットブレーカーパターンを実装する
- 並行稼働中は両経路を監視対象に含める

> 📖 [AWS Payment Cryptography ワークショップ](https://catalog.workshops.aws/payment-cryptography/en-US)

---

### Q28: ハイブリッド運用中の鍵同期はどのように扱いますか？

ハイブリッド運用中は、レガシー HSM と APC の両方で鍵を同一に保つ必要があります。

1. **初期同期** — レガシー HSM のすべてのアクティブ鍵を APC にインポートします
2. **ローテーションの協調** — 鍵をローテーションする際:
   - 一方のシステムで新しい鍵を生成する
   - TR-31 でエクスポートしてもう一方にインポートする
   - アプリケーション内で両システムの鍵参照をアトミックに更新する
3. **新規鍵の作成** — APC（将来のプライマリ）で新しい鍵を作成し、必要に応じてフォールバック用にレガシー HSM へエクスポートする
4. **監査証跡** — 両システムですべての鍵操作を記録し、日次で突合する

APC の鍵エイリアスとタグを使用して、レガシー HSM の鍵ラベルと APC の鍵 ARN のマッピングを維持します。

---

## 追加リソース

- [AWS Payment Cryptography ユーザーガイド](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/)
- [AWS Payment Cryptography API リファレンス](https://docs.aws.amazon.com/payment-cryptography/latest/APIReference/)
- [サンプルコードリポジトリ](https://github.com/aws-samples/samples-for-payment-cryptography-service)
- [AWS Payment Cryptography ワークショップ](https://catalog.workshops.aws/payment-cryptography/en-US)
- [AWS セキュリティブログ — Payment Cryptography 関連記事](https://aws.amazon.com/blogs/security/tag/aws-payment-cryptography/)
- [AWS re:Invent Payment Cryptography セッション](https://www.youtube.com/results?search_query=aws+reinvent+payment+cryptography)

---

*最終更新: 2026-07-08*
