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
| BDK | マスター鍵、HSM外に出ない | AWS Payment Cryptography（TR31_P0_PIN_ENCRYPTION_KEY） |
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
      "DukptKeyDerivationType": "TDES_3KEY",
      "DukptKeyVariant": "BIDIRECTIONAL",
      "Mode": "CBC"
    }
  }
}
```

### サポートされる DUKPT 導出タイプ

| 導出タイプ | 鍵長 | ユースケース |
|-----------|------|------------|
| `TDES_2KEY` | 128ビット（実効112ビット） | レガシー端末 |
| `TDES_3KEY` | 192ビット（実効168ビット） | 標準POS端末 |
| `AES_128` | 128ビット | 近年の端末（ANSI X9.24-3準拠） |
| `AES_256` | 256ビット | 高セキュリティ環境 |

### サポートされる暗号モード

- **CBC**（Cipher Block Chaining）— P2PEペイロードで最も一般的
- **ECB**（Electronic Codebook）— 限定的なユースケース
- **CFB**（特定の端末実装におけるストリーミング復号用）

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
  "IncomingKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/terminal-key",
  "OutgoingKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/network-zpk",
  "IncomingTranslationAttributes": {
    "DukptIso2004": {
      "KeySerialNumber": "FFFF9876543210E00001",
      "DukptKeyDerivationType": "TDES_3KEY",
      "DukptKeyVariant": "PIN"
    }
  },
  "OutgoingTranslationAttributes": {
    "IsoPin0": { "PrimaryAccountNumber": "4111111111111111" }
  }
}
```

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
    "Algorithm": "ISO9797_ALGORITHM3",
    "MacLength": 8
  }
}
```

### サポートされるMACアルゴリズム

| アルゴリズム | 規格 | 鍵タイプ | ユースケース |
|------------|------|---------|------------|
| HMAC-SHA256 | FIPS 198-1 | HMAC鍵 | 最新APIベースメッセージング |
| Retail MAC（ISO 9797-1 Alg 3） | ISO 9797-1 | TDES鍵 | ISO 8583金融メッセージ |
| CMAC（AES） | NIST SP 800-38B | AES鍵 | AESベースネットワークプロトコル |
| ISO 9797-1 Algorithm 1 | ISO 9797-1 | TDES鍵 | レガシーネットワーク |

### DUKPT派生MAC鍵

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/bdk",
  "MessageData": "0200B238...",
  "GenerationAttributes": {
    "DukptIso9797Algorithm3": {
      "KeySerialNumber": "FFFF9876543210E00001",
      "DukptKeyDerivationType": "TDES_3KEY",
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

アクワイアラは多数のPOI端末の暗号鍵を管理する必要があります。AWS Payment Cryptography はRemote Key Injection（RKI）および初期鍵プロビジョニングをサポートする鍵エクスポートAPIを提供します。

### Remote Key Loading（RKI）

```
1. 端末がRSA鍵ペアを生成
2. 端末が公開鍵（証明書付き）をアクワイアラホストに送信
3. アクワイアラが証明書チェーンを検証
4. アクワイアラがIPEKを端末公開鍵で暗号化してエクスポート（ExportKey API）
5. 端末が復号しIPEKをセキュアメモリに格納
```

### ExportKey API による IPEK 配布

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

### POI端末への鍵注入

| 端末ベンダー | RKIプロトコル | 鍵フォーマット |
|------------|-------------|-------------|
| Ingenico（Worldline） | TLSベースRKI、DUKPT | TR-31ラップIPEK |
| Verifone | VeriShield RKI | TR-31 / 独自エンベロープ |
| PAX Technology | PAX RKIプラットフォーム | TR-31ラップ鍵 |

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
