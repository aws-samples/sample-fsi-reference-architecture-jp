---
name: mcp-tool-invoker
description: >-
  CLIツールを使ったMCPサーバー呼び出しのリファレンススキル。他のスキルが
  CLI、TypeScript、PythonからMCPサーバーツールを呼び出す必要がある場合に、このスキルを
  参照します。MCPサーバーツールの呼び出し、利用可能なMCPツールの一覧取得、ワークフローへの
  MCPサーバー機能の統合が必要な場合に使用します。スクリプトからのMCP
  ツール呼び出し、コマンドラインからのMCPサーバー呼び出しについてユーザーが質問した場合にも
  使用します。トリガーキーワード: MCP server call, MCP tool invocation,
  MCPサーバー呼び出し, MCPツール実行, mcp-tool-invoker.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.1"
---

# mcp-tool-invoker — MCPサーバー呼び出しリファレンス

このスキルは [mcporter](https://github.com/steipete/mcporter) を使ったMCPサーバーツールの呼び出し方法をドキュメント化しています。MCPサーバー連携が必要な他のスキルのリファレンスとして機能します。

MCPサーバー呼び出しに依存するスキルは、このスキルを参照することで、将来的に呼び出し方法が変更された場合にも対応できます。

## クイックリファレンス

```bash
# 利用可能なサーバーとツールの一覧
npx mcporter list
npx mcporter list <server-name>

# ツールの呼び出し
npx mcporter call <server>.<tool> key1=value1 key2=value2

# JSON出力（スクリプト向け）
npx mcporter call <server>.<tool> key1=value1 --output json
```

## 出力形式

`--output` フラグはmcporterがMCPレスポンスをどのようにレンダリングするかを制御します。スクリプトで使う場合、この違いの理解が重要です:

| 形式 | 出力内容 |
|------|----------|
| `raw` | MCP生エンベロープ: `{content: [{type: 'text', text: '...'}]}` |
| `text` | `content[0].text` の文字列をそのまま出力（デフォルト） |
| `json` | `content[0].text` をJSONパースした結果を出力 |
| `markdown` | 人間向けフォーマット |

**重要**: `--output json` の場合、出力はMCPエンベロープではなく**パース済みコンテンツ**です。MCPサーバーが `{content: [{text: '{"data":{"id":"123"}}'}]}` を返した場合:
- `--output raw` → `{content: [{type: 'text', text: '{"data":{"id":"123"}}'}]}`
- `--output text` → `{"data":{"id":"123"}}`
- `--output json` → `{"data":{"id":"123"}}`（整形済み）

**重要**: `--output json` の場合、mcporterは `content[0].text` のJSONパースを試みます。パースに成功すればパース済みオブジェクトを直接出力します（MCPエンベロープは除去）。パースに失敗した場合（プレーンテキストのレスポンスなど）、MCPエンベロープがそのまま返されます。

例 — MCPサーバーが `content[0].text` にJSONを返す場合:
- `--output raw` → `{content: [{type: 'text', text: '{"id":"123"}'}]}`
- `--output text` → `{"id":"123"}`
- `--output json` → `{"id":"123"}`（整形済み、エンベロープ除去）

例 — MCPサーバーが `content[0].text` にプレーンテキストを返す場合:
- `--output raw` → `{content: [{type: 'text', text: 'Hello world'}]}`
- `--output text` → `Hello world`
- `--output json` → `{"content": [{"type": "text", "text": "Hello world"}]}`（エンベロープそのまま）

`--output json` のトップレベル構造はMCPサーバーの返す内容に依存します。`.data` のような固定キーを前提に**しないでください** — 各MCPサーバーの実際のレスポンスを確認してください。

### エラーレスポンス

MCPサーバーがエラーを返した場合、`content[0].text` はJSONパースできないエラー文字列になります。この場合、`--output json` は `"isError": true` 付きのMCPエンベロープを返します:

```json
{"content": [{"type": "text", "text": "MCP error -32602: Invalid arguments..."}], "isError": true}
```

**注意**: MCPサーバーがエラーを返した場合でも、mcporterの終了コードは0です。エラー検出には `"isError": true` の有無、または期待するキーの存在確認で判定してください:

```bash
# エラーチェック付き
... --output json | jq 'if .isError then error(.content[0].text) else . end'
```

## 重要: コンテキスト溢れの回避

MCPサーバーの出力は非常に大きくなることがあります。生出力をそのままコンテキストに流し込んではいけません。

### パイプで直接処理してよい場合

出力量が予測でき、jq や head 等でフィルタして少量のテキストだけ取り出す場合は、パイプで直接つないでよい。一時ファイルの管理が不要になり簡潔になる。

```bash
# 特定フィールドだけ抽出 — パイプで OK
npx mcporter call <server>.<tool> args... --output json | jq '.data.someField' | head -50

# キー一覧だけ取得 — パイプで OK
npx mcporter call <server>.<tool> args... --output json | jq 'keys'
```

### ファイルにリダイレクトすべき場合

以下のケースでは一時ファイルに保存してから処理する:

- 出力量が予測できない（Webページ取得、大量レコード検索など）
- 同じ出力を複数回参照・使い回したい
- JSONL等で追記していきたい
- スクリプトで後続処理したい

```bash
# ファイルに保存してから選択的に読む
npx mcporter call fetch.fetch url=https://example.com --output json > /tmp/mcp_result.json
jq '.data | keys' /tmp/mcp_result.json
jq '.data.someField' /tmp/mcp_result.json | head -100
```

### NGパターン

```bash
# NG — 生出力をそのままコンテキストに流す
npx mcporter call fetch.fetch url=https://example.com
```

## フォールバック: mcporterが利用できない場合

mcporterがインストールされていない、または `npx mcporter` が失敗する場合:

1. エージェントにMCPサーバーがネイティブツールとして設定済みか確認します。設定済みの場合、ユーザーに確認します: 「mcporterが利用できません。`<tool-name>` がネイティブMCPツールとして設定されています。直接使用してよいですか？」
2. mcporterもネイティブツールも利用できない場合、ユーザーにmcporterのインストールを案内します: `npm install -g mcporter` または `npx mcporter` を使用。

mcporterとネイティブエージェントツールの両方が利用可能な場合、常にmcporterを優先します。これにより、スキル間で一貫した動作と出力形式が保証されます。

## CLI使用方法

### サーバーとツールの一覧

```bash
# 設定済みサーバーの一覧
npx mcporter list

# 特定サーバーのツール一覧（TypeScript風シグネチャ）
npx mcporter list <server-name>

# 完全なパラメータスキーマを表示
npx mcporter list <server-name> --schema

# スクリプト向けJSON出力
npx mcporter list <server-name> --json
```

### ツールの呼び出し

```bash
# key=value構文
npx mcporter call <server>.<tool> key1=value1 key2="string value"

# 関数呼び出し構文
npx mcporter call '<server>.<tool>(key1: "value1", key2: "value2")'

# 出力形式: text（デフォルト）, json, markdown, raw
npx mcporter call <server>.<tool> args... --output json

# アドホックサーバー（設定不要）
npx mcporter call --stdio "npx -y @modelcontextprotocol/server-fetch" fetch.fetch url=https://example.com --output json > /tmp/result.json
```

### 主要フラグ

| フラグ | 説明 |
|--------|------|
| `--output json` | JSON出力（スクリプトに必須） |
| `--config <path>` | カスタム設定ファイル |
| `--timeout <ms>` | タイムアウト上書き（デフォルト30秒） |
| `--raw-strings` | 数値を文字列として保持 |
| `--no-coerce` | すべての値変換を無効化 |

### 値の型変換の落とし穴

mcporterのkey=valueパーサーは、ブール値や数値に見える値を自動的に型変換します。
ツールパラメータが `string` 型なのに値が `"true"`, `"false"`, 数値の場合にエラーになります:

```bash
# 失敗: value=true がブール値に変換され、サーバーが "Expected string, received boolean" を返す
npx mcporter call my-server.update_record id="rec123" field="status" value=true
```

**回避策1**（推奨）: `--no-coerce` ですべての値変換を無効化:

```bash
npx mcporter call my-server.update_record \
  id="rec123" field="status" value=true \
  --no-coerce --config "$MCPORTER_CONFIG" --output json
```

**回避策2**: 関数呼び出し構文を使用:

```bash
npx mcporter 'my-server.update_record("rec123", "status", "true")' \
  --config "$MCPORTER_CONFIG" --output json
```

注意: `--raw-strings` は数値の型変換のみを防ぎ、ブール値の型変換は防ぎません。

これは、stringパラメータに `true`, `false`, `null`, または数値を渡す可能性があるすべてのMCPツールに該当します。

## TypeScriptからの使用

```typescript
import { callOnce } from "mcporter";

// ワンショット呼び出し
const result = await callOnce({
  server: "fetch",
  toolName: "fetch",
  args: { url: "https://example.com" },
});
console.log(result);

// 複数回呼び出し用ランタイム
import { createRuntime, createServerProxy } from "mcporter";
const runtime = await createRuntime();
const fetch = createServerProxy(runtime, "fetch");
const page = await fetch.fetch({ url: "https://example.com" });
console.log(page.text());
await runtime.close();
```

## Pythonからの使用

mcporterはNode.jsツールです。Pythonからはsubprocessで呼び出します:

```python
import subprocess
import json

def mcporter_call(server: str, tool: str, args: dict, timeout: int = 60, config_path: str | None = None) -> dict:
    """mcporter経由でMCPツールを呼び出し、パース済みJSONを返す。"""
    cmd = ["npx", "mcporter", "call", f"{server}.{tool}", "--output", "json"]
    if config_path:
        cmd.extend(["--config", config_path])
    for k, v in args.items():
        cmd.append(f"{k}={v}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"mcporter failed: {result.stderr}")
    return json.loads(result.stdout)

# 使用例
data = mcporter_call("fetch", "fetch", {"url": "https://example.com"}, config_path="/path/to/assets/mcporter.json")
```

## スキル作成者向けガイドライン

MCPサーバーツールの呼び出しが必要なスキルを作成する場合:

1. SKILL.mdでこのmcp-tool-invokerスキルを参照し、エージェントがMCPツールの呼び出し方法を把握できるようにします。
2. **デフォルト設定ファイルをスキルに同梱し、常に `--config` を指定する。** mcporterはデフォルトで `./config/mcporter.json` を探しますが、これはカレントディレクトリに依存するため、ほとんどの状況で失敗します。スキルにデフォルト設定ファイルを同梱し、すべてのmcporter呼び出しで `--config` を明示的に指定してください。詳細は下記「デフォルト設定パターン」を参照。
3. 出力制御を必ず行う — 生出力をそのままコンテキストに流さない。少量フィールド抽出ならパイプ、出力量不明・再利用ありならファイル（詳細は「コンテキスト溢れの回避」セクション参照）。
4. `--output json` を使用し、jqまたはPythonのjsonモジュールで処理します。
5. mcporterが利用できない場合のフォールバックを処理します（上記「フォールバック」セクション参照）。
6. このスキルの手順が変更された場合（例: mcporterが別のツールに置き換わった場合）、このリファレンスを再読み込みすることで自動的に新しい方法に対応できます。

### デフォルト設定パターン

mcporterは利用可能なMCPサーバーを宣言する設定ファイルが必要です。`--config` を指定しない場合、カレントディレクトリからの相対パス `./config/mcporter.json` を探しますが、これは実行場所に依存するため信頼できません。スキルがどこから実行されても動作するようにするには:

1. **スキルディレクトリ内に `assets/mcporter.json` を作成**し、スキルが必要とするMCPサーバーを定義します:

```
your-skill/
├── SKILL.md
├── SKILL_ja.md
└── assets/
    └── mcporter.json      ← スキルに同梱するデフォルト設定
```

`assets/mcporter.json` の例:
```json
{
  "mcpServers": {
    "your-mcp-server": {
      "command": "your-mcp-server-command"
    }
  }
}
```

2. **SKILL.mdのワークフローで、SKILL.mdファイル自体のパスから設定ファイルのパスを導出し、すべての呼び出しで `--config` を指定します。** スキルディレクトリは、エージェントが現在読んでいるSKILL.mdが置かれているディレクトリです。そこから設定パスを導出してください。

```bash
# スキルディレクトリは、このSKILL.mdファイルが置かれているディレクトリ。
# 例: このSKILL.mdが /path/to/your-skill/SKILL.md にある場合、
# 設定ファイルは /path/to/your-skill/assets/mcporter.json にある。
# エージェントはSKILL.mdを読んだ時点でそのパスを知っている。
SKILL_DIR="$(dirname /path/to/your-skill/SKILL.md)"
MCPORTER_CONFIG="$SKILL_DIR/assets/mcporter.json"

# すべてのmcporter呼び出しで --config を使用
npx mcporter call your-server.your-tool key=value --config "$MCPORTER_CONFIG" --output json
npx mcporter list your-server --config "$MCPORTER_CONFIG"
```

3. **SKILL.mdでエージェントに以下を指示します:**
   - 現在読んでいるSKILL.mdファイルのパスからスキルディレクトリを導出する（エージェントはファイルを読んだ時点でこのパスを知っている）
   - 設定パスを `<スキルディレクトリ>/assets/mcporter.json` として構築する
   - ユーザーがカスタム設定パスを指定した場合は、デフォルトの代わりにそちらを使用する
   - すべての `npx mcporter` 呼び出しで `--config <解決したパス>` を渡す

これにより、ユーザーが別途mcporterの設定を行わなくても、スキルがそのまま動作します。

## デーモンモード（Keep-Aliveサーバー）

ブラウザベースのSSO認証など、初期化に時間がかかるMCPサーバーは、永続デーモンとして実行することで恩恵を受けます。mcporterのデーモンはサーバープロセスを呼び出し間で維持し、セッションキャッシュを保持して繰り返しの起動コストを回避します。

### 設定

`mcporter.json`のサーバー定義に `"lifecycle": "keep-alive"` を追加:

```json
{
  "mcpServers": {
    "my-slow-server": {
      "command": "my-slow-server",
      "lifecycle": "keep-alive"
    }
  }
}
```

### デーモンコマンド

```bash
# デーモン起動（バックグラウンドにデタッチ）
npx mcporter daemon start --config "$MCPORTER_CONFIG"

# ステータス確認
npx mcporter daemon status --config "$MCPORTER_CONFIG"

# デーモン停止
npx mcporter daemon stop --config "$MCPORTER_CONFIG"

# 再起動（停止 + 起動）
npx mcporter daemon restart --config "$MCPORTER_CONFIG"
```

### 動作の仕組み

- `daemon start` でmcporterがMCPサーバーを起動し、プロセスを維持する。
- `mcporter call` はサーバーに `"lifecycle": "keep-alive"` が設定されている場合、自動的にデーモン経由でルーティングする。
- サーバープロセスは呼び出し間で生き続け、インメモリの状態（認証セッション、キャッシュ）を保持する。
- デーモンが起動していない場合、`mcporter call` は新しいプロセスを起動するフォールバックを行う（低速）。

### 使用タイミング

以下のようなMCPサーバーにデーモンモードを使用:
- ブラウザベースの認証（SSO/OAuth）で10秒以上かかる
- メモリ内にセッションをキャッシュし、分〜時間単位で期限切れになる
- 起動が重い（大きなモデルの読み込み、接続の確立）

例: ブラウザベースのOAuth認証を起動時に行うMCPサーバー。デーモンなし: 再認証のため呼び出しごとに約20秒。デーモンあり: 初回認証後は約3秒。

### デバッグ

```bash
# デーモンをフォアグラウンドで実行（全出力を確認）
npx mcporter daemon start --foreground --config "$MCPORTER_CONFIG"

# ロギング有効化
npx mcporter daemon start --log --config "$MCPORTER_CONFIG"

# 特定サーバーのみログ
npx mcporter daemon start --log-servers my-slow-server --config "$MCPORTER_CONFIG"
```

### デーモンサーバーを単一MCPサーバーとして公開

`mcporter serve` でデーモン管理下の全サーバーを統合MCPサーバーとして公開できる（単一MCP接続のみサポートするクライアント向け）:

```bash
npx mcporter serve --config "$MCPORTER_CONFIG"
```

ツールは `server__tool`（ダブルアンダースコア区切り）で名前空間化される。

## 追加ドキュメント

- [mcporter GitHubリポジトリ](https://github.com/steipete/mcporter)
- [CLIリファレンス](https://github.com/steipete/mcporter/blob/main/docs/cli-reference.md)
- [呼び出し構文](https://github.com/steipete/mcporter/blob/main/docs/call-syntax.md)
- [アドホック接続](https://github.com/steipete/mcporter/blob/main/docs/adhoc.md)
