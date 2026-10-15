<!-- Fictional example. Part of customer-context-manager's example store, not real data. -->
# Organization — Any Manufacturing Co., Ltd.

Full names, matching people.md. Roles live in the people table, not in the prose.

## Current Structure
<!-- The org hierarchy relevant to your engagement — not the whole company -->
Source: [L20260401](#L20260401)
supplemented by meeting 2026-04-10

```
代表取締役社長 甲野 太郎（創業家・株式 XX% 保有）
├── 専務取締役 甲野 一郎（海外事業部 部長）← 同姓の別人（社長の長男）
├── 財務部 乙野 次郎 部長
│   └── 経理部 乙野 花子 課長 ← 同姓の別人
├── 製造部 丁野 四郎 部長
│   ├── 第一工場（本社敷地内）
│   └── 海外工場
├── 情報システム部 丙野 三郎 課長
├── 総務部 己野 {unknown}
└── 営業部 戊野 五郎 部長
```

<!-- A hierarchy diagram is the one place a role sits next to a name: the role IS the
     content being recorded, and the whole block carries a dated source. Prose elsewhere
     should not repeat the title — it goes stale. -->

## Decision-Making Flow
<!-- Who approves what: capital investment, borrowing, contracts -->

- 設備投資 X千万円未満: 丁野様の起案 → 乙野様（財務）承認 [[M20260410](#M20260410)]
- 設備投資 X千万円以上: 取締役会決議（月1回開催） [[M20260410](#M20260410)]
- 借入 X億円以上: 甲野社長の決裁が必須 [[M20260410](#M20260410)]
- M&A・事業承継: 甲野社長の専決事項。取締役会は事後報告のケースあり [[M20260319](#M20260319)]
- システム投資: 丙野様が起案 → 乙野様が費用承認 → X千万円超は取締役会 [[M20260210](#M20260210)] {unconfirmed}

## Key Departments

- 財務部: 当行の主要カウンターパート。資金調達・銀行取引全般 [[L20260401](#L20260401)]
- 製造部: 設備投資の発生源。XX名体制。工場2拠点を管轄 [[L20260401](#L20260401)]
- 情報システム部: 基幹システム更新を推進中。少人数（X名）で外部委託中心 [[L20260401](#L20260401)]

## Change History
<!-- Track reorganizations. Newest first. One Source line covers the block. -->

### 2024-04: 海外事業部 新設
- Old: 海外工場は製造部の管下
- New: 甲野 一郎を部長とする独立部署。海外投資の起案権限を持つ
- Impact: 海外設備資金の稟議が迅速化。当行への相談が直接来るようになった
- Source: [M20240418](#M20240418)

### 2022-10: 情報システム部 新設
- Old: 経理部内のシステム担当（1名）
- New: 独立した情報システム部（丙野様が初代課長）
- Impact: 基幹システム更新計画が本格始動
- Source: [M20221015](#M20221015)

## Sources

<!-- 出所の定義。参照側は [KEY](#KEY) の形で本文・表から指す。
     キー形式: <種別><YYYYMMDD>。同一キーに別の出所が当たる場合のみ末尾に b, c … を付す。 -->

- <a id="L20260401"></a>**L20260401** — [org chart 2026-04-01](https://www.any-manufacturing.example.co.jp/company/officers/)
- <a id="M20221015"></a>**M20221015** — meeting 2022-10-15
- <a id="M20240418"></a>**M20240418** — meeting 2024-04-18
- <a id="M20260210"></a>**M20260210** — meeting 2026-02-10 — threshold stated verbally, not documented
- <a id="M20260319"></a>**M20260319** — meeting 2026-03-19, 甲野 太郎
- <a id="M20260410"></a>**M20260410** — meeting 2026-04-10, 乙野 次郎
