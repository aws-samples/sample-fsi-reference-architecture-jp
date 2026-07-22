"""Constants for BOJ Statistics API.

DB_CATALOG is a local snapshot of the DB name-to-description mapping
from the BOJ API manual. It can be supplemented at runtime via the
Metadata API.
"""

BASE_URL = "https://www.stat-search.boj.or.jp/api/v1"

ENDPOINTS = {
    "code": f"{BASE_URL}/getDataCode",
    "layer": f"{BASE_URL}/getDataLayer",
    "metadata": f"{BASE_URL}/getMetadata",
}

VALID_FORMATS = ("json", "csv")
VALID_LANGS = ("jp", "en")
VALID_FREQUENCIES = ("CY", "FY", "CH", "FH", "Q", "M", "W", "D")

# Maximum series per single API request (BOJ limit)
API_MAX_SERIES_PER_REQUEST = 250
# Maximum series from layer search condition (BOJ limit)
API_MAX_LAYER_SERIES = 1250
# Maximum data points per request (series x periods)
API_MAX_DATA_POINTS = 60000

DEFAULT_REQUEST_INTERVAL = 2.0  # seconds (base for jitter)
DEFAULT_MAX_PAGES = 20

# DB name catalog (from BOJ API manual, February 2026 edition)
DB_CATALOG: dict[str, dict[str, str]] = {
    "IR01": {
        "jp": "基準割引率および基準貸付利率の推移",
        "en": "Basic Discount Rate and Basic Loan Rate",
    },
    "IR02": {
        "jp": "預金種類別店頭表示金利の平均年利率等",
        "en": "Average Interest Rates Posted at Financial Institutions by Type of Deposit",
    },
    "IR03": {
        "jp": "定期預金の預入期間別平均金利",
        "en": "Average Interest Rates on Time Deposits by Term",
    },
    "IR04": {
        "jp": "貸出約定平均金利",
        "en": "Average Contracted Interest Rates on Loans and Discounts",
    },
    "FM01": {"jp": "無担保コールO/N物レート", "en": "Uncollateralized Overnight Call Rate"},
    "FM02": {"jp": "短期金融市場金利", "en": "Money Market Rates"},
    "FM03": {"jp": "短期金融市場残高", "en": "Money Market Outstanding"},
    "FM04": {"jp": "コール市場残高", "en": "Call Market Outstanding"},
    "FM05": {
        "jp": "公社債発行・償還および現存額",
        "en": "Issuance, Redemption and Outstanding of Bonds",
    },
    "FM06": {"jp": "公社債消化状況（利付国債）", "en": "Absorption of Government Bonds"},
    "FM07": {
        "jp": "国債窓口販売額・窓口販売率（参考）",
        "en": "Over-the-Counter Sales of Government Bonds (Reference)",
    },
    "FM08": {"jp": "外国為替市況", "en": "Foreign Exchange Rates"},
    "FM09": {"jp": "実効為替レート", "en": "Effective Exchange Rates"},
    "PS01": {"jp": "各種決済", "en": "Payment and Settlement"},
    "PS02": {"jp": "フェイルの発生状況", "en": "Fails in JGB Transactions"},
    "MD01": {"jp": "マネタリーベース", "en": "Monetary Base"},
    "MD02": {"jp": "マネーストック", "en": "Money Stock"},
    "MD03": {"jp": "マネタリーサーベイ", "en": "Monetary Survey"},
    "MD04": {
        "jp": "マネーサプライ(M2+CD)増減と信用面の対応（参考）",
        "en": "Money Supply (Reference)",
    },
    "MD05": {"jp": "通貨流通高", "en": "Currency in Circulation"},
    "MD06": {
        "jp": "日銀当座預金増減要因と金融調節",
        "en": "Sources of Changes in Current Account Balances and Market Operations",
    },
    "MD07": {"jp": "準備預金額", "en": "Reserve Requirement"},
    "MD08": {"jp": "業態別の日銀当座預金残高", "en": "Current Account Balances by Sector"},
    "MD09": {
        "jp": "マネタリーベースと日本銀行の取引",
        "en": "Monetary Base and the Bank of Japan's Transactions",
    },
    "MD10": {"jp": "預金者別預金", "en": "Deposits by Depositor"},
    "MD11": {"jp": "預金・現金・貸出金", "en": "Deposits, Vault Cash and Loans"},
    "MD12": {
        "jp": "都道府県別預金・現金・貸出金",
        "en": "Deposits, Vault Cash and Loans by Prefecture",
    },
    "MD13": {"jp": "貸出・預金動向", "en": "Loans and Deposits"},
    "MD14": {"jp": "定期預金の残高および新規受入高", "en": "Time Deposits"},
    "LA01": {"jp": "貸出先別貸出金", "en": "Loans by Sector"},
    "LA02": {"jp": "日本銀行貸出", "en": "Bank of Japan Loans"},
    "LA03": {"jp": "その他貸出残高", "en": "Other Loans Outstanding"},
    "LA04": {"jp": "コミットメントライン契約額、利用額", "en": "Commitment Lines"},
    "LA05": {"jp": "主要銀行貸出動向アンケート調査", "en": "Senior Loan Officer Opinion Survey"},
    "BS01": {"jp": "日本銀行勘定", "en": "Bank of Japan Accounts"},
    "BS02": {
        "jp": "民間金融機関の資産・負債",
        "en": "Assets and Liabilities of Domestically Licensed Banks",
    },
    "FF": {"jp": "資金循環", "en": "Flow of Funds"},
    "OB01": {
        "jp": "日本銀行の対政府取引",
        "en": "Bank of Japan's Transactions with the Government",
    },
    "OB02": {
        "jp": "日本銀行が受入れている担保の残高",
        "en": "Collateral Accepted by the Bank of Japan",
    },
    "CO": {"jp": "短観", "en": "Tankan"},
    "PR01": {"jp": "企業物価指数", "en": "Producer Price Index"},
    "PR02": {"jp": "企業向けサービス価格指数", "en": "Services Producer Price Index"},
    "PR03": {
        "jp": "製造業部門別投入・産出物価指数",
        "en": "Input-Output Price Index of Manufacturing Industry",
    },
    "PR04": {
        "jp": "最終需要・中間需要物価指数（サテライト指数）",
        "en": "Final Demand-Intermediate Demand Price Index",
    },
    "PF01": {"jp": "財政資金収支", "en": "Fiscal Funds"},
    "PF02": {"jp": "政府債務", "en": "Government Debt"},
    "BP01": {"jp": "国際収支統計", "en": "Balance of Payments"},
    "BIS": {
        "jp": "BIS国際資金取引統計および国際与信統計の日本分集計結果",
        "en": "BIS International Banking Statistics (Japan)",
    },
    "DER": {
        "jp": "デリバティブ取引に関する定例市場報告",
        "en": "Regular Derivatives Market Statistics",
    },
    "OT": {"jp": "その他", "en": "Others"},
}
