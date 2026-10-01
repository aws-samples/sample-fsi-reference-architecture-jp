#!/usr/bin/env python3
"""
build_items.py — FISC 全文テキストから基準項目を構造抽出する (決定論的)

抽出単位: 各基準項目 (統/実/設/監 + 主番号[-枝番])
各項目に code / cat / title / summary / body / page を付与し items.json に保存。

Usage:
    python3 build_items.py --text <fisc_full.txt> --out <items.json>
"""
import argparse
import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fisc_lib as L

CATNAME = {"統": "統制基準", "実": "実務基準", "設": "設備基準", "監": "監査基準"}

# ページ境界に繰り返し現れる定型ヘッダー/フッター行 (ノイズ除去用)
NOISE_PATTERNS = [
    r"公益財団法人金融情報システムセンター",
    r"金融機関等コンピュータシステムの安全対策基準・解説書",
    r"金融機関等コンピュータシステムの安全対策基準",
    r"（第13版）",
    r"第13\s*版",
    r"^-\s*\d+\s*-$",          # ページ番号 -92-
    r"^適\s*用\s*区\s*分$",
    r"^基準\s*$",
    r"^分類\s*$",
    r"^共\s*$", r"^セ\s*$", r"^本\s*$", r"^提\s*$", r"^ダ\s*$",
    r"^基礎\s*$", r"^◎\s*$", r"^○\s*$", r"^△\s*$",
]
NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.MULTILINE)

# 見出し項番: 直前が 【 、 数字 、 - でない (相互参照を除外)。
# 主番号のみ or 主番号-枝番。直後にタイトル (「こと。」終端) が続くもののみ採用。
ANCHOR_RE = re.compile(r"(?<![【、\d\-])(統|実|設|監)\s{1,3}(\d+)(?:-(\d+))?(?![\d\-])")


def load_pages(text_path):
    raw = open(text_path, encoding="utf-8").read()
    parts = re.split(r"===== \[PDF_PAGE (\d+)\] =====", raw)
    # parts[0] は先頭ゴミ。以降 [num, body, num, body, ...]
    seq = []  # (page_no, body)
    for i in range(1, len(parts), 2):
        seq.append((int(parts[i]), parts[i + 1]))
    return seq


def build_offset_index(seq):
    """全文連結テキストと、文字オフセット→ページ番号の境界配列を作る"""
    full = []
    bounds = []  # (start_offset, page_no)
    pos = 0
    for page_no, body in seq:
        bounds.append((pos, page_no))
        full.append(body)
        pos += len(body)
    return "".join(full), bounds


def offset_to_page(offset, bounds):
    # bounds は昇順。offset 以下で最大の start を持つページ
    lo, hi, ans = 0, len(bounds) - 1, bounds[0][1]
    while lo <= hi:
        mid = (lo + hi) // 2
        if bounds[mid][0] <= offset:
            ans = bounds[mid][1]
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


def clean(text):
    text = NOISE_RE.sub("", text)
    text = re.sub(r"[ \t\u3000]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 文中の折返し改行を連結する。段落区切り(\n\n)と、次行が番号/括弧/箇条書きで
    # 始まる改行は保持する。決定論的な整形。
    text = text.replace("\n\n", "\x00")  # 段落区切りを一時保護
    text = re.sub(
        r"(?<![。．！？：\n])\n(?!\s*(?:\d+\s*[.\)．）]|[(（]\d|[・\-*■●○�() ]|[①-⑳]))",
        "", text,
    )
    text = text.replace("\x00", "\n\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    L.set_secure_umask()
    seq = load_pages(L.canonical_path(args.text))
    full, bounds = build_offset_index(seq)

    # 見出し候補を全部集め、タイトルが「こと。」で終わるものだけ採用
    heads = []  # (start_offset, cat, major, minor, title)
    for m in ANCHOR_RE.finditer(full):
        cat, maj, mnr = m.group(1), int(m.group(2)), m.group(3)
        tail = full[m.end():m.end() + 320]
        flat = re.sub(r"\s+", "", tail)
        mt = re.match(r"(.{6,120}?こと。)", flat)
        if not mt:
            continue
        heads.append((m.start(), m.end(), cat, maj, mnr, mt.group(1)))

    # 同一 code の重複は初出のみ (一覧表など前方の再掲を排除するため本文範囲を優先)
    # 本文は各カテゴリの後半に固まるため、code ごとに最後に現れた見出しを本体とみなすと
    # 一覧表(前方)を誤採用しにくい。ただし解説が続く=本体なので、直後本文が長いものを選ぶ。
    best = {}  # code -> (score, record)
    for (s, e, cat, maj, mnr, title) in heads:
        code = f"{cat}{maj}" + (f"-{mnr}" if mnr else "")
        body_after = full[e:e + 1500]
        # 本体らしさ: 直後に解説番号 "1." や句点が多い
        score = body_after.count("。") + 5 * len(re.findall(r"\n\s*\d+\.", body_after))
        if code not in best or score > best[code][0]:
            best[code] = (score, (s, e, cat, maj, mnr, title))

    records = [v[1] for v in best.values()]
    records.sort(key=lambda r: r[0])  # 出現順

    items = []
    for idx, (s, e, cat, maj, mnr, title) in enumerate(records):
        end = records[idx + 1][0] if idx + 1 < len(records) else min(len(full), e + 6000)
        block = full[e:end]
        block_clean = clean(block)
        # 要約 = ブロック先頭から最初の解説番号 "1." まで
        msum = re.split(r"\n\s*1\s*\.", block_clean, maxsplit=1)
        summary = clean(msum[0])[:600]
        body = block_clean
        code = f"{cat}{maj}" + (f"-{mnr}" if mnr else "")
        items.append({
            "code": code,
            "cat": cat,
            "catname": CATNAME[cat],
            "major": maj,
            "minor": int(mnr) if mnr else None,
            "title": title,
            "summary": summary,
            "body": body[:8000],
            "page": offset_to_page(s, bounds),
        })

    L.secure_write(L.guard_output_path(args.out),
                   json.dumps(items, ensure_ascii=False, indent=1))
    from collections import Counter
    c = Counter(it["cat"] for it in items)
    print(f"[build_items] 抽出 {len(items)} 項目: " +
          ", ".join(f"{CATNAME[k]}={c[k]}" for k in ["統", "実", "設", "監"]))
    print(f"[build_items] -> {args.out}")


if __name__ == "__main__":
    main()
