<!-- Fictional example. Part of customer-context-manager's example store, not real data. -->
# Systems & Operations — Any Manufacturing Co., Ltd.

## Known Systems
<!-- 両者の取引で実際に触れるシステムと、お客様側で需要や制約を生んでいるシステム。
     この例のシステム名は `ANY-` 接頭辞で架空であることを示し、外部サービスや業界インフラも
     一般名詞で書いている。実名かどうか読者が確かめられない名前を公開例に置くと、実在の
     名称である可能性が残るため。実ストアでは社内名称・製品名をそのまま記録する。 -->

| System Name | Category | Technology | Source | Notes |
|-------------|----------|-----------|--------|-------|
| ANY-EB | 当行EBサービス | Web + API | [M20241115](#M20241115) | 総合振込・残高照会。API連携は未対応、要望あり |
| ANY-DEBT | 電子記録債権 | 外部ネットワーク経由 | [M20250603](#M20250603) | 月間 XXX件利用。手形レス化完了済 |
| ANY-EDI | 企業間データ連携 | 金融EDI（業界標準） | [M20250603](#M20250603) | 主要取引先XX社と接続済。消込自動化の要望あり |
| ANY-SEISAN | 生産管理 | オンプレミス（自社開発、レガシー言語） | [M20260205](#M20260205) | 導入30年超。更新計画あり → 設備資金の融資機会 |
| ANY-KAIKEI | 会計システム | パッケージ（オンプレミス） | [M20240822](#M20240822) | ベンダーサポート2027年終了。クラウド移行を検討中 |
| ANY-SHIKIN | 資金管理システム | 表計算ソフト + マクロ | [M20260205](#M20260205) | 丙野様が独自に構築。限界を感じている。CMS提案の余地 |
| ANY-SEISAN-OVS | 海外工場生産管理 | {unknown} | [UNS20260512](#UNS20260512) | Name appeared in an undated internal note. Existence not confirmed with the customer — ask before referencing |

## Operational Constraints
<!-- お客様の業務サイクル上、こちらの動きを縛るもの: 締め日、承認段階、利用時間、
     意思決定の開催サイクル。Source each line. -->
- 月次締め: 毎月25日締め・翌月5日払い（この前後の振込設定変更は避ける） [[D20251110](#D20251110)]
- 総合振込の承認: 経理課長 → 財務部長の2段階承認 [[D20251110](#D20251110)]
- EB利用時間: 平日 8:00-21:00（休日利用なし） [[M20240312](#M20240312)]
- 資金需要の山: 6月・12月の賞与月と3月の決算期 [[D20251110](#D20251110)]
- 取締役会: 月1回。稟議の社内締切はその2週間前 [[M20250603](#M20250603)]

## Planned Changes
Source: [M20260410](#M20260410)（このセクション全体）

- 生産管理システムの更新を検討中。投資規模・時期は未定 → 設備資金の相談が見込まれる
- 会計システムはベンダーサポート終了（2027年）に伴う移行を検討中
- 資金管理の表計算ソフト運用に限界を認識。CMS導入の提案余地あり
- 海外工場の増設に伴い、現地の資金管理方式が未定
- 投資判断では同業他社の導入実績を重視する

<!--
Note the two patterns above: the constraints each carry their own source because they come
from different places; the planned changes share one source, so it is stated once under the
heading instead of repeated five times.
-->

<!--
This file records what the relationship touches — the systems in use between the two
organizations, the operating rhythm that constrains when you can act, and the changes the
customer is planning. It is not a technical inventory of the customer's IT estate: record a
system's internals only where they explain a need or a constraint you have to work with.
-->

## Sources

<!-- 出所の定義。参照側は [KEY](#KEY) の形で本文・表から指す。
     キー形式: <種別><YYYYMMDD>。同一キーに別の出所が当たる場合のみ末尾に b, c … を付す。 -->

- <a id="D20251110"></a>**D20251110** — doc:社内規程集 2025-11-10 {no-url} — paper handout; ask 乙野様 for the document library location
- <a id="M20240312"></a>**M20240312** — meeting 2024-03-12
- <a id="M20240822"></a>**M20240822** — meeting 2024-08-22
- <a id="M20241115"></a>**M20241115** — meeting 2024-11-15
- <a id="M20250603"></a>**M20250603** — meeting 2025-06-03, 丙野 三郎
- <a id="M20260205"></a>**M20260205** — meeting 2026-02-05
- <a id="M20260410"></a>**M20260410** — meeting 2026-04-10, 乙野 次郎
- <a id="UNS20260512"></a>**UNS20260512** — {unsourced} recorded 2026-05-12
