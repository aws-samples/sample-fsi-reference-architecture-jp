#!/usr/bin/env python3
"""
fisc_lib.py — FISC → Security Agent 変換パイプラインの共有ライブラリ。

このモジュールは **import 時に副作用を持たない**（関数・定数の定義のみ。
設定の読み込みやファイル I/O は呼び出し側が明示的に行う）。これにより
validate.py などが本モジュールを import しても、悪意あるモジュールレベル
コードが実行される経路を作らない（脅威 #5 対策）。

内容:
  1. セキュリティヘルパ
     - sha256_file / sha256_text            : 整合性検証(SHA-256)
     - canonical_path / ensure_within        : パス正規化・トラバーサル防止
     - guard_output_path                     : 出力先がツールチェーン(scripts/config)を
                                               上書きしないことを保証
     - resolve_trusted_binary                : PATH汚染を避け許可ディレクトリ配下の
                                               絶対パスのみ許可(pdftotext等)
     - sanitize_field                        : PDF由来テキストのMarkdown/フェンス無害化
     - set_secure_umask / secure_write       : 権限厳格化(0600)
  2. フィールド生成 (build_*) と Markdown レンダラ (render_*)
  3. AWS対応方法案 (remediation) 設定のロード

いずれも入力が同じなら出力は同一(決定論的)。
"""
import glob
import hashlib
import json
import os
import re
import shutil

SRC = "金融機関等コンピュータシステムの安全対策基準・解説書(第13版)"

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
CONFIG_DIR = os.path.join(SKILL_ROOT, "config")

# pdftotext フォールバックで許可するシステムバイナリの所在ディレクトリ (PATH汚染対策)
TRUSTED_BIN_DIRS = ("/usr/bin", "/bin", "/usr/local/bin", "/opt/homebrew/bin", "/sbin")


# ---------------------------------------------------------------------------
# セキュリティヘルパ
# ---------------------------------------------------------------------------
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_path(path):
    """~展開 + 絶対化 + シンボリックリンク解決。トラバーサルを実体パスに正規化する。"""
    return os.path.realpath(os.path.expanduser(path))


def ensure_within(path, base):
    """path が base ディレクトリ配下(実体)にあることを保証。外れていれば SystemExit。"""
    rp = canonical_path(path)
    rb = canonical_path(base)
    if rp != rb and not rp.startswith(rb + os.sep):
        raise SystemExit(f"[security] パスが許可ベース外です: {rp} (base={rb})")
    return rp


def guard_output_path(path):
    """出力先を正規化し、SKILL の scripts/ や config/ を上書きしないことを保証(脅威 #14)。"""
    rp = canonical_path(path)
    for protected in (SCRIPTS_DIR, CONFIG_DIR):
        if rp == protected or rp.startswith(protected + os.sep):
            raise SystemExit(f"[security] 出力先がツールチェーン領域を指しています(拒否): {rp}")
    return rp


def resolve_trusted_binary(name, allowed_dirs=TRUSTED_BIN_DIRS):
    """PATH から name を解決しつつ、許可ディレクトリ配下の絶対パスのみ返す(脅威 #8)。
    見つからない/許可外なら None を返す(呼び出し側で判断)。"""
    found = shutil.which(name)
    if not found:
        return None
    rp = canonical_path(found)
    parent = os.path.dirname(rp)
    if parent in {canonical_path(d) for d in allowed_dirs}:
        return rp
    return None


def sanitize_field(text):
    """PDF由来テキストが Markdown 構造を注入するのを無害化する(脅威 #12)。
    正規のFISC本文(和文)には現れない危険シーケンスのみを対象とするため、
    正当な入力に対しては出力が変化しない(決定論・忠実性を維持)。
      - コードフェンス(``` 以上)を ZWSP で分断し fenced-block 化を阻止
      - 行頭 ATX 見出し(# ...)を ZWSP でエスケープ
      - ページ区切りマーカーの偽装を無害化
    """
    if not text:
        return text
    zwsp = "\u200b"
    text = re.sub(r"`{3,}", lambda m: zwsp.join("`" * len(m.group(0))), text)
    text = re.sub(r"(?m)^(#{1,6})(\s)", zwsp + r"\1\2", text)
    text = re.sub(r"=====\s*\[PDF_PAGE", "=" + zwsp + "====[PDF_PAGE", text)
    return text


def set_secure_umask():
    """新規作成ファイルを所有者のみ読み書き可能にする(脅威 #13)。"""
    os.umask(0o077)


def secure_write(path, text):
    """テキストを書き込み、所有者のみ 0600 に制限する(脅威 #13)。"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def verify_pdf_hash(pdf_path, expected_sha256):
    """--pdf-sha256 が与えられた場合に PDF の完全性を検証する(脅威 #7/#12)。
    戻り値は実際のSHA-256。不一致なら SystemExit。未指定(None)なら計算のみ。"""
    actual = sha256_file(pdf_path)
    if expected_sha256:
        if actual.lower() != expected_sha256.strip().lower():
            raise SystemExit(
                f"[security] PDF の SHA-256 が期待値と一致しません。中断します。\n"
                f"  expected: {expected_sha256.strip().lower()}\n  actual  : {actual}"
            )
    return actual


# ---------------------------------------------------------------------------
# AWS対応方法案 (remediation) 設定のロード ※import時には実行されない
# ---------------------------------------------------------------------------
def latest_remediation_config(config_dir=CONFIG_DIR):
    """config/aws_remediation_v<NN>.json のうち版番号が最大のものを返す(第14版差し替え対応)。"""
    best, best_ver = None, -1
    for p in glob.glob(os.path.join(config_dir, "aws_remediation_v*.json")):
        m = re.search(r"aws_remediation_v(\d+)\.json$", os.path.basename(p))
        if m and int(m.group(1)) > best_ver:
            best, best_ver = p, int(m.group(1))
    return best


def load_remediation(path=None, enable=True):
    """AWS対応方法案設定を読み込み dict を返す(グローバル状態は持たない)。
    戻り値: {"path":選択パス, "map":{...}, "src":出典, "sha256":ファイルハッシュ} または
            無効/不在時は {"path":None, "map":{}, "src":"", "sha256":None}。"""
    if not enable:
        return {"path": None, "map": {}, "src": "", "sha256": None}
    if path is None:
        path = latest_remediation_config()
    if not path or not os.path.exists(path):
        return {"path": None, "map": {}, "src": "", "sha256": None}
    data = json.load(open(path, encoding="utf-8"))
    return {
        "path": path,
        "map": data.get("map", {}),
        "src": data.get("source", ""),
        "sha256": sha256_file(path),
    }


def aws_entries(code, aws_map):
    """項目コードに対応するAWS行を返す。厳密一致 + ベースコード(-N除去)の両方を引き重複排除。"""
    entries, seen = [], set()
    base = re.sub(r"-\d+$", "", code)
    for key in ([code] if base == code else [code, base]):
        for e in aws_map.get(key, []):
            sig = (e.get("customer_control", ""), e.get("supplement", ""))
            if sig in seen:
                continue
            seen.add(sig)
            entries.append(e)
    return entries


# ---------------------------------------------------------------------------
# テキスト整形
# ---------------------------------------------------------------------------
def clip(text, limit, tail="…(以下略。出典参照)"):
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - len(tail)].rstrip() + tail


def normalize(text):
    """PDF抽出由来のノイズ(行末空白・過剰な空行)を軽く整形する(文言は不変)。"""
    text = re.sub(r"[ \t\u3000]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _celltext(text):
    """AWS対応方法案セルの整形。折返し改行は保持(URLを独立行に)し空白のみ圧縮。"""
    text = re.sub(r"[ \t\u3000]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return sanitize_field(text.strip())


def strip_koto(title):
    return re.sub(r"すること。$|こと。$|。$", "", title).strip()


def _title(it):
    return sanitize_field(it["title"].strip())


def _body(it):
    return sanitize_field(it.get("body", ""))


def gist(it):
    """summary から基準文(title)を除いた趣旨段落。無ければ title。"""
    s = it.get("summary", "").strip()
    t = it["title"].strip()
    if s.startswith(t):
        rest = s[len(t):].strip(" 　\n")
        g = rest if rest else t
    else:
        g = s or t
    return sanitize_field(g)


# ---------------------------------------------------------------------------
# フィールド生成 (build_*)
# ---------------------------------------------------------------------------
def build_name(it):
    base = f"FISC {it['code']} {strip_koto(_title(it))}"
    return clip(base, 80, tail="…")


def build_description(it):
    d = f"本要件はFISC安対基準【{it['code']}】に基づき、{gist(it)}"
    return clip(d, 500)


def build_applicability(it, pack):
    body = (
        f"本セキュリティ要件は、{SRC} のFISC【{it['code']}】"
        f"（{it['catname']}「{_title(it)}」）に対応します。\n\n"
        f"【適用対象】\n"
        f"本要件は、金融機関等が開発・運用する情報システム／ワークロード"
        f"（アプリケーション、API、バッチ処理、クラウド基盤構成、IaC を含む）のうち、"
        f"「{pack['name']}」の観点に関わる設計・実装を対象として評価します。"
        f"該当する機能・データ・通信・運用を扱う全てのワークロードに適用します。\n\n"
        f"【要件の趣旨】\n{gist(it)}\n\n"
        f"【NOT_APPLICABLE（非適用）と判断する場合】\n"
        f"- 対象ワークロードが本要件の扱う機能・データ・通信・処理を一切保持しない場合。\n"
        f"- 純粋に物理設備・建物・組織運営・人事教育のみに関する事項で、"
        f"アプリケーション設計やコードに対応する実装ポイントが存在しない場合。\n"
        f"- 当該機能を外部のマネージドサービスへ完全に委譲しており、"
        f"責任共有モデル上お客様側の設計・実装に評価対象が存在しない場合"
        f"（この場合も委譲の妥当性・設定は評価対象になり得ます）。"
    )
    return clip(body, 10000)


def build_compliance(it):
    body = (
        f"【準拠（COMPLIANT）と判断できる設計】\n"
        f"次を満たす設計・実装は本要件に準拠していると判断できます。\n"
        f"- FISC【{it['code']}】が求める「{strip_koto(_title(it))}」が、"
        f"設計または実装として具体的に確認できる。\n"
        f"- {gist(it)}\n"
        f"- 下記のFISC解説に示された着眼点が、設計上考慮されている。\n\n"
        f"【非準拠（NON_COMPLIANT）と判断する設計】\n"
        f"- 上記の制御・機能・手続きが設計／実装に存在しない、または明らかに不十分である。\n"
        f"- 該当機能を扱うにもかかわらず、FISC【{it['code']}】の趣旨に反する実装が見られる。\n\n"
        f"【FISC解説に基づく着眼点（原文根拠）】\n{_body(it)}"
    )
    return clip(body, 10000)


def build_remediation(it, aws_map=None, aws_src=""):
    aws_map = aws_map or {}
    entries = aws_entries(it["code"], aws_map)
    parts = []
    if entries:
        parts.append(
            "FISC安対基準の解説、および AWS が提示する対応方法案（お客様が統制すべき内容・補足情報）を、"
            "対象ワークロードの設計・実装に反映して是正します。"
        )
        controls = [_celltext(e["customer_control"]) for e in entries if e.get("customer_control")]
        supplements = [_celltext(e["supplement"]) for e in entries if e.get("supplement")]
        if controls:
            parts.append(
                "【AWSによる対応方法案（お客様が統制すべき内容）】\n"
                + "\n".join(f"- {c}" for c in controls)
            )
        if supplements:
            parts.append(
                "【補足情報（AWS）】\n" + "\n".join(f"- {s}" for s in supplements)
            )
        if aws_src:
            parts.append(f"（AWS対応方法案の出典: {aws_src}）")
        parts.append("【FISC解説に基づく是正事項（原文根拠）】\n" + _body(it))
    else:
        parts.append(
            "FISC安対基準の解説に示された次の事項を、対象ワークロードの設計・実装に反映して是正します。\n\n"
            + _body(it)
        )
    parts.append(f"（出典: {SRC} FISC【{it['code']}】）")
    return clip("\n\n".join(parts), 10000)


# ---------------------------------------------------------------------------
# Markdown レンダラ (upload / manual)
# ---------------------------------------------------------------------------
def render_item(it, pack, n, aws_map=None, aws_src=""):
    return (
        f"## {n}. {it['code']} {it['title']}\n\n"
        f"- **セキュリティ要件名（name）**: {build_name(it)}\n"
        f"- **説明（description）**: {build_description(it)}\n\n"
        f"### 適用性（Applicability）\n{build_applicability(it, pack)}\n\n"
        f"### コンプライアンス基準（Compliance criteria）\n{build_compliance(it)}\n\n"
        f"### 是正ガイダンス（Remediation guidance）\n{build_remediation(it, aws_map, aws_src)}\n\n"
        f"---\n\n"
    )


def render_pack(pack, idx, aws_map=None, aws_src=""):
    head = (
        f"# {pack['name']}\n\n"
        f"> AWS Security Agent Custom セキュリティ要件パック（ソースドキュメント）\n"
        f"> 出典: {SRC}\n"
        f"> 本ファイルは1項目=1セクション構成です。各セクションが1つのセキュリティ要件に対応します。\n"
        f"> パック説明: {pack['description']}\n"
        f"> 収録項目数: {len(pack['items'])}\n\n"
        f"---\n\n"
    )
    parts = [head]
    for n, it in enumerate(pack["items"], start=1):
        parts.append(render_item(it, pack, n, aws_map, aws_src))
    return "".join(parts)


def _paste_block(label, limit, content):
    content = content.strip()
    n = len(content)
    warn = "  ⚠上限超過(要短縮)" if n > limit else ""
    return (
        f"**{label}**  _（上限{limit}字 / 現在{n}字{warn}）_\n\n"
        f"```text\n{content}\n```\n\n"
    )


def render_item_manual(it, pack, n, aws_map=None, aws_src=""):
    name = build_name(it)
    desc = build_description(it)
    appl = normalize(build_applicability(it, pack))
    comp = normalize(build_compliance(it))
    reme = normalize(build_remediation(it, aws_map, aws_src))
    head = (
        f"## {n}. {it['code']} {it['title']}\n\n"
        f"- **FISC区分**: {it['catname']}（{it['code']}）　**出典ページ**: p.{it.get('page', '-')}\n"
        f"- **出典**: {SRC}\n\n"
        f"> 下の各コードブロックの中身を、Security Agent コンソールの対応フィールドへ"
        f"そのまま貼り付けてください（見出し・記号は貼り付け不要）。\n\n"
    )
    body = (
        _paste_block("① セキュリティ要件名 (name)", 80, name)
        + _paste_block("② 説明 (description)", 500, desc)
        + _paste_block("③ 適用性 (applicability)", 10000, appl)
        + _paste_block("④ コンプライアンス基準 (compliance criteria)", 10000, comp)
        + _paste_block("⑤ 是正ガイダンス (remediation guidance)", 10000, reme)
    )
    return head + body + "---\n\n"


def render_pack_manual(pack, idx, aws_map=None, aws_src=""):
    head = (
        f"# {pack['name']}（手動登録用）\n\n"
        f"> AWS Security Agent Custom セキュリティ要件パック — **手動登録用フォーマット**\n"
        f"> 出典: {SRC}\n"
        f"> 本ファイルは1項目=1セクション。各項目の5フィールドをコンソールへ"
        f"コピー&ペーストで手動登録してください（アップロードによる自動再解釈を避けるため）。\n"
        f"> フィールド上限: name 80 / description 500 / "
        f"applicability・compliance・remediation 各10000 文字。\n"
        f"> 収録項目数: {len(pack['items'])}\n\n"
        f"---\n\n"
    )
    parts = [head]
    for n, it in enumerate(pack["items"], start=1):
        parts.append(render_item_manual(it, pack, n, aws_map, aws_src))
    return "".join(parts)


def get_renderer(fmt):
    return render_pack_manual if fmt == "manual" else render_pack
