# Sample Trigger Prompts and Outputs

This document shows realistic user prompts that trigger the boj-statistics skill, along with the CLI commands the agent executes and the resulting output. These examples demonstrate the business value of each API type.

---

## Metadata API (`get-metadata`, `search-series`, `list-db`)

### Example M-1: "日銀にどんな統計データベースがあるか教えて"

**Business context**: A financial analyst new to BOJ data wants to understand what's available.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py list-db --format table
```

**Output**:
```
  IR01  基準割引率および基準貸付利率の推移
  IR02  預金種類別店頭表示金利の平均年利率等
  IR03  定期預金の預入期間別平均金利
  IR04  貸出約定平均金利
  FM01  無担保コールO/N物レート
  FM02  短期金融市場金利
  ...
  FM08  外国為替市況
  ...
  CO    短観
  PR01  企業物価指数
  BP01  国際収支統計
  FF    資金循環
  ...
```

**Value**: One command for a complete overview of 50 BOJ databases — no need to browse the BOJ website manually.

---

### Example M-2: "ドル円の為替データの系列コードを調べたい"

**Business context**: A treasury department staff member needs to identify the correct series code for USD/JPY rates before building a report.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py search-series --db FM08 --keywords ドル 円 --format table --max-series-size 5
```

**Output**:
```
  FXERD01  東京市場　ドル・円　スポット　9時時点       [DAILY]    19990101~20260317
  FXERD02  東京市場　ドル・円　スポット　最高値        [DAILY]    19990101~20260317
  FXERD03  東京市場　ドル・円　スポット　最安値        [DAILY]    19990101~20260317
  FXERD04  東京市場　ドル・円　スポット　17時時点      [DAILY]    19980105~20260317
  FXERD05  東京市場　ドル・円　スポット　中心相場      [DAILY]    19990101~20260317
```

**Value**: Keyword search across hundreds of series in seconds. The analyst can immediately see the available granularity (9am, 17pm, high, low, central rate) and coverage period.

---

### Example M-3: "短観のデータベースにはどんな系列があるか確認したい"

**Business context**: An economist preparing a Tankan analysis needs to understand the structure of the Tankan database.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py get-metadata --db CO --format table --max-series-size 10
```

**Output**:
```
                        判断項目  []  ~
                        判断項目（D.I.）  []  ~
                        業況（「良い」−「悪い」）  []  ~
                        全規模合計  []  ~
  TK99F0000601GCQ00000  D.I./業況/全規模/全産業/実績  [QUARTERLY]  197402~202504
  ...
```

**Value**: Reveals the hierarchical structure of the Tankan database — the analyst can see how series are organized by category (DI, judgment items), scale (all sizes, large enterprises), and industry.

---

### Example M-4: "企業物価指数の総平均の系列コードを探して"

**Business context**: A risk analyst needs the Producer Price Index (PPI) overall average for inflation monitoring.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py search-series --db PR01 --keywords 企業物価指数 総平均 --format table
```

**Output**:
```
  PRCG20_2200000000  [国内企業物価指数] 総平均                    [MONTHLY]  196001~202602
  PRCG20_22G2200000  (参考)夏季電力料金調整後/総平均              [MONTHLY]  199001~202602
```

**Value**: Pinpoints the exact series code from a database with thousands of price index series, distinguishing the standard index from seasonal adjustment variants.

---

## Code API (`get-data`, `latest`)

### Example C-1: "2024年のドル円月中平均レートの推移を見せて"

**Business context**: A corporate finance team needs monthly average USD/JPY rates for FY2024 financial statement translation.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py search-series --db FM08 --keywords ドル 円 中心相場 月中平均 --format table
# → finds FXERM09

python3 scripts/boj_statistics_cli.py get-data --db FM08 --code FXERM09 --start 202401 --end 202412 --format table
```

**Output**:
```
--- FXERM09: 東京市場　ドル・円　スポット　中心相場/月中平均 (1ドルにつき円) [MONTHLY] ---
  202401  146.57
  202402  149.42
  202403  149.63
  202404  153.43
  202405  156.13
  202406  157.82
  202407  158.06
  202408  146.23
  202409  143.38
  202410  149.63
  202411  153.72
  202412  153.72
```

**Value**: Official BOJ exchange rates used for financial reporting — directly usable for foreign currency translation in financial statements.

---

### Example C-2: "短観の大企業・製造業と非製造業の業況判断DIを2023年から比較したい"

**Business context**: A macro strategist wants to compare manufacturing vs. non-manufacturing sentiment trends.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py get-data --db CO \
  --code TK99F1000601GCQ01000,TK99F2000601GCQ01000 \
  --start 202301 --end 202504 --format table
```

**Output**:
```
--- TK99F1000601GCQ01000: D.I./業況/大企業/製造業/実績 (%ポイント) [QUARTERLY] ---
  202301  1
  202302  5
  202303  9
  202304  12
  202401  11
  202402  13
  202403  13
  202404  14
  202501  12
  202502  13
  202503  14
  202504  15

--- TK99F2000601GCQ01000: D.I./業況/大企業/非製造業/実績 (%ポイント) [QUARTERLY] ---
  202301  20
  202302  23
  202303  27
  202304  30
  202401  34
  202402  33
  202403  34
  202404  33
  202501  35
  202502  34
  202503  34
  202504  34
```

**Value**: Side-by-side comparison of two key Tankan DI series. The data shows non-manufacturing consistently outperforming manufacturing — a critical insight for sector allocation decisions.

---

### Example C-3: "企業物価指数（総平均）の直近の推移を確認したい"

**Business context**: A credit analyst monitoring inflation trends for loan portfolio risk assessment.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py get-data --db PR01 --code PRCG20_2200000000 \
  --start 202401 --end 202502 --format table
```

**Output**:
```
--- PRCG20_2200000000: [国内企業物価指数] 総平均 (2020年=100) [MONTHLY] ---
  202401  120.4
  202402  120.6
  202403  121
  202404  121.8
  202405  122.7
  202406  123
  202407  123.6
  202408  123.2
  202409  123.6
  202410  124.2
  202411  124.6
  202412  125.1
  202501  125.5
  202502  125.8
```

**Value**: Monthly PPI trend showing steady upward pressure — directly relevant for inflation forecasting and BOJ policy outlook analysis.

---

### Example C-4: "今のドル円レートの最新値を教えて"

**Business context**: A quick check of the latest official BOJ exchange rate.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py latest --db FM08 --code FXERM09 --format table
```

**Output**:
```
--- FXERM09: 東京市場　ドル・円　スポット　中心相場/月中平均 (1ドルにつき円) [MONTHLY] ---
  202602  155.07
```

**Value**: Instant access to the latest published rate without navigating the BOJ website.

---

## Layer API (`get-layer`)

### Example L-1: "国際収支の経常収支の内訳を月次で取得したい"

**Business context**: An economist analyzing Japan's current account structure for a quarterly report.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py get-layer --db BP01 --layer 1,1,1 --frequency M \
  --start 202401 --end 202406 --format table --max-series-size 3
```

**Output**:
```
--- BPBP6JYNCB: 経常収支 (億円) [MONTHLY] ---
  202401  2987.99
  202402  27343.91
  202403  34372.75
  202404  21132.82
  202405  28750.48
  202406  16890.74

--- BPBP6JYNTS: 貿易・サービス収支 (億円) [MONTHLY] ---
  202401  -22347.86
  202402  -4159.99
  202403  4589.82
  202404  -13684.76
  202405  -11496.53
  202406  2415.23

--- BPBP6JYNTB: 貿易収支/ネット (億円) [MONTHLY] ---
  202401  -14859.53
  202402  -2983.07
  202403  4635.03
  202404  -6355.30
  202405  -10980.42
  202406  5805.40
```

**Value**: Hierarchical retrieval of related BOP series in one request. The analyst can see the current account, trade & services balance, and trade balance together — revealing that Japan's current account surplus is driven by income balance despite persistent trade deficits.

---

### Example L-2: "資金循環統計の金融機関の資産データを四半期で取得したい"

**Business context**: A financial stability analyst examining the asset composition of Japan's financial sector.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py get-layer --db FF --layer 1,1,1,1 --frequency Q \
  --start 202301 --end 202404 --format table --max-series-size 2 --max-item-length 4
```

**Output**:
```
--- FOF_FFAS100A100: 資産・現金・預金／金融機関／ストック (億円) [QUARTERLY] ---
  202301  8009521
  202302  8042498
  202303  7997509
  202304  8021716

--- ...
```

**Value**: Flow of Funds data is one of the most complex BOJ databases with thousands of series organized in deep hierarchies. The layer API lets the analyst navigate this structure systematically — specifying "financial institutions → assets → cash & deposits" without knowing individual series codes.

---

### Example L-3: "対外資産負債残高を暦年で取得したい"

**Business context**: A sovereign risk analyst reviewing Japan's international investment position over multiple years.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py get-layer --db BP01 --layer 1,3,1 --frequency CY \
  --start 2020 --end 2024 --format table --max-series-size 3
```

**Output**:
```
--- BPBP6KA: 対外資産負債残高（資産）/資産計 (億円) [ANNUAL] ---
  2020  11871377
  2021  13721073
  2022  15244413
  2023  16149680
  2024  17068330

--- BPBP6KAA: 対外資産負債残高（資産）/資産計/中央銀行および一般政府 (億円) [ANNUAL] ---
  ...

--- BPBP6KAB: 対外資産負債残高（資産）/資産計/中央銀行および一般政府以外 (億円) [ANNUAL] ---
  ...
```

**Value**: Annual international investment position data showing Japan's growing external assets — essential for sovereign credit analysis and understanding the structural drivers of the yen.

---

### Example L-4: "金利の預金種類別店頭表示金利を週次で取得したい"

**Business context**: A deposit pricing analyst tracking weekly changes in posted deposit rates.

**Agent executes**:
```bash
python3 scripts/boj_statistics_cli.py get-layer --db IR02 --layer "*" --frequency W \
  --start 202501 --end 202503 --format table --max-series-size 3 --max-item-length 4
```

**Output**:
```
--- DLDR43TL11MN: 定期預金　/預入金額 １千万円以上/１か月 (%) [WEEKLY(MONDAY)] ---
  ...
```

**Value**: Weekly deposit rate data is critical for ALM (Asset-Liability Management) — tracking how banks adjust posted rates in response to BOJ policy changes.
