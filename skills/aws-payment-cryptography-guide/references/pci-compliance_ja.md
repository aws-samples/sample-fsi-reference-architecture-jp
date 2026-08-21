# AWS Payment Cryptography の PCI コンプライアンス

本リファレンスでは、AWS Payment Cryptography（APC）の PCI コンプライアンスについて、
取得済み認証、責任共有モデル、お客様自身の PCI 審査に関するガイダンスを解説します。

---

## コンプライアンス認証

AWS Payment Cryptography は、以下の PCI コンプライアンス認証を取得しています。
AWSサービスにおける 最新の PCI カバレッジと該当する **Attestation of Compliance（AOC）** は [AWS Artifact](https://aws.amazon.com/jp/artifact/) を利用してお客様はセルフサービスで取得・確認することができます。

### PCI DSS

- PCI DSS (Payment Card Industry Data Security Standard) は、加盟店やサービス・プロバイダーにおいて、クレジットカード会員データを安全に取り扱うことを目的として PCI SSC(Security Standards Council) によって策定された、クレジットカード業界の国際セキュリティ基準です。

### PCI PIN

- PCI PIN は、PIN(Personal Identification Number) セキュリティに関する HSM 鍵管理、PIN ブロック処理、鍵インジェクションをカバーするコンプライアンスです。

### PCI P2PE

- PCI P2PE （Point-to-Point Encryption）は、クレジットカード決済端末からネットワークを経由し決済処理までのカード情報を一貫して暗号化して保護する国際的なセキュリティ基準です。
- APC は 3 つの個別の Attestation of Validation（AOV）を取得しています：

| コンポーネント | AOV タイプ | 対象範囲 |
|--------------|-----------|---------|
| 復号管理 | DMCP | APC を復号環境として使用 |
| 鍵管理 | KMCP | APC 内の鍵ライフサイクル管理 |
| 鍵ローディング | KLCP | APC の鍵ローディング / インジェクション機能 |

- 最新の PCI P2PE カバレッジと該当する AOC は AWS Artifact で確認してください。

### PCI 3DS

- PCI 3DS（3-D Secure）は、クレジットカードの不正利用を防ぐための本人認証の仕組みや、そのデータ保護を安全に扱うための国際的なセキュリティ基準です。
- APC は 3DS Server / ACS(Access Control Server) / Directory Server(DS) 実装向けに HSMベースの暗号オペレーションを提供します。
- 最新の PCI 3DS カバレッジと該当する AOC は AWS Artifact で確認してください。

---

## 責任共有モデル

APC の PCI コンプライアンスは 他のAWSサービスと同様に **[責任共有モデル](https://aws.amazon.com/jp/compliance/shared-responsibility-model/)** に基づいています。
お客様の PCI審査のスコープ設定を適切に設計する上で、責任共有モデルの理解は重要なポイントです。

### AWS の統制範囲

AWS は **クラウドのセキュリティ**（インフラストラクチャ）を責任範囲(統制範囲)とします：

| カテゴリ | AWS の責任 |
|---------|-----------|
| HSM ハードウェア | PCI PTS HSM 認証取得済み HSM（PCI モードで運用）の調達、プロビジョニング、ライフサイクル管理、廃棄 |
| 物理セキュリティ | データセンターの物理アクセス制御、環境保護、監視 |
| メイン鍵管理 | AWS マネージドメイン鍵（鍵暗号化鍵）の生成、保管、ローテーション |
| インフラコンプライアンス | ネットワークインフラ、ハイパーバイザーセキュリティ、サービスエンドポイント保護 |
| ファームウェア管理 | HSM ファームウェアの更新、セキュリティパッチ、検証 |
| 耐タンパー性 | HSM のタンパー検知・タンパー応答メカニズム |
| 可用性 | HSM インフラのマルチ AZ 展開、フェイルオーバー、災害復旧 |

### お客様の統制範囲

お客様は **クラウドにおけるセキュリティ** を責任範囲(統制範囲)とします：

| カテゴリ | お客様の責任 |
|---------|------------|
| アプリケーションセキュリティ | セキュアコーディング、入力バリデーション、セキュアな API 統合 |
| 鍵属性管理 | 適切な鍵用途属性、アルゴリズム選択、鍵目的の割り当て |
| 正確な API 使用 | translate、encrypt、decrypt、generate 操作の適切な使用 |
| 復号後のデータ処理 | APC から返されたクリアテキストデータの保護 |
| アクセス制御 | IAM ポリシー、リソースポリシー、APC API への最小権限アクセス |
| ネットワークセキュリティ | VPC 設定、セキュリティグループ、API 呼び出しの TLS 強制 |
| モニタリングとアラート | 適切なアラームの設定とセキュリティイベントへの対応 |
| コンプライアンス文書 | 自社の PCI 審査に必要なエビデンスと文書の管理 |

---

## PCI PIN コンプライアンス

### AWSサービスの統制範囲

APC を PIN 処理に使用する場合、以下の PCI PIN 要件が AWSサービスの統制範囲とすることができます：

- **HSM 物理セキュリティ**: 認定データセンターにおける物理アクセス制御、
  タンパー検知、HSM のセキュアな保管
- **キーブロックでの鍵保管**: すべての鍵が TR-31 キーブロック形式で保管され、
  鍵用途属性がバインドされる（AWSサービスによって強制）
- **タンパー応答**: 物理的なタンパー検知時の自動鍵ゼロ化
- **メイン鍵のデュアルコントロール**: AWS がメイン鍵の生成・ロードにおける
  デュアルコントロールおよびスプリットナレッジ手順を管理
- **キーブロックバインディング**: 鍵属性の暗号的バインディングによる誤用防止
  （例：PIN 暗号化鍵を PIN 検証鍵として使用することの防止）
- **HSM 論理セキュリティ**: ファームウェア整合性検証、セキュアブート、
  制限されたコマンドセット

### お客様に残る事項

お客様は引き続き以下が統制範囲です：

- **アプリケーションでの PIN ブロック処理**: PIN ブロックがアプリケーション
  メモリ内で処理時間を超えてクリアテキストとしてログ、キャッシュ、保存されないこと
- **ネットワークセキュリティ**: すべての API 呼び出しにおける TLS 1.2+ の強制、
  必要に応じた VPC エンドポイントの使用、ネットワークセグメンテーション
- **アクセス制御**: PIN 関連 API を呼び出せるユーザーを制限する IAM ポリシー、
  鍵管理と PIN 操作の職務分離
- **PIN 試行カウンター**: アプリケーション層での PIN 試行制限とロックアウト
  メカニズムの実装
- **PIN メーラーセキュリティ**（該当する場合）: PIN メーラーのセキュアな生成と配布
- **カード保有者への通信**: PIN のカード保有者への安全な配信チャネル

---

## PCI P2PE コンポーネント

### PCI 復号管理コンポーネントプロバイダー（DMCP）

APC は **P2PE 復号環境** として機能します：

- P2PE 検証済み POI デバイスからの暗号化された決済データが APC に直接送信され復号
- 復号は HSM 境界内でのみ実行
- クリアテキスト PAN は TLS 経由でお客様のアプリケーションに返却
- 復号後のデータ保護はお客様の責任
- 復号鍵は適切な用途属性でバインド

```
[POI デバイス] → (暗号化データ) → [お客様アプリ] → [APC DecryptData API]
                                                          ↓
                                                   [HSM 復号処理]
                                                          ↓
                                              (TLS 経由でクリアテキスト返却)
```

### PCI 鍵管理コンポーネントプロバイダー（KMCP）

APC は P2PE 復号鍵のフルライフサイクルを管理します：

- **鍵生成**: HSM 内でのセキュアな乱数鍵生成
- **鍵保管**: 鍵は AWS メイン鍵で暗号化され、クリアテキストとして公開されない
- **鍵配布**: デバイスインジェクション用の TR-31 キーブロックによるセキュアな鍵エクスポート
- **鍵ローテーション**: `CreateKey` とエイリアス更新によるプログラマティックな鍵ローテーション
- **鍵削除**: スケジューリングをサポートする設定可能な削除待機期間

### PCI 鍵ローディングコンポーネントプロバイダー（KLCP）

PCI P2PE 鍵ローディングの実現にAPC の鍵管理機能を利用することができます：

- 決済端末へのセキュアな鍵インジェクションを実現
- TR-31 および TR-34 鍵交換プロトコルをサポート
- APC と鍵ローディングデバイス間の証明書ベースの相互認証
- CloudTrail による全鍵ローディング操作の監査証跡
- 初期鍵ローディングと鍵ローテーションの両シナリオをサポート

---

## 監査とログ

### AWS CloudTrail

すべての APC コントロールプレーンの操作は CloudTrail にデフォルトで記録されます：

**鍵管理操作**:
- `CreateKey`、`DeleteKey`、`UpdateKeyAttributes`
- `ImportKey`、`ExportKey`
- `ListKeys`、`GetKey`、`GetKeyStatus`
- `CreateAlias`、`UpdateAlias`、`DeleteAlias`

加えて、CloudTrail証跡で **データイベントの記録** を明示的に有効にすることで、 データプレーンの操作も CloudTrailに記録することができます：
(**デフォルトではデータイベントのログは記録されません**)

**暗号操作**:
- `EncryptData`、`DecryptData`
- `TranslatePinData`
- `GeneratePinData`、`VerifyPinData`
- `GenerateCardValidationData`、`VerifyCardValidationData`
- `GenerateMac`、`VerifyMac`

各ログエントリには以下が含まれます：
- タイムスタンプ、送信元 IP、IAM Principalの識別子
- 操作に使用された鍵のARN
- リクエストパラメータ（機密データを除く）
- 成功/失敗ステータスとエラーコード

### Amazon CloudWatch メトリクス

APC は Amazon CloudWatch メトリクス に主に以下のメトリクスを発行し、その使用状況をモニタリングすることができます：

- `SuccessfulRequests` / `FailedRequests` — 操作ごと
- `Latency` — 操作の処理時間
- `ThrottledRequests` — レート制限イベント
- `KeyCount` — アクティブな鍵の総数

### 鍵メタデータ

アカウントおよびリージョンでご利用のAPCの鍵に関する情報(メタデータ)は、以下に代表されるAPI(CLI)で入手することができます：

```bash
# コンプライアンス監査用に全鍵と属性を一覧表示
aws payment-cryptography list-keys

# 作成日と用途を含む詳細な鍵情報を取得
aws payment-cryptography get-key --key-identifier "arn:aws:..."

# 鍵のステータスと有効期限を確認
aws payment-cryptography get-parameters-for-export \
  --key-material-type KEY_CRYPTOGRAM \
  --signing-key-algorithm RSA_2048
```

---

## コンプライアンスレポートへのアクセス

### AWS Artifact ポータル

APC の PCI コンプライアンスレポートは AWS Artifact を通じて入手できます：

1. [AWS Artifact コンソール](https://console.aws.amazon.com/artifact/)にアクセス
2. 入手アーティファクトとして「Payment Cryptography」または「PCI」で検索
3. 秘密保持契約(NDA) に同意
4. 文書をダウンロード

### 補足：NDA 要件について

- ほとんどの PCI コンプライアンス文書の入手には秘密保持契約（NDA）の承諾が必要です
- レポートごとに個別の NDA 承諾が必要な場合があります
- NDAの承諾はAWS Artifact内に記録されます。

### 入手可能な文書

| 文書 | 説明 |
|------|------|
| PCI PIN AOC | PIN セキュリティ要件に関する Attestation of Compliance |
| PCI P2PE DMCP AOV | 復号管理に関する Attestation of Validation |
| PCI P2PE KMCP AOV | 鍵管理に関する Attestation of Validation |
| PCI P2PE KLCP AOV | 鍵ローディングに関する Attestation of Validation |
| PCI DSS AOC | レベル 1 サービスプロバイダー Attestation of Compliance |
| Responsibility Summary | コントロールごとの詳細な責任マトリクス |
| Component User Guide | APC を P2PE ソリューションに統合するお客様向けガイダンス |
| PCI 3DS（AWS の PCI DSS/3DS AOC 経由） | APC は AWS の PCI DSS/3DS 評価の対象。AWS の PCI 3DS AOC を参照 |

---

## お客様の PCI 審査への影響

### PCI 審査スコープの縮小

AWS責任共有モデル に伴い、AWSサービスであるAPCの使用により、お客様からみたPCI審査のスコープの縮小に貢献します：

- **HSM コントロール**: HSM 関連のすべてのコントロール（物理セキュリティ、
  鍵管理ハードウェア、タンパー応答）が AWS に移管
- **鍵保管**: ローカルの鍵保管コントロールを実証する必要がない
- **施設セキュリティ**: HSM施設のセキュリティ要件が、AWSのコンプライアンスで充足

### 一般的なエビデンス収集

お客様がPCI 審査を受ける際には、APCの利用に関連して以下の情報の整理をお薦めします。

1. **AWS コンプライアンスレポート**: AWS Artifact から関連する AOC/AOV をダウンロード
2. **責任マトリクス**: AWS Responsibility Summary 文書を参照
3. **アーキテクチャ図**: アプリケーションと APC の統合方法を文書化
4. **IAM ポリシー**: APC API アクセスに対するアクセス制御を提示
5. **CloudTrail ログ**: すべての暗号操作の監査ログを実証
6. **鍵インベントリ**: 適切な鍵管理を示す鍵メタデータのエクスポート
7. **ネットワーク図**: TLS 強制とネットワークセグメンテーションを提示

上記以外にも、以下の提示が必要になる場合があります：

- **代替コントロール**: 非標準的な実装に対するお客様の代替アプローチ
- **APCの運用手順**: APC に関連する鍵ローテーション、アクセスレビュー、
  インシデントレスポンスの手順
- **テストのエビデンス**: アプリケーション層のペネトレーションテスト結果
  （AWSインフラストラクチャに対するものではないお客様統制範囲に対するテスト）
- **モニタリング設定**: Amazon CloudWatch アラームを利用したモニタリングとインシデントレスポンス手順

### 参考：スコープに関する考慮事項

| 利用シナリオ | スコープへの影響 |
|---------|----------------|
| PIN 変換のみ | 物理HSM自体のコントロールはAPCの統制範囲です。アプリケーションコントロールはお客様の統制範囲です |
| P2PE 復号 | 復号環境コントロールはAPCの統制範囲です。復号後の処理はお客様の統制範囲です |
| 鍵管理のみ | 鍵保管とライフサイクルはAPCの統制範囲です。鍵の使用とそのガバナンスはお客様の統制範囲です |
| 決済処理全体 | アプリケーション、ネットワーク、アクセス制御はお客様の統制範囲です |

---

## 免責事項

> 本ガイドは、AWS Payment Cryptography の PCI コンプライアンスに関する
> 一般的な情報を提供するものです。教育および計画目的のみを意図しています。
>
> **本文書は以下に該当しません**：
> - 正式な PCI コンプライアンス審査
> - 法的または規制上のアドバイス
> - 特定の実装に対するコンプライアンスの保証
> - 専門的なセキュリティ審査の代替
>
> **正式な PCI コンプライアンス審査には、Qualified Security Assessor（QSA）
> による審査が必要です**。審査の具体的なスコープ、要件、必要なエビデンスは、
> お客様固有の実装、ビジネスモデル、および組織に適用される PCI 基準によって
> 異なります。
>
> AWS のコンプライアンス認証は、AWS のインフラストラクチャとサービスを対象とします。
> お客様が管理する環境の部分に対して適用される PCI 基準への
> コンプライアンスは、引き続きお客様自身の統制範囲です。
>
> 最新のコンプライアンス状況と認証済みリージョンについては、
> [AWS Artifact](https://console.aws.amazon.com/artifact/) および
> [AWS コンプライアンスプログラム](https://aws.amazon.com/compliance/programs/)
> ページを参照してください。

---

## 関連リソース

- [AWS Payment Cryptography ドキュメント](https://docs.aws.amazon.com/payment-cryptography/)
- [AWS Artifact](https://console.aws.amazon.com/artifact/)
- [AWS コンプライアンスプログラム](https://aws.amazon.com/compliance/programs/)
- [コンプライアンスプログラム対象の AWS サービス](https://aws.amazon.com/compliance/services-in-scope/)
- [PCI Security Standards Council](https://www.pcisecuritystandards.org/)
- [AWS 責任共有モデル](https://aws.amazon.com/compliance/shared-responsibility-model/)
