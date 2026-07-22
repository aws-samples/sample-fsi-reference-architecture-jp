# AWS Payment Cryptography の PCI コンプライアンス

本リファレンスでは、AWS Payment Cryptography（APC）の PCI コンプライアンスについて、
取得済み認証、責任共有モデル、お客様自身の PCI 審査に関するガイダンスを解説します。

---

## コンプライアンス認証

AWS Payment Cryptography は、以下の PCI コンプライアンス認証を取得しています。
独立した Qualified Security Assessor（QSA）による審査済みです。

### PCI PIN

- PIN セキュリティに関する **Attestation of Compliance（AOC）**
- HSM 鍵管理、PIN ブロック処理、鍵インジェクションをカバー
- APC がハードウェアおよび鍵管理コントロールに関する PCI PIN セキュリティ
  要件を満たしていることを検証

### PCI P2PE（Point-to-Point Encryption）

APC は 3 つの個別の Attestation of Validation（AOV）を取得しています：

| コンポーネント | AOV タイプ | 対象範囲 |
|--------------|-----------|---------|
| 復号管理 | DMCP | APC を復号環境として使用 |
| 鍵管理 | KMCP | APC 内の鍵ライフサイクル管理 |
| 鍵ローディング | KLCP | APC の鍵ローディング / インジェクション機能 |

### PCI DSS レベル 1

- APC インフラストラクチャは AWS の PCI DSS レベル 1 サービスプロバイダー
  コンプライアンスに含まれています
- 基盤インフラストラクチャ、ネットワークセグメンテーション、アクセス制御、
  モニタリングをカバー

### PCI 3DS（3-D Secure）

- AWS Payment Cryptography は **AWS の PCI DSS および PCI 3DS 評価の対象** です
  （上記の APC 固有の PCI PIN / P2PE アテステーションとは区別されます）。3DS
  サーバー / ACS / DS 実装向けに HSM ベースの暗号オペレーションを提供できます。
- 最新の 3DS カバレッジと該当する AOC は AWS Artifact で確認してください。

---

## 責任共有モデル

AWS Payment Cryptography の PCI コンプライアンスは責任共有モデルに基づいています。
お客様自身の PCI 審査のスコープ設定には、責任の分担を正確に理解することが重要です。

### AWS の責任

AWS は **クラウドのセキュリティ**（インフラストラクチャ）に責任を負います：

| カテゴリ | AWS の責任 |
|---------|-----------|
| HSM ハードウェア | PCI PTS HSM 認証取得済み HSM（PCI モードで運用）の調達、プロビジョニング、ライフサイクル管理、廃棄 |
| 物理セキュリティ | データセンターの物理アクセス制御、環境保護、監視 |
| メイン鍵管理 | AWS マネージドメイン鍵（鍵暗号化鍵）の生成、保管、ローテーション |
| インフラコンプライアンス | ネットワークインフラ、ハイパーバイザーセキュリティ、サービスエンドポイント保護 |
| ファームウェア管理 | HSM ファームウェアの更新、セキュリティパッチ、検証 |
| 耐タンパー性 | HSM のタンパー検知・タンパー応答メカニズム |
| 可用性 | HSM インフラのマルチ AZ 展開、フェイルオーバー、災害復旧 |

### お客様の責任

お客様は **クラウドにおけるセキュリティ** に責任を負います：

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

### AWS に移管される事項

APC を PIN 処理に使用する場合、以下の PCI PIN 要件が AWS の責任に移管されます：

- **HSM 物理セキュリティ**: 認定データセンターにおける物理アクセス制御、
  タンパー検知、HSM のセキュアな保管
- **キーブロックでの鍵保管**: すべての鍵が TR-31 キーブロック形式で保管され、
  鍵用途属性がバインドされる（サービスによって強制）
- **タンパー応答**: 物理的なタンパー検知時の自動鍵ゼロ化
- **メイン鍵のデュアルコントロール**: AWS がメイン鍵の生成・ロードにおける
  デュアルコントロールおよびスプリットナレッジ手順を管理
- **キーブロックバインディング**: 鍵属性の暗号的バインディングによる誤用防止
  （例：PIN 暗号化鍵を PIN 検証鍵として使用することの防止）
- **HSM 論理セキュリティ**: ファームウェア整合性検証、セキュアブート、
  制限されたコマンドセット

### お客様に残る事項

お客様は以下について引き続き責任を負います：

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

### 復号管理コンポーネントプロバイダー（DMCP）

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

### 鍵管理コンポーネントプロバイダー（KMCP）

APC は P2PE 復号鍵のフルライフサイクルを管理します：

- **鍵生成**: HSM 内でのセキュアな乱数鍵生成
- **鍵保管**: 鍵は AWS メイン鍵で暗号化され、クリアテキストとして公開されない
- **鍵配布**: デバイスインジェクション用の TR-31 キーブロックによるセキュアな鍵エクスポート
- **鍵ローテーション**: `CreateKey` とエイリアス更新によるプログラマティックな鍵ローテーション
- **鍵削除**: スケジューリングをサポートする設定可能な削除待機期間

### 鍵ローディングコンポーネントプロバイダー（KLCP）

APC の鍵ローディング機能は PCI P2PE 鍵ローディングをサポートします：

- 決済端末へのセキュアな鍵インジェクションを実現
- TR-31 および TR-34 鍵交換プロトコルをサポート
- APC と鍵ローディングデバイス間の証明書ベースの相互認証
- CloudTrail による全鍵ローディング操作の監査証跡
- 初期鍵ローディングと鍵ローテーションの両シナリオをサポート

---

## 対象リージョン — サービス可用性 と PCI 認証範囲

**重要な区別**: AWS Payment Cryptography が *利用可能な* リージョンは、*PCI PIN /
P2PE 認証を取得済みの* リージョンよりも広い。あるリージョンで利用可能であること
は、そのリージョンでの PCI PIN/P2PE 認証を意味しない。

- **サービス可用性** には、東京（`ap-northeast-1`）・大阪（`ap-northeast-3`）
  などのアジアパシフィックリージョンが含まれる。
- **PCI PIN / P2PE 認証済みリージョンはその部分集合** であり、順次拡大されている
  （例: PCI PIN/P2PE カバレッジは南米 — サンパウロ（`sa-east-1`）およびアジア
  パシフィック — シドニー（`ap-southeast-2`）に拡大された）。本書執筆時点で、
  東京/大阪リージョンが PCI PIN/P2PE 認証範囲に含まれることは **確認されていない**。

> ⚠️ **日本国内のデプロイではこの点が決定的である。** 東京/大阪でのリージョン内
> PCI PIN/P2PE カバレッジを前提にしないこと。リージョン内でのコンプライアンスを
> 前提に設計する前に、PCI PIN・P2PE・DSS・3DS の **最新の** 認証済みリージョン
> 一覧を [AWS Artifact](https://console.aws.amazon.com/artifact/) および
> [AWS コンプライアンスプログラム対象サービス](https://aws.amazon.com/compliance/services-in-scope/)
> ページで必ず確認すること。

---

## 監査とログ

### AWS CloudTrail

すべての APC 操作が CloudTrail に記録されます：

**鍵管理操作**:
- `CreateKey`、`DeleteKey`、`UpdateKeyAttributes`
- `ImportKey`、`ExportKey`
- `ListKeys`、`GetKey`、`GetKeyStatus`
- `CreateAlias`、`UpdateAlias`、`DeleteAlias`

**暗号操作**:
- `EncryptData`、`DecryptData`
- `TranslatePinData`
- `GeneratePinData`、`VerifyPinData`
- `GenerateCardValidationData`、`VerifyCardValidationData`
- `GenerateMac`、`VerifyMac`

各ログエントリには以下が含まれます：
- タイムスタンプ、送信元 IP、IAM ID
- 操作に使用された鍵 ARN
- リクエストパラメータ（機密データを除く）
- 成功/失敗ステータスとエラーコード

### Amazon CloudWatch メトリクス

CloudWatch で APC の使用状況を監視：

- `SuccessfulRequests` / `FailedRequests` — 操作ごと
- `Latency` — 操作の処理時間
- `ThrottledRequests` — レート制限イベント
- `KeyCount` — アクティブな鍵の総数

### 鍵メタデータによるコンプライアンスレポート

APC API をコンプライアンスレポートに活用：

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
2. 「Payment Cryptography」または「PCI」で検索
3. NDA に同意（ほとんどのレポートで必要）
4. 関連する文書をダウンロード

### NDA 要件

- ほとんどの PCI コンプライアンス文書には秘密保持契約（NDA）の承諾が必要
- NDA は AWS Artifact ポータル内で電子的に提示
- レポートごとに個別の NDA 承諾が必要な場合がある
- NDA の承諾はログに記録され、AWS アカウントに関連付けられる

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

### SAQ/RoC スコープの縮小

APC の使用により、PCI 審査のスコープを大幅に縮小できます：

- **HSM コントロール**: HSM 関連のすべてのコントロール（物理セキュリティ、
  鍵管理ハードウェア、タンパー応答）が AWS に移管
- **鍵保管**: ローカルの鍵保管コントロールを実証する必要がない
- **施設セキュリティ**: HSM 施設のセキュリティ要件は AWS のコンプライアンスで充足

### エビデンス収集

PCI 審査を受ける際、APC に関連する以下のエビデンスを準備してください：

1. **AWS コンプライアンスレポート**: AWS Artifact から関連する AOC/AOV をダウンロード
2. **責任マトリクス**: AWS Responsibility Summary 文書を参照
3. **アーキテクチャ図**: アプリケーションと APC の統合方法を文書化
4. **IAM ポリシー**: APC API アクセスに対するアクセス制御を提示
5. **CloudTrail ログ**: すべての暗号操作の監査ログを実証
6. **鍵インベントリ**: 適切な鍵管理を示す鍵メタデータのエクスポート
7. **ネットワーク図**: TLS 強制とネットワークセグメンテーションを提示

### 審査員の期待事項

QSA は通常、以下を確認します：

- **サービス契約**: AWS サービス契約のエビデンス
- **コンプライアンスの継承**: AWS が所有するコントロールを示す文書
- **代替コントロール**: 非標準的な実装に対する代替コントロール
- **運用手順**: APC に関連する鍵ローテーション、アクセスレビュー、
  インシデントレスポンスの手順
- **テストのエビデンス**: アプリケーション層のペネトレーションテスト結果
  （AWS インフラに対するものではない）
- **モニタリング設定**: CloudWatch アラームとインシデントレスポンス手順

### スコープに関する考慮事項

| シナリオ | スコープへの影響 |
|---------|----------------|
| PIN 変換のみ | HSM コントロールは完全に委託、アプリケーションコントロールは残存 |
| P2PE 復号 | 復号環境コントロールは委託、復号後の処理はスコープ内 |
| 鍵管理のみ | 鍵保管とライフサイクルは委託、鍵使用ガバナンスは残存 |
| フル決済処理 | 大幅な縮小だがアプリケーション、ネットワーク、アクセス制御は残存 |

---

## 免責事項

> **⚠️ 重要なお知らせ**
>
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
> との契約が必要です**。審査の具体的なスコープ、要件、必要なエビデンスは、
> お客様固有の実装、ビジネスモデル、および組織に適用される PCI 基準によって
> 異なります。
>
> AWS のコンプライアンス認証は、AWS のインフラストラクチャとサービスをカバー
> します。お客様が管理する環境の部分については、適用される PCI 基準への
> コンプライアンスについてお客様自身が責任を負います。
>
> 最新のコンプライアンス状況と認証済みリージョンについては、必ず
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
