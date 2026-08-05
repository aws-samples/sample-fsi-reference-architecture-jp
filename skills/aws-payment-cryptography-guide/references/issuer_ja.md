# イシュアー向けリファレンスガイド — AWS Payment Cryptography

## 概要

本ガイドは、AWS Payment Cryptography（APC）を活用してPIN管理、カード検証、EMVトランザクション認証、外部パートナー連携を行う**カード発行銀行・金融機関**向けのリファレンスです。

APCは、PCI PTS HSM認証を取得したクラウドネイティブ環境を提供し、オンプレミスHSM管理の負担を排除しつつ、決済ネットワーク基準への完全準拠を維持します。

---

## PIN生成・検証

### 概要

PIN操作はイシュアー処理の中核機能です。APCは業界標準方式によるランダムPIN生成とPIN検証の両方をサポートしています。

### GeneratePinData API

`GeneratePinData` APIはPINとその検証データ（PVVまたはオフセット）を単一のアトミック操作で生成します。

**主要パラメータ：**
- `GenerationKeyIdentifier` — PIN生成キー（PGK）のARNまたはエイリアス
- `GenerationAttributes` — 方式の指定（PVVまたはIBM 3624）
- `PinBlockFormat` — ISOフォーマット（ISO_FORMAT_0、ISO_FORMAT_3、ISO_FORMAT_4）
- `PrimaryAccountNumber` — カード会員のPAN
- `EncryptionKeyIdentifier` — 返却PINブロック暗号化用の鍵

**使用例：**
```json
{
  "GenerationKeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/abc123",
  "GenerationAttributes": {
    "VisaPinVerificationValue": {
      "EncryptedPinBlock": "...",
      "PinVerificationKeyIndex": 1
    }
  },
  "PinBlockFormat": "ISO_FORMAT_0",
  "PrimaryAccountNumber": "[REDACTED_CC]",
  "EncryptionKeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/def456"
}
```

### VerifyPinData API

`VerifyPinData` APIは暗号化PINブロックを保存済み検証データと照合し、クリアテキストPINを公開せずに検証します。

**主要パラメータ：**
- `VerificationKeyIdentifier` — PIN検証キー（PVK）のARN
- `VerificationAttributes` — 方式固有のパラメータ
- `EncryptedPinBlock` — トランザクションからの暗号化PINブロック
- `PinBlockFormat` — 生成時のフォーマットと一致が必要
- `PrimaryAccountNumber` — カード会員のPAN

### PVV（PIN Verification Value）方式

Visa PVV方式は以下の要素から4桁の検証値を導出します：
1. PIN検証キー（PVK） — ダブルレングスDESまたはAES鍵
2. PAN（チェックディジットを除く右端12桁）
3. PIN検証キーインデックス（PVKI） — 1桁の数値（1〜6）
4. PINの左端の桁

**利点：**
- コンパクトなストレージ（4桁の値をDB保存）
- PINオフセット非保存により漏洩リスク低減
- Visaおよびほとんどの国際ネットワークで広くサポート

### IBM 3624オフセット方式

デシマライゼーションテーブルとPIN検証キーを使用してPANから「自然PIN」を生成し、顧客選択PINとの差分をオフセットとして保存する方式です。

**特徴：**
- オフセットはイシュアーDBまたは磁気ストライプに保存
- デシマライゼーションテーブルは全検証ポイントで一貫性が必要
- ATMネットワークやデビットスキームで依然として広く使用

**セキュリティ注意：** デシマライゼーションテーブルとPIN検証キーはPIN自体と同等の保護が必要です。APCはこれらをHSM境界内に安全に保管します。

---

## Select PIN（ECDH）

### 概要

近年のイシュアーはモバイルアプリ経由でのカード会員PIN選択を支援しています。APCはECDH（楕円曲線ディフィー・ヘルマン）ベースの鍵合意メカニズムを提供し、中間地点でのクリアテキストPIN露出なしにセキュアなPIN転送を実現します。

### アーキテクチャ構成要素

1. **モバイルアプリケーション** — カード会員がPINを入力するフロントエンド
2. **AWS Private CA** — 短期有効なECDH鍵ペア用証明書を発行
3. **APC ECDH鍵導出** — PINブロック暗号化用の共有対称鍵を導出

### フロー図

```
┌──────────┐       ┌─────────────┐       ┌─────────────┐
│ モバイル  │       │  イシュアー   │       │    APC      │
│  アプリ   │◄─────►│  バックエンド │◄─────►│   (HSM)     │
└──────────┘       └─────────────┘       └─────────────┘
     │                    │                      │
     │ 1. PIN変更要求     │                      │
     │────────────────────►│                      │
     │                    │ 2. ECDH公開鍵取得     │
     │                    │─────────────────────►│
     │                    │◄─────────────────────│
     │ 3. サーバー公開鍵返却│                      │
     │◄────────────────────│                      │
     │ 4. 共有鍵でPIN暗号化│                      │
     │────────────────────►│                      │
     │                    │ 5. PINブロック転送    │
     │                    │─────────────────────►│
     │                    │ 6. 復号・検証         │
     │                    │◄─────────────────────│
     │ 7. 完了通知         │                      │
     │◄────────────────────│                      │
```

### サブフロー

#### PIN再設定（Reset PIN）
カード会員がPINを忘れた場合 → 追加認証（OTP、生体認証）→ モバイルアプリでの新PIN選択。

#### PIN設定（Set PIN）
カード有効化時の初回PIN選択。モバイルアプリがPINをキャプチャし、ECDH導出鍵で暗号化してAPCに送信。

#### PIN表示（Reveal PIN）
カード会員が現在のPINを確認（例：海外渡航前）。ECDH導出鍵で暗号化し、モバイルデバイスのセキュアエンクレーブ内でのみ復号。

### 証明書管理

- **短期有効証明書**（数分〜数時間）により漏洩影響を最小化
- **AWS Private CA**が発行・失効を管理
- **証明書ピンニング**によりMITM攻撃を防止

### リファレンス実装

[AWS Samples — Payment Cryptography向けECDHフロー](https://github.com/aws-samples/samples-for-payment-cryptography-service/blob/main/python_sdk_example/ecdh_flows/README.md)

---

## CVV / iCVV / dCVV

### CVV/CVV2

磁気ストライプ（CVV1）またはカード券面（CVV2）の静的検証値。

- **GenerateCardValidationData** — CVK、PAN、有効期限、サービスコードからCVVを生成
- **VerifyCardValidationData** — CVVを検証、期待値を公開せず合否を返却

### iCVV（ICカード検証値）

チップ→磁気ストライプのフォールバック時に使用。偽造検知のため通常CVVと異なる値。

- iCVV計算ではサービスコード`999`を使用（CVV1では実際のサービスコード）
- 磁気ストライプ取引でiCVVが出現した場合、チップカードクローンの可能性を示唆

### dCVV（動的CVV）

定期的に変更（例：20分ごと）され、EC取引セキュリティを強化。

**イシュアーの考慮事項：**
- カードとイシュアー間の時刻同期アルゴリズムが必要
- クロックドリフト許容値の適切な設定
- 時間制約による検証コール量増加
- APCは基盤となる暗号演算をサポート

---

## ARQC検証

### EMVオンライン認証

チップカードがオンライン取引を開始する際、カードマスター鍵から導出されたセッション鍵でARQCを生成します。

### VerifyAuthRequestCryptogram API

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:...:key/issuer-mk",
  "TransactionData": "<16進エンコードのトランザクションデータ>",
  "AuthRequestCryptogram": "<8バイトARQC>",
  "MajorKeyDerivationMode": "EMV_OPTION_A",
  "SessionKeyDerivationAttributes": {
    "Mastercard": {
      "ApplicationTransactionCounter": "001C",
      "PanSequenceNumber": "00",
      "PrimaryAccountNumber": "[REDACTED_CC]"
    }
  }
}
```

### セッション鍵導出方式

#### Mastercard（EMV Option A / CSK）
1. イシュアーマスター鍵からPAN＋PANシーケンス番号でICCマスター鍵を導出
2. ATC（Application Transaction Counter）でセッション鍵を導出
3. トランザクションデータのMACを計算
4. カードからのARQCと比較

#### Visa（EMV Option A）
1. 類似の導出だが異なる多様化データを使用
2. Visa固有のパディングと鍵導出定数
3. CVN（Cryptogram Version Number）がアルゴリズムバリアントを決定

### ARPC生成

ARQC検証後、イシュアーがカードに対して自身を認証するARPCを生成：
- **Method 1：** ARPC = DES(SK)[ARQC ⊕ ARC]
- **Method 2：** 4バイトプロプライエタリデータによるリッチレスポンス

APCの`GenerateAuthResponseCryptogram`が両方式に対応。

### ベストプラクティス

- IMKは`TR31_E0_EMV_MKEY_APP_CRYPTOGRAMS`鍵タイプとして保存
- MAC、暗号化、データ認証に個別IMKを使用
- ARQC失敗率を監視 — 急増は漏洩の兆候
- 暗号検証と併せて速度制御チェックを実装

---

## 外部パートナー連携の課題

### 課題の概要

カードパーソナライゼーションビューローやプリントベンダーは、ストライプエンコード、チップパーソナライゼーション、PIN生成のために暗号鍵を必要とします。APCネイティブの鍵交換方式であるTR-31/TR-34をサポート**していない**HSMを運用している場合があります

### 回避策の選択肢

#### (a) ブリッジHSM

APCフォーマットとパートナーレガシーフォーマットの両方をサポートする中間HSM。

**オプション1 — AWS CloudHSM：**
```
APC ──(TR-31)──► CloudHSM ──(レガシー形式)──► パートナー
```

**オプション2 — 既存オンプレミスHSM：**
```
APC ──(TR-34)──► オンプレHSM ──(パートナープロトコル)──► パートナー
```

#### (b) パートナーへの規格採用要請

- TR-31必須化のタイムライン提示（12〜18ヶ月）
- PCI PIN Security Requirements v3.1（2025年鍵ブロック義務化）を参照
- APCのTR-31エクスポート機能でテスト支援を提案
- Visa/Mastercardコンプライアンスプログラムを通じてエスカレーション

#### (c) クリアテキスト鍵コンポーネント

最終手段 — 厳格な管理下でのクリアテキストコンポーネント交換。

**PCI要件：**
- 最低2コンポーネント（3つ推奨）、別々の管理者が保持
- ロード時デュアルコントロール — 単一人物が完全鍵を見ることを禁止
- 別々のセキュアチャネルで送信、タンパーエビデントパッケージング

**リスク：** PCI監査負担増大、運用リスク、ヒューマンエラー。長期使用は非推奨。

### マイグレーション戦略

```
フェーズ1： クリアテキストコンポーネント（厳格なデュアルコントロール）
フェーズ2： ブリッジHSM構築
フェーズ3： パートナーがTR-31/TR-34を採用
フェーズ4： APCからパートナーへの直接鍵交換
```

---

## まとめ

| 機能 | APC API | 鍵タイプ |
|------|---------|----------|
| PIN生成 | `GeneratePinData` | TR31_V2_VISA_PIN_VERIFICATION_VALUE |
| PIN検証 | `VerifyPinData` | TR31_V2_VISA_PIN_VERIFICATION_VALUE |
| CVV生成 | `GenerateCardValidationData` | TR31_C0_CARD_VERIFICATION_KEY |
| CVV検証 | `VerifyCardValidationData` | TR31_C0_CARD_VERIFICATION_KEY |
| ARQC検証 | `VerifyAuthRequestCryptogram` | TR31_E0_EMV_MKEY_APP_CRYPTOGRAMS |
| ARPC生成 | `GenerateAuthResponseCryptogram` | TR31_E0_EMV_MKEY_APP_CRYPTOGRAMS |
| PIN変換 | `TranslatePinData` | TR31_P0_PIN_ENCRYPTION_KEY |
| ECDH鍵合意 | `GetPublicKeyCertificate` | TR31_K2_TR34_ASYMMETRIC_KEY |

---

*最終更新：2026年7月8日*
*対象：サポート全リージョンのAWS Payment Cryptographyサービス*
