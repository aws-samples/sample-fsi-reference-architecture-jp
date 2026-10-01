#!/usr/bin/env python3
"""customer-context ストアの整合性を検証する。

使い方:
    python3 validate-store.py <データディレクトリ>
    python3 validate-store.py <データディレクトリ> --quiet   # 問題のみ出力

終了コード: 0 = 問題なし / 1 = 問題あり

検証項目
  1. ソースキー: 未定義参照 / 孤児定義 / 重複定義 / キー形式 / アンカーの対応
  2. テーブル: ヘッダと行の列数一致 / Source 欄の空 / Source 欄がキー参照形式か
  3. 人名: Name 列に敬称・肩書きが残っていないか
  4. マーカー: 角括弧形（旧形式）の残存 / エスケープされたマーカー
  5. 出所: 事実行にソースがあるか（行単位・ブロック単位・セクション単位のいずれか）
  6. Markdown: 脚注の使用 / コードフェンスとHTMLコメントの対応 / ローカルパスの直書き
"""
import collections
import glob
import os
import re
import sys

KEY_RE = r'[A-Z]{1,4}\d{4,8}[a-z]?'
MARKERS = ('unknown', 'inferred', 'unconfirmed', 'unsourced', 'no-url')
BLOCK_FIELDS = r'^- (What happened|Significance|Impact|Impact on relationship|Old|New)'
# 出所を必要としない記録項目（自分で維持する状態・識別子）
EXEMPT_FIELDS = (r'^- (Status|Current status|Last synced|Last updated|Group|Website'
                 r'|Date Added|Primary contacts?|SA Assignment|TAM|TAM Assignment|AM'
                 r'|CSM|CSM Assignment|AWS Executive Sponsor|Formal name)\b')


def strip_regions(lines):
    """コードフェンス / HTML コメントの内側を空行に置き換えた行リストを返す"""
    out = []
    infence = incomment = False
    for line in lines:
        if re.match(r'^\s*(```|````)', line):
            infence = not infence
            out.append('')
            continue
        if '<!--' in line:
            incomment = True
        if incomment:
            if '-->' in line:
                incomment = False
            out.append('')
            continue
        out.append('' if infence else line)
    return out


def tables(lines):
    """(ヘッダ行番号, ヘッダ列, [(行番号, セル列)]) を列挙"""
    i = 0
    while i < len(lines):
        if re.match(r'^\s*\|.*\|\s*$', lines[i]) and i + 1 < len(lines) \
                and re.match(r'^\s*\|[\s:|-]+\|\s*$', lines[i + 1]):
            head = [c.strip() for c in lines[i].strip().strip('|').split('|')]
            rows = []
            j = i + 2
            while j < len(lines) and re.match(r'^\s*\|.*\|\s*$', lines[j]):
                cells = [c.strip() for c in lines[j].strip().strip('|').split('|')]
                rows.append((j, cells))
                j += 1
            yield i, head, rows
            i = j
        else:
            i += 1


def check(path):
    problems = []
    with open(path) as f:
        raw = f.read()
    lines = raw.split('\n')
    vis = strip_regions(lines)

    # --- 1. ソースキー ---
    defs = collections.Counter()
    anchors = {}
    for i, line in enumerate(lines):
        m = re.match(r'^- <a id="([^"]+)"></a>\*\*([^*]+)\*\* — (.+)$', line.strip())
        if m:
            aid, key, body = m.groups()
            defs[key] += 1
            anchors[key] = aid
            if not re.fullmatch(KEY_RE, key):
                problems.append(f'L{i+1}: キー形式が規約外: {key}')
            if aid != key:
                problems.append(
                    f'L{i+1}: アンカー id とキーが不一致: id={aid} key={key}')
            if not body.strip():
                problems.append(f'L{i+1}: 定義本文が空: {key}')
    for k, n in defs.items():
        if n > 1:
            problems.append(f'キーが重複定義されている: {k} ({n}回)')
    refs = collections.Counter()
    ref_re = r'\[(' + KEY_RE + r')\]\(#(' + KEY_RE + r')\)'
    for m in re.finditer(ref_re, raw):
        refs[m.group(1)] += 1
        if m.group(1) != m.group(2):
            problems.append(
                f'参照のキーとアンカーが不一致: [{m.group(1)}](#{m.group(2)})')
    for k in refs:
        if k not in defs:
            problems.append(f'未定義のキーを参照: {k} ({refs[k]}箇所)')
    for k in defs:
        if k not in refs:
            problems.append(f'孤児の定義（参照されていない）: {k}')

    # --- 2. テーブル ---
    for hi, head, rows in tables(vis):
        for j, cells in rows:
            if len(cells) != len(head):
                problems.append(f'L{j+1}: 列数が{len(cells)}（ヘッダは{len(head)}）')
            if 'Source' in head:
                k = head.index('Source')
                v = cells[k] if k < len(cells) else ''
                if not v or v == '-':
                    problems.append(f'L{j+1}: Source 欄が空')
                elif not re.search(r'\[' + KEY_RE + r'\]\(#', v):
                    problems.append(f'L{j+1}: Source 欄がキー参照形式でない: {v[:40]}')
            # --- 3. 人名 ---
            honorific = (r'(様|さん|氏|部長|課長|本部長|社長|専務|執行役員'
                         r'|CTO|CIO|CEO|GM)$')
            if head and head[0] == 'Name' and cells and \
                    re.search(honorific, cells[0]):
                problems.append(f'L{j+1}: Name 列に敬称/肩書き: {cells[0]}')

    # --- 4. マーカー ---
    for m in re.finditer(r'\[(' + '|'.join(MARKERS) + r')\]', raw):
        problems.append(f'旧形式の角括弧マーカー: [{m.group(1)}] （波括弧に直す）')
    for m in re.finditer(r'\\\{(' + '|'.join(MARKERS) + r')\\\}', raw):
        problems.append(f'マーカーがエスケープされている: {m.group(0)}')

    # --- 5. 出所 ---
    sect = insources = False
    for i, line in enumerate(vis):
        s = line.strip()
        if s.startswith('#'):
            sect = False
            insources = bool(re.match(r'^#+\s*Sources\s*$', s))
        if insources:
            continue
        if re.match(r'^- <a id="[^"]+"></a>', s):
            continue
        if re.match(r'^Source:', s):
            sect = True
            continue
        if re.match(r'^\s*-\s+Source:', line):
            continue
        if not re.match(r'^-\s+\S', s):
            continue
        if re.match(BLOCK_FIELDS, s) or re.match(EXEMPT_FIELDS, s):
            continue
        # 事実行は行内にキー参照を持つ（または節単位 Source で覆われている）
        if re.search(r'\[' + KEY_RE + r'\]\(#', s) or sect:
            continue
        # 折り返した箇条書きは継続行にキーがあってもよい
        cont = False
        for x in vis[i + 1:]:
            if not x.strip():
                break
            if re.match(r'^\s*(-\s|#|\|)', x):
                break
            if re.search(r'\[' + KEY_RE + r'\]\(#', x):
                cont = True
                break
        if cont:
            continue
        problems.append(f'L{i+1}: 事実行に出所がない: {s[:52]}')

    # --- 5b. 散文の参照は [ ] で括る ---
    infence = False
    for i, line in enumerate(lines):
        if re.match(r'^\s*(```|````)', line):
            infence = not infence
            continue
        if infence or line.lstrip().startswith('|') \
                or re.match(r'^\s*-\s+Source:', line) \
                or re.match(r'^Source:', line) \
                or line.strip().startswith('- <a id='):
            continue
        for m in re.finditer(r'(?<!\[)\[' + KEY_RE + r'\]\(#', line):
            snippet = line.strip()[m.start():m.start() + 30]
            problems.append(f'L{i+1}: 散文の参照は [ ] で括る: {snippet}')

    # --- 6. Markdown ---
    for i, line in enumerate(vis):
        if re.match(r'^\s+-\s+Source:', line):
            problems.append(f'L{i+1}: 入れ子の - Source: は事実行の末尾へ行内で書く')
    if re.search(r'\[\^\w+\]', raw):
        problems.append('Markdown 脚注が使われている（レンダラ依存のため不可）')
    if sum(1 for line in lines if re.match(r'^\s*(```|````)', line)) % 2:
        problems.append('コードフェンスの数が奇数')
    if raw.count('<!--') != raw.count('-->'):
        problems.append('HTML コメントの開閉が不一致')
    for m in re.finditer(r'Source:[^|\n]*(~/|/Users/|C:\\\\)', raw):
        problems.append('出所にローカルパスが書かれている')
    return problems


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    quiet = '--quiet' in sys.argv
    if not args:
        print(__doc__)
        return 2
    os.chdir(args[0])
    total = 0
    files = sorted(glob.glob('**/*.md', recursive=True))
    for p in files:
        if os.path.basename(p).lower() == 'readme.md':
            continue
        pr = check(p)
        if pr:
            total += len(pr)
            print(f'\n{p}')
            for x in pr:
                print(f'  - {x}')
        elif not quiet:
            print(f'OK   {p}')
    print(f'\n検査 {len(files)} ファイル / 問題 {total} 件')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
