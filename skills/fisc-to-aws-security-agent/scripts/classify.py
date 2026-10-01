#!/usr/bin/env python3
"""
classify.py — items.json を pack_mapping.json に従って 5 パックへ決定論的に分類する

selection_mode:
  include_list (既定): 各パックの include に列挙された code のみ採用。未列挙は除外。
                       完全に決定論的で「誰がやっても同じ」結果になる。
  keyword        : include で拾えない code を keywords スコアで最高スコアのパックへ。
                   同点はパック定義順で先勝ち。閾値未満は除外。

Usage:
    python3 classify.py --items <items.json> --config <pack_mapping.json> --out <classified.json>
"""
import argparse
import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fisc_lib as L


def keyword_score(text, keywords):
    return sum(len(re.findall(re.escape(k), text)) for k in keywords)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    L.set_secure_umask()

    items = json.load(open(L.canonical_path(args.items), encoding="utf-8"))
    cfg = json.load(open(L.canonical_path(args.config), encoding="utf-8"))
    packs = cfg["packs"]
    mode = cfg.get("selection_mode", "include_list")

    by_code = {it["code"]: it for it in items}

    # include の重複検証 (同一 code が複数パックにあると非決定的になる)
    seen = {}
    dup = []
    for p in packs:
        for c in p.get("include", []):
            if c in seen:
                dup.append((c, seen[c], p["id"]))
            seen[c] = p["id"]
    if dup:
        raise SystemExit(f"[classify] ERROR: include に重複 code: {dup}")

    result = {"mode": mode, "packs": [], "excluded": [], "missing_codes": []}
    assigned = set()

    for p in packs:
        chosen = []
        for c in p.get("include", []):
            if c in by_code:
                chosen.append(by_code[c])
                assigned.add(c)
            else:
                result["missing_codes"].append({"pack": p["id"], "code": c})
        result["packs"].append({
            "id": p["id"], "name": p["name"], "description": p["description"],
            "items": chosen,
        })

    # keyword フォールバック (mode=keyword のときのみ未割当を分類)
    if mode == "keyword":
        for it in items:
            if it["code"] in assigned:
                continue
            text = it["title"] + " " + it.get("summary", "")
            best, best_s = None, 0
            for p in packs:
                s = keyword_score(text, p.get("keywords", []))
                if s > best_s:
                    best, best_s = p["id"], s
            if best and best_s >= 2:
                for pk in result["packs"]:
                    if pk["id"] == best:
                        pk["items"].append(it)
                        assigned.add(it["code"])
                        break

    for it in items:
        if it["code"] not in assigned:
            result["excluded"].append(it["code"])

    L.secure_write(L.guard_output_path(args.out),
                   json.dumps(result, ensure_ascii=False, indent=1))
    print(f"[classify] mode={mode}")
    for pk in result["packs"]:
        print(f"  {pk['id']:28s} {len(pk['items']):3d} 項目  ({pk['name']})")
    print(f"  {'採用合計':28s} {sum(len(pk['items']) for pk in result['packs']):3d} 項目")
    print(f"  除外: {len(result['excluded'])} 項目 / missing(定義したが本文に無い): {len(result['missing_codes'])}")
    if result["missing_codes"]:
        print("   missing:", result["missing_codes"])
    print(f"[classify] -> {args.out}")


if __name__ == "__main__":
    main()
