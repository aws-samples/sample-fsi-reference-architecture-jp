---
name: mcp-tool-invoker
description: >-
  Reference skill for calling MCP servers via CLI tools. Other skills
  should reference this skill when they need to invoke MCP server tools from
  CLI, TypeScript, or Python. Use this skill whenever another skill needs to
  call an MCP server tool, list available MCP tools, or integrate MCP server
  capabilities into a workflow. Also use when the user asks about MCP tool
  invocation from scripts, or wants to call an MCP server from the command
  line. Trigger keywords: MCP server call, MCP tool invocation,
  MCPサーバー呼び出し, MCPツール実行, mcp-tool-invoker.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.1"
---

# mcp-tool-invoker — MCP Server Invocation Reference

This skill documents how to call MCP server tools using [mcporter](https://github.com/steipete/mcporter). It serves as a reference for other skills that need MCP server integration.

Other skills that depend on MCP server calls should reference this skill so they can adapt when the invocation method changes in the future.

## Quick Reference

```bash
# List available servers and tools
npx mcporter list
npx mcporter list <server-name>

# Call a tool
npx mcporter call <server>.<tool> key1=value1 key2=value2

# Call with JSON output (for scripting)
npx mcporter call <server>.<tool> key1=value1 --output json
```

## Output Formats

The `--output` flag controls how mcporter renders the MCP response. Understanding the difference is critical for scripting:

| Format | Output |
|--------|--------|
| `raw` | Full MCP envelope: `{content: [{type: 'text', text: '...'}]}` |
| `text` | The `content[0].text` string as-is (default) |
| `json` | `content[0].text` parsed as JSON (the MCP envelope is stripped) |
| `markdown` | Formatted for human reading |

**Key point**: With `--output json`, mcporter attempts to JSON-parse `content[0].text`. If parsing succeeds, the parsed object is output directly (the MCP envelope is stripped). If parsing fails (e.g., plain text response), the MCP envelope is returned as-is.

Example — MCP server returns JSON in `content[0].text`:
- `--output raw` → `{content: [{type: 'text', text: '{"id":"123"}'}]}`
- `--output text` → `{"id":"123"}`
- `--output json` → `{"id":"123"}` (pretty-printed, envelope stripped)

Example — MCP server returns plain text in `content[0].text`:
- `--output raw` → `{content: [{type: 'text', text: 'Hello world'}]}`
- `--output text` → `Hello world`
- `--output json` → `{"content": [{"type": "text", "text": "Hello world"}]}` (envelope kept)

With `--output json`, the top-level structure depends on what the MCP server returns. Do **not** assume a fixed key like `.data` — check the actual response of each MCP server.

### Error responses

When the MCP server returns an error, `content[0].text` is a plain error string that cannot be parsed as JSON. In this case, `--output json` returns the MCP envelope with `"isError": true`:

```json
{"content": [{"type": "text", "text": "MCP error -32602: Invalid arguments..."}], "isError": true}
```

**Note**: mcporter returns exit code 0 even when the MCP server returns an error. Check for `"isError": true` or the absence of expected keys in the response to detect errors:

```bash
# With error check
... --output json | jq 'if .isError then error(.content[0].text) else . end'
```

## Critical: Avoiding Context Overflow

MCP server output can be very large. Never run mcporter without controlling the output size. Never pipe raw output directly into the conversation context.

### When piping directly is fine

When the output size is predictable and you filter it down to a small amount of text with jq, head, etc., piping directly is fine. This avoids unnecessary temp file management and keeps things simple.

```bash
# Extract a specific field — pipe is OK
npx mcporter call <server>.<tool> args... --output json | jq '.data.someField' | head -50

# Get just the keys — pipe is OK
npx mcporter call <server>.<tool> args... --output json | jq 'keys'
```

### When to redirect to a file

Use a temp file in the following cases:

- Output size is unpredictable (e.g., fetching web pages, large record searches)
- You need to reference the same output multiple times
- You want to append incrementally (e.g., JSONL)
- You need to process the output in a script

```bash
# Save to file, then selectively read
npx mcporter call fetch.fetch url=https://example.com --output json > /tmp/mcp_result.json
jq '.data | keys' /tmp/mcp_result.json
jq '.data.someField' /tmp/mcp_result.json | head -100
```

### Anti-pattern

```bash
# WRONG — raw output flows directly into context
npx mcporter call fetch.fetch url=https://example.com
```

## Fallback: When mcporter Is Unavailable

If mcporter is not installed or `npx mcporter` fails:

1. Check if the agent already has the MCP server configured as a native tool. If so, ask the user: "mcporter is not available. You have `<tool-name>` configured as a native MCP tool. May I use it directly?"
2. If neither mcporter nor a native tool is available, ask the user to install mcporter: `npm install -g mcporter` or use `npx mcporter`.

When both mcporter and a native agent tool are available, always prefer mcporter. This ensures consistent behavior and output format across skills.

## CLI Usage

### Listing Servers and Tools

```bash
# List all configured servers
npx mcporter list

# List tools for a specific server (TypeScript-style signatures)
npx mcporter list <server-name>

# Show full parameter schemas
npx mcporter list <server-name> --schema

# JSON output for scripting
npx mcporter list <server-name> --json
```

### Calling Tools

```bash
# Key=value syntax
npx mcporter call <server>.<tool> key1=value1 key2="string value"

# Function-call syntax
npx mcporter call '<server>.<tool>(key1: "value1", key2: "value2")'

# Output formats: text (default), json, markdown, raw
npx mcporter call <server>.<tool> args... --output json

# Ad-hoc server (no config needed)
npx mcporter call --stdio "npx -y @modelcontextprotocol/server-fetch" fetch.fetch url=https://example.com --output json > /tmp/result.json
```

### Key Flags

| Flag | Description |
|------|-------------|
| `--output json` | JSON output (essential for scripting) |
| `--config <path>` | Custom config file |
| `--timeout <ms>` | Override call timeout (default 30s) |
| `--raw-strings` | Keep numeric values as strings |
| `--no-coerce` | Disable all value coercion |

### Value Coercion Pitfall

mcporter's key=value parser automatically coerces values that look like booleans or
numbers. This causes errors when a tool parameter is typed as `string` but the value
is `"true"`, `"false"`, or a number:

```bash
# FAILS: value=true is coerced to boolean, server rejects "Expected string, received boolean"
npx mcporter call my-server.update_record id="rec123" field="status" value=true
```

**Workaround 1** (recommended): Use `--no-coerce` to disable all value coercion:

```bash
npx mcporter call my-server.update_record \
  id="rec123" field="status" value=true \
  --no-coerce --config "$MCPORTER_CONFIG" --output json
```

**Workaround 2**: Use the positional function-call syntax:

```bash
npx mcporter 'my-server.update_record("rec123", "status", "true")' \
  --config "$MCPORTER_CONFIG" --output json
```

Note: `--raw-strings` only prevents number coercion, not boolean coercion.

This applies to any MCP tool where a string parameter may contain `true`, `false`,
`null`, or bare numbers.

## Using mcporter from TypeScript

```typescript
import { callOnce } from "mcporter";

// One-shot call
const result = await callOnce({
  server: "fetch",
  toolName: "fetch",
  args: { url: "https://example.com" },
});
console.log(result);

// Runtime for multiple calls
import { createRuntime, createServerProxy } from "mcporter";
const runtime = await createRuntime();
const fetch = createServerProxy(runtime, "fetch");
const page = await fetch.fetch({ url: "https://example.com" });
console.log(page.text());
await runtime.close();
```

## Using mcporter from Python

mcporter is a Node.js tool. From Python, call it via subprocess:

```python
import subprocess
import json

def mcporter_call(server: str, tool: str, args: dict, timeout: int = 60, config_path: str | None = None) -> dict:
    """Call an MCP tool via mcporter and return parsed JSON."""
    cmd = ["npx", "mcporter", "call", f"{server}.{tool}", "--output", "json"]
    if config_path:
        cmd.extend(["--config", config_path])
    for k, v in args.items():
        cmd.append(f"{k}={v}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"mcporter failed: {result.stderr}")
    return json.loads(result.stdout)

# Usage
data = mcporter_call("fetch", "fetch", {"url": "https://example.com"}, config_path="/path/to/assets/mcporter.json")
```

## For Skill Authors

If your skill needs to call MCP server tools, follow these guidelines:

1. Reference this mcp-tool-invoker skill in your SKILL.md so the agent knows how to invoke MCP tools.
2. **Bundle a default config file and always use `--config`.** mcporter looks for `./config/mcporter.json` by default, which depends on the working directory and will fail in most contexts. Your skill must include a default config file and pass it explicitly via `--config` on every mcporter invocation. See "Default Config Pattern" below for details.
3. Always control output size — never pipe raw output directly into context. Use pipes for small field extractions; use files when output size is unpredictable or you need to reuse the result (see "Avoiding Context Overflow" section for details).
4. Use `--output json` and process with jq or Python's json module.
5. Handle the fallback case where mcporter is unavailable (see "Fallback" section above).
6. When this skill's instructions change (e.g., mcporter is replaced by another tool), your skill automatically picks up the new method by re-reading this reference.

### Default Config Pattern

mcporter requires a config file that declares which MCP servers are available. Without `--config`, it searches `./config/mcporter.json` relative to the current working directory, which is unreliable. To make your skill work regardless of where it is run from:

1. **Create `assets/mcporter.json` in your skill directory** with the MCP servers your skill needs:

```
your-skill/
├── SKILL.md
├── SKILL_ja.md
└── assets/
    └── mcporter.json      ← default config bundled with the skill
```

Example `assets/mcporter.json`:
```json
{
  "mcpServers": {
    "your-mcp-server": {
      "command": "your-mcp-server-command"
    }
  }
}
```

2. **In your SKILL.md workflow, resolve the config path relative to the SKILL.md file itself and pass `--config` on every call.** The skill directory path is the directory containing the SKILL.md that the agent is currently reading. Derive the config path from that.

```bash
# The skill directory is the directory containing this SKILL.md file.
# For example, if this SKILL.md is at /path/to/your-skill/SKILL.md,
# then the config is at /path/to/your-skill/assets/mcporter.json.
# The agent already knows the SKILL.md path because it read the file.
SKILL_DIR="$(dirname /path/to/your-skill/SKILL.md)"
MCPORTER_CONFIG="$SKILL_DIR/assets/mcporter.json"

# All mcporter calls must use --config
npx mcporter call your-server.your-tool key=value --config "$MCPORTER_CONFIG" --output json
npx mcporter list your-server --config "$MCPORTER_CONFIG"
```

3. **In your SKILL.md, instruct the agent** to:
   - Derive the skill directory from the path of the SKILL.md file it is currently reading (the agent already knows this path)
   - Construct the config path as `<skill-directory>/assets/mcporter.json`
   - If the user provides a custom config path, use that instead of the default
   - Pass `--config <resolved-path>` on every `npx mcporter` invocation

This ensures the skill works out of the box without requiring the user to set up mcporter configuration separately.

## Daemon Mode (Keep-Alive Servers)

MCP servers that require expensive initialization (e.g., browser-based SSO authentication) benefit from running as a persistent daemon. mcporter's daemon keeps the server process alive between calls, preserving session caches and avoiding repeated startup costs.

### Configuration

Add `"lifecycle": "keep-alive"` to the server definition in `mcporter.json`:

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

### Daemon Commands

```bash
# Start the daemon (detaches to background)
npx mcporter daemon start --config "$MCPORTER_CONFIG"

# Check status
npx mcporter daemon status --config "$MCPORTER_CONFIG"

# Stop the daemon
npx mcporter daemon stop --config "$MCPORTER_CONFIG"

# Restart (stop + start)
npx mcporter daemon restart --config "$MCPORTER_CONFIG"
```

### How It Works

- On `daemon start`, mcporter launches the MCP server and keeps it running.
- `mcporter call` automatically routes calls through the daemon when the server has `"lifecycle": "keep-alive"`.
- The server process stays alive between calls, preserving in-memory state (auth sessions, caches).
- If the daemon is not running, `mcporter call` falls back to spawning a fresh process (slower).

### When to Use

Use daemon mode when an MCP server:
- Requires browser-based authentication (SSO/OAuth) that takes 10+ seconds
- Caches sessions in memory that expire after minutes/hours
- Has expensive startup (loading large models, establishing connections)

Example: An MCP server that authenticates via browser-based OAuth on startup. Without daemon: ~20 seconds per call for re-authentication. With daemon: ~3 seconds after initial auth.

### Debugging

```bash
# Run daemon in foreground (see all output)
npx mcporter daemon start --foreground --config "$MCPORTER_CONFIG"

# Enable logging
npx mcporter daemon start --log --config "$MCPORTER_CONFIG"

# Log specific servers only
npx mcporter daemon start --log-servers my-slow-server --config "$MCPORTER_CONFIG"
```

### Exposing Daemon Servers as a Single MCP Server

Use `mcporter serve` to expose all daemon-managed servers as one unified MCP server (useful for clients that only support a single MCP connection):

```bash
npx mcporter serve --config "$MCPORTER_CONFIG"
```

Tools are namespaced as `server__tool` (double underscore separator).

## Additional Documentation

- [mcporter GitHub repository](https://github.com/steipete/mcporter)
- [CLI Reference](https://github.com/steipete/mcporter/blob/main/docs/cli-reference.md)
- [Call Syntax](https://github.com/steipete/mcporter/blob/main/docs/call-syntax.md)
- [Ad-hoc Connections](https://github.com/steipete/mcporter/blob/main/docs/adhoc.md)
