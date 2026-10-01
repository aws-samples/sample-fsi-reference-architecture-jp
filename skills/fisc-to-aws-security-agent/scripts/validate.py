#!/usr/bin/env python3
"""
validate.py — 生成物 (.md) が制約を満たし、かつ改ざんされていないことを検証する。

チェック内容:
  1. **改ざん検知(脅威 #2/#6)**: classified.json + config + remediation設定から各パックの
     Markdown を **再生成し、実際の output/*.md とバイト単位で突合**する。
     一致しなければ「.md が改ざん/陳腐化している」と判定して FAIL。
     → 検証対象(=再生成結果)とアップロード対象(=実ファイル)の乖離を排除。
  2. manifest.json があれば各 .md の SHA-256 を照合(脅威 #6)。
  3. フィールド文字数: name<=80, description<=500, 他<=10000 (config field_limits)。
  4. 1パック項目数 <= max_items、.md ファイル <= 2MB。

本スクリプトは fisc_lib のみを import する(generate_packs は import しない)。
fisc_lib は import 時に副作用を持たないため、モジュール読込による任意コード実行の
経路を作らない(脅威 #5 対策)。

Usage:
    python3 validate.py --classified <classified.json> --config <pack_mapping.json> \
        --outdir <生成dir> [--format upload|manual] [--max-items 20] \
        [--remediation-config <json>] [--no-remediation]
終了コード: 全て合格なら 0、違反があれば 1。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fisc_lib as L

FILE_MAX = 2 * 1024 * 1024  # 2MB


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classified", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--format", choices=["upload", "manual"], default="upload")
    ap.add_argument("--max-items", type=int, default=20)
    ap.add_argument("--remediation-config", default=None)
    ap.add_argument("--no-remediation", action="store_true")
    args = ap.parse_args()

    L.set_secure_umask()

    data = json.load(open(L.canonical_path(args.classified), encoding="utf-8"))
    cfg = json.load(open(L.canonical_path(args.config), encoding="utf-8"))
    lim = cfg["field_limits"]
    outdir = L.canonical_path(args.outdir)
    rem = L.load_remediation(path=args.remediation_config, enable=not args.no_remediation)
    render = L.get_renderer(args.format)

    manifest = {}
    mpath = os.path.join(outdir, "manifest.json")
    if os.path.exists(mpath):
        try:
            mj = json.load(open(mpath, encoding="utf-8"))
            manifest = {f["file"]: f.get("sha256") for f in mj.get("files", [])}
        except Exception:
            manifest = {}

    errors = []
    total_items = 0

    for idx, pack in enumerate(data["packs"], start=1):
        n = len(pack["items"])
        total_items += n
        if n > args.max_items:
            errors.append(f"[項目数] {pack['id']}: {n} > {args.max_items}")

        # (1) 実 .md と再生成結果を突合 = 改ざん/陳腐化検知
        fname = f"{idx:02d}_{pack['id']}.md"
        fpath = os.path.join(outdir, fname)
        expected_md = render(pack, idx, rem["map"], rem["src"])
        if not os.path.exists(fpath):
            errors.append(f"[欠落] {fname} が存在しません")
        else:
            actual_md = open(fpath, encoding="utf-8").read()
            if actual_md != expected_md:
                errors.append(
                    f"[改ざん検知] {fname} が classified.json/config からの再生成結果と一致しません"
                    f"(生成後の編集、または陳腐化した成果物の可能性)")
            # (2) manifest の SHA-256 照合
            exp_hash = manifest.get(fname)
            if exp_hash:
                act_hash = L.sha256_text(actual_md)
                if act_hash != exp_hash:
                    errors.append(f"[SHA-256不一致] {fname}: manifest={exp_hash[:12]}… actual={act_hash[:12]}…")

        # (3) フィールド文字数
        for it in pack["items"]:
            checks = {
                "name": (L.build_name(it), lim["name"]),
                "description": (L.build_description(it), lim["description"]),
                "applicability": (L.build_applicability(it, pack), lim["applicability"]),
                "compliance": (L.build_compliance(it), lim["compliance_criteria"]),
                "remediation": (L.build_remediation(it, rem["map"], rem["src"]), lim["remediation_guidance"]),
            }
            for field, (val, mx) in checks.items():
                if len(val) > mx:
                    errors.append(f"[文字数] {pack['id']} {it['code']} {field}: {len(val)} > {mx}")

    # (4) ファイルサイズ
    for fn in sorted(os.listdir(outdir)):
        if fn.endswith(".md"):
            sz = os.path.getsize(os.path.join(outdir, fn))
            flag = "OK" if sz <= FILE_MAX else "NG"
            if sz > FILE_MAX:
                errors.append(f"[サイズ] {fn}: {sz} > {FILE_MAX}")
            print(f"  file {fn}: {sz/1024:.1f}KB [{flag}]")

    print(f"\n合計採用項目: {total_items} / パック数: {len(data['packs'])} / 除外: {len(data['excluded'])}")
    if manifest:
        print("  manifest.json の SHA-256 と照合しました。")
    print(f"  改ざん検知: 実 .md と classified/config からの再生成結果を突合しました。")
    if errors:
        print("\n❌ 検証NG:")
        for e in errors:
            print("  " + e)
        sys.exit(1)
    print("\n✅ 検証OK: 全項目がフィールド上限・項目数・サイズ制約を満たし、"
          ".md は再生成結果および manifest ハッシュと一致します。")


if __name__ == "__main__":
    main()
