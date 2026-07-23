#!/usr/bin/env bash
#
# retrieve-tabulardata.sh
#
# Retrieve representative BOJ time-series data for all databases and save as
# TSV files suitable for loading into BI tools (e.g. Amazon QuickSight).
#
# Usage:
#   OUTPUT_DIR=/path/to/output ./retrieve-tabulardata.sh
#
# Environment:
#   OUTPUT_DIR  - Directory for TSV and log files (required)
#
# Scheduling:
#   Run daily via cron. Each run overwrites existing TSV files.
#   Example crontab entry:
#     0 10 * * * OUTPUT_DIR=/data/boj /path/to/retrieve-tabulardata.sh
#
# Exit codes:
#   0 - Success
#   1 - Error (see log file for details)
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

if [[ -z "${OUTPUT_DIR:-}" ]]; then
  echo "ERROR: OUTPUT_DIR environment variable is required." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CLI="${SKILL_ROOT}/scripts/boj_statistics_cli.py"
PYTHON="${PYTHON:-python3}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${OUTPUT_DIR}/retrieve-tabulardata_${TIMESTAMP}.log"

# Interval between API calls (seconds) — avoids overloading the BOJ API
REQUEST_INTERVAL=7

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

mkdir -p "${OUTPUT_DIR}"

exec > >(tee -a "${LOG_FILE}") 2>&1

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

safe_filename() {
  # Replace @ with _at_, other special chars with _
  echo "$1" | sed 's/@/_at_/g; s/[^A-Za-z0-9._-]/_/g'
}

fetch_series() {
  local db="$1"
  local code="$2"
  local desc="$3"
  local safe_code
  safe_code="$(safe_filename "${code}")"
  local outfile="${OUTPUT_DIR}/${db}-${safe_code}.tsv"

  log "Fetching: DB=${db} CODE=${code} (${desc})"

  if ! "${PYTHON}" "${CLI}" get-data \
      --db "${db}" \
      --code "${code}" \
      --format tsv \
      --output "${outfile}"; then
    log "ERROR: Failed to fetch DB=${db} CODE=${code}"
    return 1
  fi

  local lines
  lines="$(wc -l < "${outfile}" | tr -d ' ')"
  log "  -> ${outfile} (${lines} lines)"
  sleep "${REQUEST_INTERVAL}"
}

# ---------------------------------------------------------------------------
# Series definitions: DB CODE "Description"
# Each DB has 1-2 representative series selected for business relevance.
# ---------------------------------------------------------------------------

log "=== BOJ Data Retrieval Start ==="
log "Output directory: ${OUTPUT_DIR}"
log "Log file: ${LOG_FILE}"
log ""

# --- Interest Rates (金利) ---
fetch_series IR01 "MADR1Z@D"          "基準割引率および基準貸付利率 (日次)"
fetch_series IR02 "DLDR43TL41MN"      "定期預金 1千万円以上/1か月 (月次)"
fetch_series IR03 "DLDRK_DLDR442DB"   "定期預金 預入期間別平均金利 総合 (月次)"
fetch_series IR04 "DLLR2CIDBNL1"      "貸出約定平均金利 新規/総合/国内銀行 (月次)"

# --- Money Markets (マーケット関連) ---
fetch_series FM01 "STRDCLUCON"        "無担保コールO/N物レート 平均値 (日次)"
fetch_series FM01 "STRDCLUCONH"       "無担保コールO/N物レート 最高値 (日次)"
fetch_series FM02 "STRACLCOON"        "有担保コールレート翌日物 月平均 (月次)"
fetch_series FM03 "STTAK_STTA2CD1TL4" "譲渡性預金発行残高 平均残高 (月次)"
fetch_series FM04 "STTECLCTS1"        "コール市場残高 有担保 合計 末残 (月次)"
fetch_series FM04 "STTECLUTS1"        "コール市場残高 無担保 合計 末残 (月次)"
fetch_series FM05 "SMBII1OG"          "普通国債等 発行 (月次)"
fetch_series FM06 "SMTPIB"            "利付国債 消化状況 (月次)"
fetch_series FM07 "SMCSLB"            "国債窓口販売額 (月次/更新停止・参考)"
fetch_series FM08 "FXERD05"           "ドル・円 スポット 中心相場 (日次)"
fetch_series FM08 "FXERM09"           "ドル・円 スポット 中心相場 月中平均 (月次)"
fetch_series FM09 "FX180110001"       "名目実効為替レート指数 (月次)"
fetch_series FM09 "FX180110002"       "実質実効為替レート指数 (月次)"

# --- Payment and Settlement (決済関連) ---
fetch_series PS01 "PMRA4"             "日銀当座預金決済額 金額 (月次)"
fetch_series PS02 "PM090120001"       "フェイル発生状況 合計件数 (月次)"

# --- Deposits, Money and Lending (預金・マネー・貸出) ---
fetch_series MD01 "MABS1AN11"         "マネタリーベース平均残高 (月次)"
fetch_series MD02 "MAM1NAM2M2MO"      "M2 マネーストック (月次)"
fetch_series MD03 "MAS1NES1FCNT"      "マネタリーサーベイ 対外資産(純) (月次)"
fetch_series MD04 "MAMSK_MAMS4ENEM2C" "マネーサプライ増減 (月次/更新停止・参考)"
fetch_series MD05 "MACCV1"            "通貨流通高 (月次)"
fetch_series MD06 "MASDM1"            "銀行券要因 (月次)"
fetch_series MD07 "MAREM3"            "法定準備預金額 平均残高 (月次)"
fetch_series MD08 "MACAB1011"         "日銀当預残高 都市銀行 (月次)"
fetch_series MD09 "MA03021001S"       "マネタリーベース ストック表 (月次)"
fetch_series MD10 "DLDDLKY45090_DLDD3DBTTL" "預金者合計 預金合計 国内銀行 (四半期)"
fetch_series MD11 "DLCDBEDBDTTO"      "預金合計 末残 国内銀行 (月次)"
fetch_series MD12 "DLTYK209_DLTYDBTTL1" "全国計 預金合計 国内銀行 (月次)"
fetch_series MD13 "FAAP@01"           "総貸出平残 銀行・信金計 (月次)"
fetch_series MD14 "DLDTK_DLDT2FODBE"  "定期預金 末残高 総合 (月次)"

# --- Lending (貸出) ---
fetch_series LA01 "DLLILKG90_DLLI5DS2T" "総貸出 残高 国内銀行 (四半期)"
fetch_series LA02 "MABCLE@01"         "日本銀行貸出 合計 (月次)"
fetch_series LA03 "DLIRK_DLIR2DBTL"   "利率別貸出金 合計 総合 (月次)"
fetch_series LA04 "DLCM02"            "コミットメントライン 契約先数 (月次)"
fetch_series LA05 "DLLSDLPB"          "資金需要判断DI 企業向け (四半期)"

# --- Financial Institution Balance Sheets (金融機関バランスシート) ---
fetch_series BS01 "MABJMTA"           "日本銀行勘定 資産合計 (月次)"
fetch_series BS02 "FAABK_FAAB2DBEAS"  "国内銀行 資産合計 (月次)"

# --- Flow of Funds (資金循環) ---
fetch_series FF   "FOF_FFAS100A100"   "金融機関 現金・預金 ストック (四半期)"

# --- Other BOJ-related (その他の日本銀行関連) ---
fetch_series OB01 "MA03021S0001"      "政府短期証券引受残高 (月次)"
fetch_series OB02 "MA090130001"       "日銀受入担保残高 総計 (月次)"

# --- Tankan Survey (短観) ---
fetch_series CO   "TK99F1000601GCQ01000" "短観DI 業況 大企業 製造業 実績 (四半期)"
fetch_series CO   "TK99F2000601GCQ01000" "短観DI 業況 大企業 非製造業 実績 (四半期)"

# --- Price Indices (物価) ---
fetch_series PR01 "PRCG20_2200000000" "国内企業物価指数 総平均 (月次)"
fetch_series PR02 "PRCS20_5200000000" "企業向けサービス価格指数 総平均 (月次)"
fetch_series PR03 "PRIO11_6B0000000"  "製造業投入物価指数 総合 (月次/更新停止・参考)"
fetch_series PR04 "PRFI20_1FXA00000"  "最終需要物価指数 総合 (月次)"

# --- Fiscal (財政関連) ---
fetch_series PF01 "PFRP2T01"          "財政資金対民間収支 受入 (月次)"
fetch_series PF02 "PFGD1"             "政府債務合計 (月次)"

# --- Balance of Payments (国際収支) ---
fetch_series BP01 "BPBP6JYNCB"        "経常収支 (月次)"
fetch_series BP01 "BPBP6JYNTB"        "貿易収支 (月次)"

# --- Derivatives (デリバティブ) ---
fetch_series DER  "D5101010101501"    "デリバティブ想定元本 全商品計 (半期)"

# --- Others (その他) ---
fetch_series OT   "CS18011ASA"        "販売統計合成指数 (月次/更新停止・参考)"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

TSV_COUNT="$(find "${OUTPUT_DIR}" -name '*.tsv' -newer "${LOG_FILE}" -o -name '*.tsv' -samefile "${LOG_FILE}" 2>/dev/null | wc -l | tr -d ' ')"
log ""
log "=== BOJ Data Retrieval Complete ==="
log "TSV files created/updated: ${TSV_COUNT}"
log "Output directory: ${OUTPUT_DIR}"
log "Log file: ${LOG_FILE}"

exit 0
