<!-- Fictional example. Part of customer-context-manager's example store, not real data. -->
# People — Any Manufacturing Co., Ltd.

<!--
Name: the full name as its owner writes it, original script, honorifics excluded
      (`山田 太郎`, `Anne-Marie O'Brien`). An unknown part is `{unknown}`.
Reading: kana for Japanese names; `-` when not applicable. Never invent either.
Source: where the name came from. Link it when an address exists.
Before adding someone here, check people/internal.md and people/partners.md — a name
mentioned in a customer meeting may be an internal member or a partner.
-->

## Customer Contacts

| Name | Reading | Department | Title | Role in Decisions | Email | Source | Notes |
|------|---------|-----------|-------|-------------------|-------|--------|-------|
| 甲野 太郎 | こうの たろう | 経営 | 代表取締役社長 | 最終意思決定者（オーナー） | - | [L20260401](#L20260401) | 創業家3代目。株式 XX% 保有。事業承継の当事者 |
| 甲野 一郎 | こうの いちろう | 海外事業部 | 部長 | 海外投資の起案者 | ichiro.kono@any-manufacturing.example.co.jp | [SIG20260214](#SIG20260214) | 社長の長男。海外工場担当。← 同姓の別人（親子だが意思決定ラインが異なる） |
| 乙野 次郎 | おつの じろう | 財務部 | 部長 | 資金調達・銀行取引の窓口 | jiro.otsuno@any-manufacturing.example.co.jp | [SIG20260214](#SIG20260214) | 日常の取引窓口。融資条件交渉の実務責任者 |
| 乙野 花子 | おつの はなこ | 経理部 | 課長 | 支払・資金繰り管理 | - | [L20260401](#L20260401) | 財務部長の乙野とは同姓の別人。← 同姓の別人 |
| 丁野 四郎 | ていの しろう {inferred} | 製造部 | 部長 | 設備投資の技術判断 | - | [M20260319](#M20260319) / [S20260319](#S20260319) | 工場の設備更新計画を主導。Reading could be ちょうの — confirm before speaking it |
| 丙野 三郎 | へいの さぶろう | 情報システム部 | 課長 | 基幹システム更新の実務担当 | - | [M20260205](#M20260205) | ERPリプレースの社内PMを務める |
| 己野 {unknown} | きの {unknown} | 総務部 | {unknown} | 契約書・登記関連 | - | [M20260210](#M20260210) | Given name and title not yet known. Fill from the next meeting invite attendee list. Email `-` by minimization, not a gap |

<!--
The 己野 row is the pattern for an incomplete name: saved rather than dropped, with the
gap visible and greppable so the next task completes it instead of re-asking the user.
A bare `己野` would have looked finished. Note the two different empty forms in that row:
{unknown} where a value exists but is not known, `-` in Email where nothing is being
recorded on purpose.
-->

## External Advisors

<!-- お客様が起用している外部専門家。当行から見た「外部関係者」 -->

| Name | Reading | Company | Role | Project/Context | Email | Source | Notes |
|------|---------|---------|------|-----------------|-------|--------|-------|
| 乙川 六郎 | おつかわ ろくろう | 乙川会計事務所 | 顧問税理士 | 税務・決算支援 | - | [M20260122](#M20260122) | 創業時からの顧問。甲野社長の信頼が厚い |
| John Doe | - | Any Advisory Partners | M&A Advisor | 事業承継・M&A | - | [SIG20260302](#SIG20260302) | Writes his name in Latin script; keep it as written. 外資系。事業承継スキーム検討中 |

## Sources

<!-- 出所の定義。参照側は [KEY](#KEY) の形で本文・表から指す。
     キー形式: <種別><YYYYMMDD>。同一キーに別の出所が当たる場合のみ末尾に b, c … を付す。 -->

- <a id="L20260401"></a>**L20260401** — [org chart 2026-04-01](https://www.any-manufacturing.example.co.jp/company/officers/)
- <a id="M20260122"></a>**M20260122** — meeting 2026-01-22
- <a id="M20260205"></a>**M20260205** — meeting 2026-02-05
- <a id="M20260210"></a>**M20260210** — meeting 2026-02-10 (mentioned by 乙野 次郎)
- <a id="M20260319"></a>**M20260319** — meeting 2026-03-19
- <a id="S20260319"></a>**S20260319** — reading: inferred 2026-03-19
- <a id="SIG20260214"></a>**SIG20260214** — email signature 2026-02-14
- <a id="SIG20260302"></a>**SIG20260302** — email signature 2026-03-02
