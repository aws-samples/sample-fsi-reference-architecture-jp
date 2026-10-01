# アクワイアラ リファレンスガイド — AWS Payment Cryptography

> 加盟店契約会社（アクワイアラ）、アクワイアリング側の決済処理事業者、端末管理プロバイダ向け。

---

## 目次

1. [P2PE 復号](#p2pe-復号)
2. [PIN 変換](#pin-変換)
3. [MAC 生成・検証](#mac-生成検証)
4. [端末鍵管理](#端末鍵管理)

---

## P2PE 復号

### 概要

Point-to-Point Encryption（P2PE）は、POI端末からアクワイアラの安全な復号環境まで、カード会員データを保護します。AWS Payment Cryptography は、PCI P2PE DMCPプログラムに基づく **PCI P2PE 復号コンポーネント** として認定されています。

### DUKPT 鍵階層

```
Base Derivation Key (BDK) — 基本導出鍵
  └── Initial PIN Encryption Key (IPEK) — 初期PIN暗号鍵
        └── Future Keys（KSNに基づきトランザクション毎に導出）
```

| 鍵レベル | 目的 | 保管場所 |
|---------|------|---------|
| BDK | マスター鍵、HSM外に出ない | AWS Payment Cryptography（`TR31_B0_BASE_DERIVATION_KEY`） |
| IPEK | プロビジョニング時に端末に注入 | 端末セキュアメモリ |
| トランザクション鍵 | IPEK + KSNから導出 | エフェメラル（トランザクション毎） |

### DecryptData API（DUKPT使用）

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/abc123",
  "CipherText": "A1B2C3D4E5F6...",
  "DecryptionAttributes": {
    "Dukpt": {
      "KeySerialNumber": "FFFF9876543210E00001",
      "DukptKeyDerivationType": "TDES_2KEY",
      "DukptKeyVariant": "BIDIRECTIONAL",
      "Mode": "CBC"
    }
  }
}
```

### サポートされる DUKPT 導出タイプ

| 導出タイプ | 鍵長 | ユースケース |
|-----------|------|------------|
| `TDES_2KEY` | 128ビット（実効112ビット） | TDES DUKPT（ANSI X9.24-1）、広く普及している端末 |
| `AES_128` | 128ビット | AES DUKPT（ANSI X9.24-3）対応端末 |
| `AES_192` | 192ビット | AES DUKPT（ANSI X9.24-3） |
| `AES_256` | 256ビット | AES DUKPT（ANSI X9.24-3）、高セキュリティ環境 |

> 導出タイプはBDKの強度以下である必要があります。DUKPTによる暗号化・復号では、BDK（`TR31_B0_BASE_DERIVATION_KEY`）のアルゴリズムとして `TDES_2KEY`、`AES_128`、`AES_192`、`AES_256` を使用できます。

### サポートされる暗号モード

DUKPTでは、`Mode` パラメータに `CBC`（デフォルト）または `ECB` を指定できます。

- **CBC**（Cipher Block Chaining）— デフォルト。P2PEペイロードで最も一般的
- **ECB**（Electronic Codebook）— 端末仕様で必須とされる場合（例：単一ブロックのデータ）を除き、使用を避けてください。ECBは同一の平文ブロックを同一の暗号文ブロックに変換するため、複数ブロックのデータではパターンが漏洩します。CBCを優先してください。

> CFBやOFBなどのモードは、DUKPTではなく非DUKPTの対称鍵（`Symmetric` 属性）でのみ利用できます。

### P2PE DMCP 認定のメリット

- アクワイアラのPCI DSSスコープを削減（加盟店のSAQ P2PE適格性）
- AWSがHSMコンプライアンスと監査証跡を管理
- AWS Payment Cryptographyサービス境界内での復号環境の分離

---

## PIN 変換

### 概要

PIN変換は、暗号化されたPINブロックを平文PINを露出させることなく別の暗号鍵に変換します。端末レベルの鍵（DUKPT/ZPK）からネットワークレベルの鍵へルーティングする際に不可欠です。

### TranslatePinData API

```json
{
  "EncryptedPinBlock": "AC17DC148BDA645E",
  "IncomingKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/terminal-bdk",
  "IncomingDukptAttributes": {
    "KeySerialNumber": "FFFF9876543210E00001",
    "DukptKeyDerivationType": "TDES_2KEY"
  },
  "IncomingTranslationAttributes": {
    "IsoFormat0": { "PrimaryAccountNumber": "4111111111111111" }
  },
  "OutgoingKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/network-zpk",
  "OutgoingTranslationAttributes": {
    "IsoFormat0": { "PrimaryAccountNumber": "4111111111111111" }
  }
}
```

`IncomingKeyIdentifier` には、DUKPTで暗号化されたPINブロックの場合はBDK（`IncomingDukptAttributes` と併用）を、それ以外の場合はPEK/ZPKを指定します。`PrimaryAccountNumber` には完全なPAN（12〜19桁）を指定します。

### PIN ブロックフォーマット

| フォーマット | 規格 | 特徴 |
|------------|------|------|
| ISO-0（Format 0） | Visa PVV、ほとんどのネットワーク | PAN依存、PANとのXOR |
| ISO-1（Format 1） | PAN非依存 | ランダムパディング |
| ISO-3（Format 3） | Mastercard推奨 | PAN依存、ランダムフィル |
| ISO-4（Format 4） | AESベース | AES暗号化、16バイトブロック |

### 変換シナリオ

**DUKPT→ZPK（端末→ネットワーク）：**
```
POI端末（DUKPT暗号化PIN）
  → アクワイアラホスト（TranslatePinData API）
    → ネットワークZPK暗号化PINブロック → カードネットワーク / イシュア
```

**ZPK→ZPK（アクワイアラ→ネットワーク）：**
ルーティングアーキテクチャに複数のZPKゾーンが存在する場合に使用。マルチネットワーク構成で一般的。

### PIN変換用の鍵タイプ

| 鍵用途 | TR-31ヘッダ | 目的 |
|--------|-----------|------|
| ZPK（Zone PIN Key） | `P0` | ゾーン間のPIN暗号化 |
| BDK（Base Derivation Key） | `B0` | 端末導出用DUKPTベース鍵 |
| PEK（PIN Encryption Key） | `P0` | 汎用PIN暗号化 |

### PCI PIN コンプライアンス

- PINブロックはSCD（Secure Cryptographic Device）外で復号してはならない
- AWS Payment Cryptographyの変換操作はPINを暗号化状態のまま維持
- 監査ログ（CloudTrail）が鍵間変換を露出なしで実証
- PCI PIN Security Requirements v3.1のコントロールに対応

---

## MAC 生成・検証

### 概要

メッセージ認証コード（MAC）は、アクワイアラホストとカードネットワーク間のトランザクションメッセージの完全性と真正性を保証します。

### GenerateMac / VerifyMac API

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/mac-key",
  "MessageData": "0200B238...",
  "GenerationAttributes": {
    "Algorithm": "ISO9797_ALGORITHM3"
  },
  "MacLength": 8
}
```

### サポートされるMACアルゴリズム

| アルゴリズム | 規格 | 鍵タイプ（KeyUsage） | ユースケース |
|------------|------|---------|------------|
| HMAC-SHA256 | FIPS 198-1 | HMAC鍵（`TR31_M7_HMAC_KEY`） | 最新APIベースメッセージング |
| Retail MAC（ISO 9797-1 Alg 3） | ISO 9797-1 | TDES鍵（`TR31_M3_ISO_9797_3_MAC_KEY`） | ISO 8583金融メッセージ |
| CMAC（AES） | NIST SP 800-38B | AES鍵（`TR31_M6_ISO_9797_5_CMAC_KEY`） | AESベースネットワークプロトコル |
| ISO 9797-1 Algorithm 1 | ISO 9797-1 | TDES鍵（`TR31_M1_ISO_9797_1_MAC_KEY`） | レガシーネットワーク |

### DUKPT派生MAC鍵

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/bdk",
  "MessageData": "0200B238...",
  "GenerationAttributes": {
    "DukptIso9797Algorithm3": {
      "KeySerialNumber": "FFFF9876543210E00001",
      "DukptDerivationType": "TDES_2KEY",
      "DukptKeyVariant": "BIDIRECTIONAL"
    }
  }
}
```

### トランザクションメッセージ完全性のユースケース

1. **ISO 8583メッセージMAC** — オーソリ要求/応答のMAC（DE-64/DE-128）
2. **バッチ精算MAC** — 精算ファイル送信の完全性
3. **管理メッセージ** — 鍵変更通知、ネットワーク管理
4. **端末→ホスト** — POI端末からのメッセージのMAC検証

---

## 端末鍵管理

### 概要

アクワイアラは多数のPOI端末の暗号鍵を管理する必要があります。AWS Payment Cryptography は端末に直接接続しません。`ExportKey` APIがBDKと端末のKSN（`ExportAttributes.ExportDukptInitialKey`）から端末固有のIPEKを導出し、TR-34またはTR-31の鍵ブロックでラップして返却します。その鍵ブロックを、利用者の鍵ローディングシステムが端末に配送します。生成されたIPEKはAWS Payment Cryptography内に保持されず、エクスポートのたびに再生成されます。

### Remote Key Loading（RKL）

本ガイドでは Remote Key Loading（RKL）という用語を使用します。RKLは Remote Key Injection（RKI）とも呼ばれます。`ExportKey` はIPEKのエクスポートに次の2つの鍵ブロック方式をサポートしています。

| 方式 | `KeyMaterial` | ラップ鍵 | 主な用途 |
|------|---------------|---------|---------|
| TR-34（非対称） | `Tr34KeyBlock` | 端末（KRD）の公開鍵証明書 | 共有対称鍵をまだ持たない端末への初期鍵ロード |
| TR-31（対称） | `Tr31KeyBlock` | 端末または鍵注入施設との間で事前に確立したKEK（`TR31_K0_KEY_ENCRYPTION_KEY` または `TR31_K1_KEY_BLOCK_PROTECTION_KEY`） | KEK確立後の鍵ロード |

#### TR-34フロー（端末の公開鍵でラップ）

TR-34の用語では、AWS Payment Cryptography が Key Distribution Host（KDH）、端末が Key Receiving Device（KRD）となります。

```
1. 端末（KRD）がRSA鍵ペアと、端末CAが発行したラップ用証明書を保持
2. アクワイアラが端末CA証明書をAWS Payment Cryptographyにインポート
   （ImportKey、RootCertificatePublicKey）
3. アクワイアラがエクスポートトークンとKDH署名証明書チェーンを取得
   （GetParametersForExport）。端末はこの証明書チェーンを信頼する必要があります
4. アクワイアラがTr34KeyBlockを指定してExportKeyを呼び出し、AWS Payment Cryptographyが
   IPEKを導出して端末のラップ用証明書でラップし、鍵ブロックに署名
5. 端末がKDHの署名を検証してIPEKをアンラップし、セキュアメモリに格納
```

```json
{
  "ExportKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/bdk",
  "KeyMaterial": {
    "Tr34KeyBlock": {
      "CertificateAuthorityPublicKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/terminal-ca",
      "WrappingKeyCertificate": "<Base64エンコードした端末（KRD）のラップ用証明書>",
      "ExportToken": "export-token-abcdef1234567890",
      "KeyBlockFormat": "X9_TR34_2012"
    }
  },
  "ExportAttributes": {
    "ExportDukptInitialKey": { "KeySerialNumber": "FFFF9876543210E00001" }
  }
}
```

#### TR-31フロー（確立済みKEKでラップ）

端末または鍵注入施設との間でKEKを共有済みの場合は、そのKEKでラップしたTR-31鍵ブロックとしてIPEKをエクスポートします。

```json
{
  "ExportKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/bdk",
  "KeyMaterial": {
    "Tr31KeyBlock": {
      "WrappingKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/kek"
    }
  },
  "ExportAttributes": {
    "ExportDukptInitialKey": { "KeySerialNumber": "FFFF9876543210E00001" }
  }
}
```

### POI端末への鍵ロード

RKLプラットフォームや対応する鍵ブロック形式は、端末ベンダーや機種によって異なります。鍵ロードのプロセスを設計する前に、各ベンダーに次の点を確認してください。

| 確認項目 | 内容 |
|---------|------|
| RKLプロトコル | ベンダーのRKLプラットフォームが初期ロードでTR-34鍵ブロックを受け付けるか、または別の方法で先にKEKをロードする必要があるか |
| 鍵ブロック形式 | 端末がTR-31鍵ブロックを受け付けるか。独自エンベロープのみに対応する場合は、AWS Payment Cryptographyと端末の間にブリッジHSMまたはベンダーの鍵ロードサービスを配置する |
| 信頼関係の確立 | 端末側PKIとAWS Payment Cryptography（KDH）の間でCA証明書をどのように交換するか |

### 鍵ライフサイクルとベストプラクティス

- 端末グループ/加盟店ごとに一意のBDKを使用し影響範囲を限定
- KSNカウンターを監視し枯渇を検出（TDES DUKPTの場合2^21）
- 2〜3年のライフサイクルでBDKをローテーション
- 鍵インベントリのマッピングを維持（BDK → 端末シリアル → 加盟店ID）

---

## 関連リソース

- [AWS Payment Cryptography 開発者ガイド](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/)
- [PCI P2PE 基準](https://www.pcisecuritystandards.org/document_library/)
- [ANSI X9.24-3（AES DUKPT）](https://webstore.ansi.org/)
- [ISO 9564（PINセキュリティ）](https://www.iso.org/standard/68014.html)
