#!/usr/bin/env python3
"""
generate_packs.py — 分類済み項目を AWS Security Agent Custom 取り込み用の
Markdown へ決定論的に変換する薄い CLI。生成ロジックは fisc_lib に集約。

セキュリティ:
  - PDF由来値は fisc_lib.sanitize_field で無害化(Markdown/フェンス注入対策)。
  - 出力は所有者のみ 0600(secure_write) / 出力先はツールチェーンを上書きしない。
  - manifest.json に各 .md の SHA-256 と使用した remediation 設定のハッシュを記録
    (後段 validate/upload 前の改ざん検知に使用)。

Usage:
    python3 generate_packs.py --classified <classified.json> --config <pack_mapping.json> \
        --outdir <dir> [--format upload|manual] [--remediation-config <json>] [--no-remediation]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fisc_lib as L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classified", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--format", choices=["upload", "manual"], default="upload",
                    help="upload=一括アップロード用(既定) / manual=手動コンソール登録用(フィールド別コピペ)")
    ap.add_argument("--remediation-config", default=None,
                    help="AWS対応方法案の設定JSON。未指定なら config/aws_remediation_v<最大版>.json を自動選択")
    ap.add_argument("--no-remediation", action="store_true",
                    help="AWS対応方法案の併記を無効化しFISC原文根拠のみにする")
    ap.add_argument("--remediation-sha256", default=None,
                    help="使用するremediation設定の期待SHA-256(指定時は不一致で中断・脅威#9対策)")
    args = ap.parse_args()

    L.set_secure_umask()

    rem = L.load_remediation(path=args.remediation_config, enable=not args.no_remediation)
    if args.remediation_sha256 and rem["sha256"] and \
            rem["sha256"].lower() != args.remediation_sha256.strip().lower():
        import sys as _sys
        _sys.exit(f"[security] remediation設定のSHA-256が期待値と一致しません。中断します。\n"
                  f"  expected: {args.remediation_sha256.strip().lower()}\n  actual  : {rem['sha256']}")
    if rem["path"]:
        print(f"[generate] AWS対応方法案 設定: {os.path.basename(rem['path'])} "
              f"(基準番号={len(rem['map'])}, sha256={rem['sha256'][:12]}…)")
    else:
        print("[generate] AWS対応方法案 設定: なし(FISC原文根拠のみ)")

    classified = L.canonical_path(args.classified)
    data = json.load(open(classified, encoding="utf-8"))
    outdir = L.guard_output_path(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    render = L.get_renderer(args.format)

    files = []
    for idx, pack in enumerate(data["packs"], start=1):
        md = render(pack, idx, rem["map"], rem["src"])
        fname = f"{idx:02d}_{pack['id']}.md"
        fpath = os.path.join(outdir, fname)
        L.secure_write(fpath, md)
        files.append({
            "file": fname,
            "pack": pack["name"],
            "items": len(pack["items"]),
            "bytes": len(md.encode("utf-8")),
            "sha256": L.sha256_text(md),
        })
        print(f"[generate] {fname}  項目={len(pack['items'])}  size={len(md.encode('utf-8'))/1024:.1f}KB")

    manifest = {
        "format": args.format,
        "source": L.SRC,
        "remediation_config": os.path.basename(rem["path"]) if rem["path"] else None,
        "remediation_sha256": rem["sha256"],
        "files": files,
    }
    mpath = os.path.join(outdir, "manifest.json")
    L.secure_write(mpath, json.dumps(manifest, ensure_ascii=False, indent=1))
    print(f"[generate] -> {outdir} ({len(files)} packs, manifestにSHA-256記録)")


if __name__ == "__main__":
    main()
