# BOJ Database Catalog

Available databases in the Bank of Japan Time-Series Statistics API.
This list is based on the BOJ API manual (February 2026 edition) and is generally stable.
Use the DB name (e.g. `FM08`) as the `--db` parameter in CLI commands.

Source: BOJ API Manual § II.3.(2) DB名

## Interest Rates (金利)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| IR01 | 基準割引率および基準貸付利率の推移 | Basic Discount Rate and Basic Loan Rate |
| IR02 | 預金種類別店頭表示金利の平均年利率等 | Average Interest Rates Posted at Financial Institutions by Type of Deposit |
| IR03 | 定期預金の預入期間別平均金利 | Average Interest Rates on Time Deposits by Term |
| IR04 | 貸出約定平均金利 | Average Contracted Interest Rates on Loans and Discounts |

## Money Markets (マーケット関連)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| FM01 | 無担保コールO/N物レート | Uncollateralized Overnight Call Rate |
| FM02 | 短期金融市場金利 | Money Market Rates |
| FM03 | 短期金融市場残高 | Money Market Outstanding |
| FM04 | コール市場残高 | Call Market Outstanding |
| FM05 | 公社債発行・償還および現存額 | Issuance, Redemption and Outstanding of Bonds |
| FM06 | 公社債消化状況（利付国債） | Absorption of Government Bonds |
| FM07 | 国債窓口販売額・窓口販売率（参考） | Over-the-Counter Sales of Government Bonds (Reference) |
| FM08 | 外国為替市況 | Foreign Exchange Rates |
| FM09 | 実効為替レート | Effective Exchange Rates |

## Payment and Settlement (決済関連)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| PS01 | 各種決済 | Payment and Settlement |
| PS02 | フェイルの発生状況 | Fails in JGB Transactions |

## Deposits, Money and Lending (預金・マネー・貸出)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| MD01 | マネタリーベース | Monetary Base |
| MD02 | マネーストック | Money Stock |
| MD03 | マネタリーサーベイ | Monetary Survey |
| MD04 | マネーサプライ(M2+CD)増減と信用面の対応（参考） | Money Supply (Reference) |
| MD05 | 通貨流通高 | Currency in Circulation |
| MD06 | 日銀当座預金増減要因と金融調節 | Sources of Changes in Current Account Balances and Market Operations |
| MD07 | 準備預金額 | Reserve Requirement |
| MD08 | 業態別の日銀当座預金残高 | Current Account Balances by Sector |
| MD09 | マネタリーベースと日本銀行の取引 | Monetary Base and the Bank of Japan's Transactions |
| MD10 | 預金者別預金 | Deposits by Depositor |
| MD11 | 預金・現金・貸出金 | Deposits, Vault Cash and Loans |
| MD12 | 都道府県別預金・現金・貸出金 | Deposits, Vault Cash and Loans by Prefecture |
| MD13 | 貸出・預金動向 | Loans and Deposits |
| MD14 | 定期預金の残高および新規受入高 | Time Deposits |
| LA01 | 貸出先別貸出金 | Loans by Sector |
| LA02 | 日本銀行貸出 | Bank of Japan Loans |
| LA03 | その他貸出残高 | Other Loans Outstanding |
| LA04 | コミットメントライン契約額、利用額 | Commitment Lines |
| LA05 | 主要銀行貸出動向アンケート調査 | Senior Loan Officer Opinion Survey |

## Financial Institution Balance Sheets (金融機関バランスシート)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| BS01 | 日本銀行勘定 | Bank of Japan Accounts |
| BS02 | 民間金融機関の資産・負債 | Assets and Liabilities of Domestically Licensed Banks |

## Flow of Funds (資金循環)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| FF | 資金循環 | Flow of Funds |

## Other BOJ-related (その他の日本銀行関連)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| OB01 | 日本銀行の対政府取引 | Bank of Japan's Transactions with the Government |
| OB02 | 日本銀行が受入れている担保の残高 | Collateral Accepted by the Bank of Japan |

## Tankan Survey (短観)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| CO | 短観 | Tankan |

## Price Indices (物価)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| PR01 | 企業物価指数 | Producer Price Index |
| PR02 | 企業向けサービス価格指数 | Services Producer Price Index |
| PR03 | 製造業部門別投入・産出物価指数 | Input-Output Price Index of Manufacturing Industry |
| PR04 | 最終需要・中間需要物価指数（サテライト指数） | Final Demand-Intermediate Demand Price Index |

## Fiscal (財政関連)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| PF01 | 財政資金収支 | Fiscal Funds |
| PF02 | 政府債務 | Government Debt |

## Balance of Payments and BIS (国際収支・BIS関連)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| BP01 | 国際収支統計 | Balance of Payments |
| BIS | BIS国際資金取引統計および国際与信統計の日本分集計結果 | BIS International Banking Statistics (Japan) |
| DER | デリバティブ取引に関する定例市場報告 | Regular Derivatives Market Statistics |

## Others (その他)

| DB | Name (JP) | Name (EN) |
|----|-----------|-----------|
| OT | その他 | Others |
