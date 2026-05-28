import json
import re
import sys
import time
from mitmproxy import http

# ── config ──────────────────────────────────────────────────────────────────
TARGET_HOST = "localhost"
TARGET_PORT = 1234
TARGET_SCHEME = "http"

# rough tiktoken-style estimate (works for most models without importing tiktoken)
def count_tokens(text: str) -> int:
    """~4 chars per token heuristic — good enough for monitoring."""
    return max(1, len(text) // 4)

def count_tokens_messages(messages: list) -> int:
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += count_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total += count_tokens(block.get("text", "") or block.get("content", ""))
        # tool_calls
        for tc in msg.get("tool_calls", []):
            total += count_tokens(json.dumps(tc))
    return total

def count_tokens_tools(tools: list) -> int:
    return count_tokens(json.dumps(tools)) if tools else 0

# ── strip patterns ───────────────────────────────────────────────────────────
STRIP_PATTERNS = [
    (r'(?s)====\n\nCAPABILITIES\n\n.*?(?====)', ''),
    (r'(?s)====\n\nRULES\n\n.*?(?====\n\nSYSTEM INFORMATION)', ''),
    (r'(?s)====\n\nSYSTEM INFORMATION\n\n.*?(?====\n\nOBJECTIVE)', ''),
    (r'(?s)====\n\nOBJECTIVE\n\n.*?(?====\n\nUSER\'S CUSTOM)', ''),
    (r"(c:/backup/JAMBOREE_CODE_MCP.*?\n)(?:.*?c:/backup/JAMBOREE_CODE_MCP.*?\n)+", r'\1'),
]

TOOLS_TO_STRIP = {
    "skill", "new_task", "switch_mode", "update_todo_list", "read_command_output",
}
MCP_PREFIX = "mcp--"
MCP_WHITELIST = {
    "mcp--kagi-search--kagi_search",
}
# ── strippers ────────────────────────────────────────────────────────────────
def strip_system_prompt(text: str) -> str:
    for pattern, replacement in STRIP_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text

def strip_tools(tools: list) -> list:
    return [
        t for t in tools
        if t.get("function", {}).get("name", "") not in TOOLS_TO_STRIP
        and (
            not t.get("function", {}).get("name", "").startswith(MCP_PREFIX)
            or t.get("function", {}).get("name", "") in MCP_WHITELIST
        )
    ]


def strip_environment_details(messages: list) -> list:
    env_pattern = re.compile(r'(?s)<environment_details>.*?</environment_details>\n?')
    last_user_idx = max(
        (i for i, m in enumerate(messages) if m.get("role") == "user"),
        default=None
    )
    for i, msg in enumerate(messages):
        if msg.get("role") != "user" or i == last_user_idx:
            continue
        content = msg.get("content", "")
        if isinstance(content, str):
            msg["content"] = env_pattern.sub('', content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    block["text"] = env_pattern.sub('', block["text"])
    return messages

def strip_write_to_file_content(messages: list) -> list:
    for msg in messages:
        if msg.get("role") != "tool":
            continue
        content = msg.get("content", "")
        if isinstance(content, str):
            try:
                data = json.loads(content)
                if data.get("operation") in ("created", "modified"):
                    data.pop("content", None)
                    msg["content"] = json.dumps(data)
            except (json.JSONDecodeError, AttributeError):
                pass
    return messages

# ── debug printer ─────────────────────────────────────────────────────────────
def print_debug(body_before: dict, body_after: dict, raw_before: bytes, raw_after: bytes):
    sep = "─" * 60

    msgs_before = body_before.get("messages", [])
    msgs_after  = body_after.get("messages", [])
    tools_before = body_before.get("tools", [])
    tools_after  = body_after.get("tools", [])

    tok_msg_before  = count_tokens_messages(msgs_before)
    tok_msg_after   = count_tokens_messages(msgs_after)
    tok_tool_before = count_tokens_tools(tools_before)
    tok_tool_after  = count_tokens_tools(tools_after)
    tok_total_before = tok_msg_before + tok_tool_before
    tok_total_after  = tok_msg_after  + tok_tool_after

    bytes_saved = len(raw_before) - len(raw_after)
    tok_saved   = tok_total_before - tok_total_after
    pct_bytes   = (bytes_saved / len(raw_before) * 100) if raw_before else 0
    pct_tok     = (tok_saved / tok_total_before * 100) if tok_total_before else 0

    # per-role message breakdown
    role_counts_before: dict = {}
    role_counts_after:  dict = {}
    for m in msgs_before:
        r = m.get("role", "?")
        role_counts_before[r] = role_counts_before.get(r, 0) + count_tokens_messages([m])
    for m in msgs_after:
        r = m.get("role", "?")
        role_counts_after[r] = role_counts_after.get(r, 0) + count_tokens_messages([m])

    # stripped tool names
    before_names = {t.get("function", {}).get("name") for t in tools_before}
    after_names  = {t.get("function", {}).get("name") for t in tools_after}
    stripped_tools = sorted(before_names - after_names)

    model = body_before.get("model", "unknown")
    timestamp = time.strftime("%H:%M:%S")

    print(f"\n{'═'*60}", flush=True)
    print(f"  🔍 BLOAT STRIPPER  [{timestamp}]  model={model}", flush=True)
    print(sep, flush=True)

    print(f"  📦 PAYLOAD SIZE", flush=True)
    print(f"     Before : {len(raw_before):>8,} bytes", flush=True)
    print(f"     After  : {len(raw_after):>8,} bytes", flush=True)
    print(f"     Saved  : {bytes_saved:>8,} bytes  ({pct_bytes:.1f}%)", flush=True)

    print(sep, flush=True)
    print(f"  🪙 TOKEN ESTIMATE  (≈4 chars/token)", flush=True)
    print(f"  {'Component':<22} {'Before':>8} {'After':>8} {'Saved':>8}", flush=True)
    print(f"  {'─'*22} {'─'*8} {'─'*8} {'─'*8}", flush=True)

    all_roles = sorted(set(list(role_counts_before) + list(role_counts_after)))
    for role in all_roles:
        b = role_counts_before.get(role, 0)
        a = role_counts_after.get(role, 0)
        print(f"  {'msg:'+role:<22} {b:>8,} {a:>8,} {b-a:>8,}", flush=True)

    print(f"  {'tools':<22} {tok_tool_before:>8,} {tok_tool_after:>8,} {tok_tool_before-tok_tool_after:>8,}", flush=True)
    print(f"  {'─'*22} {'─'*8} {'─'*8} {'─'*8}", flush=True)
    print(f"  {'TOTAL':<22} {tok_total_before:>8,} {tok_total_after:>8,} {tok_saved:>8,}  ({pct_tok:.1f}%)", flush=True)

    print(sep, flush=True)
    print(f"  🗂  MESSAGES  before={len(msgs_before)}  after={len(msgs_after)}", flush=True)
    for i, msg in enumerate(msgs_after):
        role = msg.get("role", "?")
        toks = count_tokens_messages([msg])
        # preview first 80 chars of content
        content = msg.get("content", "")
        if isinstance(content, list):
            preview = " ".join(
                b.get("text", b.get("content", ""))[:40]
                for b in content if isinstance(b, dict)
            )
        else:
            preview = str(content)
        preview = preview.replace("\n", " ")[:80]
        tc_count = len(msg.get("tool_calls", []))
        tc_str = f"  [{tc_count} tool_call(s)]" if tc_count else ""
        print(f"     [{i:02d}] {role:<12} {toks:>5} tok  {preview!r}{tc_str}", flush=True)

    print(sep, flush=True)
    print(f"  🔧 TOOLS  before={len(tools_before)}  after={len(tools_after)}", flush=True)
    for t in tools_after:
        name = t.get("function", {}).get("name", "?")
        toks = count_tokens(json.dumps(t))
        print(f"     ✅ {name:<35} {toks:>5} tok", flush=True)
    for name in stripped_tools:
        print(f"     ❌ {name:<35} (stripped)", flush=True)

    print(f"{'═'*60}\n", flush=True)


# ── addon ─────────────────────────────────────────────────────────────────────
class BloatStripper:
    def request(self, flow: http.HTTPFlow):
        # always rewrite destination
        flow.request.host   = TARGET_HOST
        flow.request.port   = TARGET_PORT
        flow.request.scheme = TARGET_SCHEME

        if "/v1/chat/completions" not in flow.request.path:
            return
        if not flow.request.content:
            return

        try:
            body_before = json.loads(flow.request.content)
        except json.JSONDecodeError:
            return

        raw_before = flow.request.content

        # deep copy for comparison
        body_after = json.loads(raw_before)

        messages = body_after.get("messages", [])

        for msg in messages:
            if msg.get("role") == "system":
                msg["content"] = strip_system_prompt(msg["content"])

        messages = strip_environment_details(messages)
        messages = strip_write_to_file_content(messages)
        body_after["messages"] = messages

        if "tools" in body_after:
            body_after["tools"] = strip_tools(body_after["tools"])

        new_body = json.dumps(body_after, separators=(',', ':'))
        raw_after = new_body.encode('utf-8')

        print_debug(body_before, body_after, raw_before, raw_after)

        flow.request.content = raw_after
        flow.request.headers["content-length"] = str(len(raw_after))
        flow.request.headers["host"] = f"{TARGET_HOST}:{TARGET_PORT}"


addons = [BloatStripper()]
