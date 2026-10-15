#!/usr/bin/env python3
"""
run_all.py — FISC PDF から Security Agent 取り込み用ソースドキュメント一式を
一括生成するパイプライン。extract -> build -> classify -> generate -> validate。

入力が同じなら .md 出力は常に同一 (決定論的 / 再現可能)。

セキュリティ:
  - umask 0077 で全成果物を所有者限定に(脅威 #13)。
  - --pdf/--outdir を realpath 正規化し、出力先はツールチェーンを侵さない(脅威 #14)。
  - 各ステージの中間成果物と config の SHA-256 を記録し、次ステージが読む直前に
    再検証して改ざんを検知(脅威 #10/#11)。
  - 実行ごとに run_manifest(実行者/時刻/引数/入力PDF・config・中間・出力の各SHA-256)を
    出力し、append-only の run_log.jsonl に追記(脅威 #3: 否認防止・監査証跡)。
  - --pdf-sha256 を extract に引き渡し、入力PDFの真正性を検証(脅威 #7/#12)。

Usage:
    python3 run_all.py --pdf <FISC.pdf> --outdir <出力dir> [--workdir <中間dir>]
        [--format upload|manual] [--pdf-sha256 <hex>] [--max-items 20]
        [--remediation-config <json>] [--no-remediation] [--require-pymupdf]
"""
import argparse
import datetime
import getpass
import json
import os
import subprocess
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fisc_lib as L

CONFIG = os.path.join(os.path.dirname(HERE), "config", "pack_mapping.json")


def run(step, *cmd):
    print(f"\n===== [{step}] =====")
    # Safety rationale: this is a shell=False invocation. The interpreter is always
    # sys.executable and the remaining arguments are internal fixed script paths built
    # from HERE, so no external input reaches the executable name and command injection
    # is not possible.
    interpreter = [sys.executable]
    r = subprocess.run([*interpreter, *cmd])
    if r.returncode != 0:
        sys.exit(f"[run_all] 失敗: {step} (exit {r.returncode})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--workdir", default=None, help="中間ファイル出力先 (既定: <outdir>/_work)")
    ap.add_argument("--config", default=CONFIG)
    ap.add_argument("--max-items", type=int, default=20)
    ap.add_argument("--format", choices=["upload", "manual"], default="upload",
                    help="upload=一括アップロード用(既定) / manual=手動コンソール登録用")
    ap.add_argument("--pdf-sha256", default=None, help="期待する入力PDFのSHA-256(指定時は検証)")
    ap.add_argument("--remediation-config", default=None)
    ap.add_argument("--no-remediation", action="store_true")
    ap.add_argument("--remediation-sha256", default=None,
                    help="使用するremediation設定の期待SHA-256(指定時は不一致で中断・脅威#9対策)")
    ap.add_argument("--require-pymupdf", action="store_true",
                    help="PyMuPDFが使えない場合に pdftotext へフォールバックせず中断する")
    args = ap.parse_args()

    L.set_secure_umask()

    pdf = L.canonical_path(args.pdf)
    if not os.path.isfile(pdf):
        sys.exit(f"[run_all] ERROR: PDF が見つかりません: {pdf}")
    outdir = L.guard_output_path(args.outdir)
    work = L.guard_output_path(args.workdir) if args.workdir else os.path.join(outdir, "_work")
    config = L.canonical_path(args.config)
    os.makedirs(work, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)

    full = os.path.join(work, "fisc_full.txt")
    items = os.path.join(work, "items.json")
    classified = os.path.join(work, "classified.json")

    # 起点の完全性: 入力PDF と config のハッシュ
    pdf_sha = L.sha256_file(pdf)
    config_sha = L.sha256_file(config)
    rem = L.load_remediation(path=args.remediation_config, enable=not args.no_remediation)
    rem_sha = rem["sha256"]
    print(f"[run_all] 入力PDF sha256={pdf_sha[:16]}…  config sha256={config_sha[:16]}…"
          + (f"  remediation({os.path.basename(rem['path'])}) sha256={rem_sha[:16]}…" if rem["path"] else "  remediation=なし"))

    recorded = {}

    def record(path):
        recorded[path] = L.sha256_file(path)

    def verify(path, label):
        if path in recorded and os.path.exists(path):
            if L.sha256_file(path) != recorded[path]:
                sys.exit(f"[run_all] 改ざん検知: {label} がステージ間で変更されました。中断します: {path}")

    def verify_config():
        if L.sha256_file(config) != config_sha:
            sys.exit("[run_all] 改ざん検知: pack_mapping.json がステージ間で変更されました。中断します。")
        if rem["path"] and L.sha256_file(rem["path"]) != rem_sha:
            sys.exit("[run_all] 改ざん検知: aws_remediation 設定がステージ間で変更されました。中断します。")

    # 1) extract
    extract_cmd = [os.path.join(HERE, "extract_pdf.py"), "--pdf", pdf, "--out", full]
    if args.pdf_sha256:
        extract_cmd += ["--pdf-sha256", args.pdf_sha256]
    if args.require_pymupdf:
        extract_cmd += ["--require-pymupdf"]
    run("1/5 extract_pdf", *extract_cmd)
    record(full)

    # 2) build_items
    verify(full, "fisc_full.txt")
    run("2/5 build_items", os.path.join(HERE, "build_items.py"), "--text", full, "--out", items)
    record(items)

    # 3) classify
    verify(items, "items.json")
    verify_config()
    run("3/5 classify", os.path.join(HERE, "classify.py"), "--items", items,
        "--config", config, "--out", classified)
    record(classified)

    # 4) generate
    verify(classified, "classified.json")
    verify_config()
    gen_extra = ["--format", args.format]
    if args.remediation_config:
        gen_extra += ["--remediation-config", args.remediation_config]
    if args.no_remediation:
        gen_extra += ["--no-remediation"]
    if args.remediation_sha256:
        gen_extra += ["--remediation-sha256", args.remediation_sha256]
    run("4/5 generate_packs", os.path.join(HERE, "generate_packs.py"), "--classified", classified,
        "--config", config, "--outdir", outdir, *gen_extra)

    # 5) validate
    verify(classified, "classified.json")
    verify_config()
    val_extra = ["--format", args.format]
    if args.remediation_config:
        val_extra += ["--remediation-config", args.remediation_config]
    if args.no_remediation:
        val_extra += ["--no-remediation"]
    run("5/5 validate", os.path.join(HERE, "validate.py"), "--classified", classified,
        "--config", config, "--outdir", outdir, "--max-items", str(args.max_items), *val_extra)

    # 監査用 run_manifest (脅威 #3)
    out_manifest_path = os.path.join(outdir, "manifest.json")
    out_files = []
    if os.path.exists(out_manifest_path):
        try:
            out_files = json.load(open(out_manifest_path, encoding="utf-8")).get("files", [])
        except Exception:
            out_files = []
    run_manifest = {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now().astimezone().isoformat(),
        "operator": getpass.getuser(),
        "argv": sys.argv,
        "cwd": os.getcwd(),
        "format": args.format,
        "pdf": {"path": pdf, "sha256": pdf_sha, "sha256_verified": bool(args.pdf_sha256)},
        "config": {"pack_mapping": {"path": config, "sha256": config_sha},
                   "remediation": ({"path": rem["path"], "sha256": rem_sha} if rem["path"] else None)},
        "intermediates": {os.path.basename(k): v for k, v in recorded.items()},
        "outputs": out_files,
    }
    L.secure_write(os.path.join(outdir, "run_manifest.json"),
                   json.dumps(run_manifest, ensure_ascii=False, indent=1))
    logpath = os.path.join(outdir, "run_log.jsonl")
    with open(logpath, "a", encoding="utf-8") as f:
        f.write(json.dumps(run_manifest, ensure_ascii=False) + "\n")
    try:
        os.chmod(logpath, 0o600)
    except OSError:
        pass

    print(f"\n✅ 完了: {outdir} に各パックの .md を出力しました。")
    print(f"   run_id={run_manifest['run_id']} / 実行者={run_manifest['operator']} / run_manifest.json・run_log.jsonl に監査記録を保存。")
    print("   アップロード前に manifest.json の各SHA-256と実ファイルの一致を確認してください。")


if __name__ == "__main__":
    main()
