#!/usr/bin/env python3
"""
build_remediation_config.py — AWS 作成の「FISC安全対策基準対応リファレンス」PDF
(Excel表ベース) から、是正ガイダンスに併記する **AWS対応方法案** の設定ファイル
(JSON) を決定論的に生成する。

抽出対象の列 (7列レイアウト):
  [0] 基準番号  [1] 枝番  [2] 対応主体(AWS)  [3] 対応主体(お客様)
  [4] AWSの対応状況        ← 使用しない (除外)
  [5] お客様が統制すべき内容 ← 使用する
  [6] 補足情報             ← 使用する

- FISC安対基準の本文・解説は一切取り込まない (このPDFはAWS作成の資料であり、
  取り込むのは AWS作成の col[5]/col[6] のみ)。
- 出力は 基準番号(例: 実5, 統5-1, 実14-1) をキーにした行リスト。同じ基準番号に
  複数の枝番行があればすべて保持する。
- 入力が同じなら出力は常に同一 (決定論的)。第14版が出たら本スクリプトを新PDFに
  対して実行し、--version 14 で新しい設定ファイルを生成して差し替える。

Usage:
    python3 build_remediation_config.py --pdf <AWS対応Reference.pdf> \
        --version 13 --out <config/aws_remediation_v13.json>
"""
import argparse
import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fisc_lib as L

CODE_RE = re.compile(r"^(統|実|設|監)\d+(-\d+)?$")
EMPTY = {"", "-", "―", "None"}


def clean(cell):
    """セル文字列を整形。空/ハイフンのみは空文字に。改行は保持しつつ正規化。"""
    if cell is None:
        return ""
    t = str(cell).replace("\r", "")
    t = re.sub(r"[ \t\u3000]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = t.strip()
    if t in EMPTY:
        return ""
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="AWS作成 FISC対応リファレンスPDF")
    ap.add_argument("--version", required=True, help="対応するFISC安対基準の版 (例: 13)")
    ap.add_argument("--out", required=True, help="出力JSONパス")
    ap.add_argument("--source", default=None, help="出典表記 (省略時は既定文言)")
    ap.add_argument("--pdf-sha256", default=None,
                    help="期待するAWS対応PDFのSHA-256(指定時は解析前に検証・脅威#7対策)")
    args = ap.parse_args()

    L.set_secure_umask()

    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.exit("[build_remediation_config] PyMuPDF(fitz) が必要です: pip install pymupdf")

    pdf_path = L.canonical_path(args.pdf)
    if not os.path.isfile(pdf_path):
        sys.exit(f"[build_remediation_config] ERROR: PDF が見つかりません: {pdf_path}")
    # AWS対応PDFの完全性検証(脅威 #7)。未指定でも実ハッシュを記録し provenance を残す。
    pdf_hash = L.verify_pdf_hash(pdf_path, args.pdf_sha256)
    if args.pdf_sha256:
        print(f"[build_remediation_config] PDF SHA-256 検証OK: {pdf_hash[:16]}…")
    else:
        sys.stderr.write(
            "[build_remediation_config] 注意: --pdf-sha256 未指定。AWS対応PDFの真正性は"
            f"検証されていません(実測 SHA-256: {pdf_hash})。\n"
        )

    out_path = L.guard_output_path(args.out)
    doc = fitz.open(pdf_path)
    mapping = {}      # code -> list[{branch, customer_control, supplement}]
    seen = {}         # code -> set of (customer, supplement) で重複排除
    rows_used = 0

    for pno in range(doc.page_count):
        try:
            tables = doc[pno].find_tables().tables
        except Exception:
            continue
        for t in tables:
            for r in t.extract():
                if len(r) < 7:
                    continue  # 統/実の対象行は7列。5列(設備基準等)は対象外
                code = (r[0] or "").strip()
                if not CODE_RE.match(code):
                    continue
                customer = clean(r[5])
                supplement = clean(r[6])
                if not customer and not supplement:
                    continue  # AWS対応状況しか無い行は是正ガイダンスに使わない
                branch = clean(r[1])
                key = (customer, supplement)
                if key in seen.setdefault(code, set()):
                    continue
                seen[code].add(key)
                mapping.setdefault(code, []).append({
                    "branch": branch,
                    "customer_control": customer,
                    "supplement": supplement,
                })
                rows_used += 1

    source = args.source or (
        f"金融機関向け AWS FISC安全対策基準対応リファレンス"
        f"（FISC安全対策基準・解説書 第{args.version}版 対応 / 作成: アマゾン ウェブ サービス ジャパン合同会社）"
    )
    out = {
        "fisc_version": args.version,
        "source": source,
        "generated_from": os.path.basename(pdf_path),
        "source_pdf_sha256": pdf_hash,
        "columns_used": ["お客様が統制すべき内容", "補足情報"],
        "columns_excluded": ["AWSの対応状況"],
        "codes": len(mapping),
        "rows": rows_used,
        "map": {k: mapping[k] for k in sorted(mapping)},
    }
    L.secure_write(out_path, json.dumps(out, ensure_ascii=False, indent=1))
    print(f"[build_remediation_config] 基準番号={len(mapping)} 行={rows_used} "
          f"pdf_sha256={pdf_hash[:12]}… -> {out_path}")


if __name__ == "__main__":
    main()
