#!/usr/bin/env python3
"""
extract_pdf.py — FISC 安対基準 PDF を全文テキスト化する (決定論的)

出力は 1 行のページ区切りマーカー "===== [PDF_PAGE N] =====" 付きプレーンテキスト。

セキュリティ:
  - --pdf-sha256 を指定すると、解析前に PDF の SHA-256 を検証し不一致なら中断(脅威 #12)。
  - 入力/出力パスは realpath 正規化(脅威 #14)。出力先はツールチェーンを上書きしない。
  - PyMuPDF が使えず pdftotext にフォールバックする場合、**stderr に明示警告**し、
    抽出方式を <out>.meta.json に記録する(脅威 #1)。--require-pymupdf でフォールバック禁止。
  - pdftotext は shutil.which で解決し、許可されたシステムディレクトリ配下の
    絶対パスのみ実行する(PATH 汚染対策・脅威 #8)。
  - 出力は所有者のみ 0600(脅威 #13)。

Usage:
    python3 extract_pdf.py --pdf <input.pdf> --out <fisc_full.txt> [--pdf-sha256 <hex>] [--require-pymupdf]
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fisc_lib as L

PAGE_MARKER = "===== [PDF_PAGE {n}] ====="


def extract_with_pymupdf(pdf_path):
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    pages = [doc[i].get_text() for i in range(doc.page_count)]
    doc.close()
    return pages


def extract_with_pdftotext(pdf_path):
    binary = L.resolve_trusted_binary("pdftotext")
    if not binary:
        sys.exit(
            "[extract_pdf] ERROR: pdftotext が信頼できるシステムディレクトリ"
            f"({', '.join(L.TRUSTED_BIN_DIRS)}) に見つかりません。PATH 汚染を避けるため中断します。"
        )
    # Safety rationale: this is a shell=False invocation. The trusted absolute path
    # resolved by resolve_trusted_binary() is passed via `executable=`, while argv[0]
    # is a static literal, so no shell interpretation or command injection is possible.
    out = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", pdf_path, "-"],
        executable=binary,
        capture_output=True, text=True, check=True,
    )
    return out.stdout.split("\f"), binary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="入力 FISC PDF パス")
    ap.add_argument("--out", required=True, help="出力テキストファイルパス")
    ap.add_argument("--pdf-sha256", default=None, help="期待する入力PDFのSHA-256(指定時は検証)")
    ap.add_argument("--require-pymupdf", action="store_true",
                    help="PyMuPDFが使えない場合に pdftotext へフォールバックせず中断する")
    args = ap.parse_args()

    L.set_secure_umask()

    pdf_path = L.canonical_path(args.pdf)
    if not os.path.isfile(pdf_path):
        sys.exit(f"[extract_pdf] ERROR: PDF が見つかりません: {pdf_path}")

    # PDF 完全性検証(脅威 #12)。未指定でも実ハッシュは記録する。
    pdf_hash = L.verify_pdf_hash(pdf_path, args.pdf_sha256)
    if args.pdf_sha256:
        print(f"[extract_pdf] PDF SHA-256 検証OK: {pdf_hash[:16]}…")
    else:
        sys.stderr.write(
            "[extract_pdf] 注意: --pdf-sha256 未指定。入力PDFの真正性は検証されていません"
            f"(実測 SHA-256: {pdf_hash})。\n"
        )

    out_path = L.guard_output_path(args.out)
    fallback = False
    try:
        pages = extract_with_pymupdf(pdf_path)
        engine = "pymupdf"
        binary = None
    except Exception as e:
        if args.require_pymupdf:
            sys.exit(f"[extract_pdf] ERROR: PyMuPDF 利用不可 ({e})。--require-pymupdf のため中断します。")
        sys.stderr.write(
            "\n" + "!" * 72 + "\n"
            f"[extract_pdf] 警告: PyMuPDF 利用不可 ({e})。pdftotext にフォールバックします。\n"
            "  抽出結果が PyMuPDF と構造的に異なる可能性があります(ページ境界/文字符号化/順序)。\n"
            "  下流の抽出忠実度に影響し得るため、結果を必ず確認してください。\n"
            + "!" * 72 + "\n"
        )
        pages, binary = extract_with_pdftotext(pdf_path)
        engine = "pdftotext"
        fallback = True

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    total = 0
    buf = []
    for i, t in enumerate(pages, start=1):
        buf.append("\n" + PAGE_MARKER.format(n=i) + "\n")
        buf.append(t)
        total += len(t)
    L.secure_write(out_path, "".join(buf))

    # 抽出方式の記録(脅威 #1: フォールバックの可視化・監査)
    meta = {
        "engine": engine,
        "fallback_used": fallback,
        "pdftotext_binary": binary,
        "pages": len(pages),
        "chars": total,
        "pdf_path": pdf_path,
        "pdf_sha256": pdf_hash,
        "output_sha256": L.sha256_file(out_path),
    }
    L.secure_write(out_path + ".meta.json", json.dumps(meta, ensure_ascii=False, indent=1))

    print(f"[extract_pdf] engine={engine} pages={len(pages)} chars={total} -> {out_path}"
          + ("  (フォールバック使用)" if fallback else ""))


if __name__ == "__main__":
    main()
