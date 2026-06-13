"""
Google Voice API via raw Chrome DevTools Protocol (CDP).

Modes:
  (default)         Ingestion worker — writes normalized JSON to .staging_queue/inbox_sms.json
                    (feeds Protocol-AI orchestrator pipeline, dedup via ledger)
  --reply-to "name" Smart reply — resolves person name to thread, then sends message

Built from live DOM probing — no libraries, just WebSocket + JSON-RPC.
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(SCRIPT_DIR, "Default_GV")
LOG_FILE = os.path.join(SCRIPT_DIR, "gv_log.jsonl")

# Protocol-AI integration paths
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # PROTOCAL-AI/
BROWSER_PATH = os.path.join(os.environ.get("HOME", "."), "node", "Chromium", "Application", "chrome.exe")
VAULT_ROOT = os.path.join(PROJECT_ROOT, "Vault")
STAGING_DIR = os.path.join(VAULT_ROOT, ".staging_queue")
LEDGER_PATH = os.path.join(STAGING_DIR, ".last_run_ledger.json")


# ---------------------------------------------------------------------------
# CDP Client — raw WebSocket JSON-RPC
# ---------------------------------------------------------------------------

class CDPClient:
    """Raw Chrome DevTools Protocol client."""

    def __init__(self):
        self.ws = None
        self._mid = 0

    async def _send(self, method: str, params: dict | None = None) -> dict:
        self._mid += 1
        await self.ws.send(json.dumps({"id": self._mid, "method": method, "params": params or {}}))
        for _ in range(50):
            resp = json.loads(await self.ws.recv())
            if isinstance(resp, dict) and resp.get("id") == self._mid:
                return resp.get("result", {})

    async def ev(self, expr: str) -> any:
        """Evaluate JavaScript returning parsed JSON value."""
        r = await self._send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        if "result" in r:
            return json.loads(r["result"]["value"])
        return {}

    async def navigate(self, url: str):
        await self._send("Page.navigate", {"url": url})


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class MessageResult:
    success: bool
    thread_id: str = ""
    body: str = ""
    timestamp: float = 0.0
    error: Optional[str] = None


@dataclass
class Conversation:
    thread_id: str
    thread_url: str          # full URL with itemId (e.g. t.+1678... or g.Group%20Message.F9ePpy...)
    thread_type: str         # "direct" | "group" | "voicemail"
    participants: list[str]
    last_message: str
    timestamp: str           # relative from DOM ("5:12 PM")
    iso_timestamp: str       # ISO 8601 UTC (computed)
    snippet: str = ""
    messages: list[dict] = ()  # [{from, text, direction}] for richer context
    message_count: int = 0     # total messages in thread (for AI context depth)


@dataclass
class Voicemail:
    phone: str
    timestamp: str
    iso_timestamp: str
    transcription: str
    raw_text: str = ""


# ---------------------------------------------------------------------------
# Logging — append every action to JSONL timeline
# ---------------------------------------------------------------------------

def log_action(action: str, **kwargs):
    """Append a timestamped entry to gv_log.jsonl."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        **kwargs,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def clean(text: str) -> str:
    """Strip Unicode directional formatting characters from text."""
    return text.replace("\u202a", "").replace("\u202c", "").replace("\u200b", "")


def output(data: dict):
    """Print JSON to stdout."""
    print(json.dumps(data))


# ---------------------------------------------------------------------------
# Timestamp helper — convert relative time to ISO 8601 UTC
# ---------------------------------------------------------------------------

def resolve_timestamp(relative_time: str) -> str:
    """Convert Google Voice relative timestamp to ISO 8601 UTC.

    Handles: '5:12 PM', 'Tue 5:29 PM', 'Jun 3, 11:57 AM', 'May 27, 4:30 PM'
    """
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    this_year = str(now.year)

    # Normalize narrow spaces to regular spaces
    t = relative_time.replace("\u202f", " ").strip()

    formats = [
        ("%I:%M %p", today_str),           # 5:12 PM → today
        ("%I%p", today_str),               # 512PM → today
        ("%a %I:%M %p", today_str),       # Tue 5:29 PM → today
        ("%b %-d, %I:%M %p", this_year),   # Jun 3, 11:57 AM
        ("%B %-d, %I:%M %p", this_year),   # June 3, 11:57 AM
    ]

    for fmt, prefix in formats:
        try:
            dt = datetime.strptime(f"{prefix} {t}", f"%Y-%m-%d {fmt}" if prefix != this_year else f"%Y %b %-d, %I:%M %p")
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue

    # Fallback: use current time if parsing fails
    return now.isoformat()


# ---------------------------------------------------------------------------
# Ledger — dedup tracking across runs
# ---------------------------------------------------------------------------

def load_ledger() -> dict:
    """Load last-run ledger (tracks google_voice sync timestamp)."""
    try:
        with open(LEDGER_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_ledger(ledger: dict):
    """Save updated ledger."""
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "w") as f:
        json.dump(ledger, f, indent=2)


# ---------------------------------------------------------------------------
# Browser launcher
# ---------------------------------------------------------------------------

async def launch_browser(debug_port: int = 9222, headless: bool = True) -> tuple[str, asyncio.subprocess.Process]:
    """Launch Chrome with CDP and return WS URL + process."""
    import urllib.request
    # Check if Chrome is already running on our debug port — reuse it
    try:
        data = urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json").read()
        info = json.loads(data)
        for t in info:
            if t["type"] == "page":
                return t["webSocketDebuggerUrl"], None  # reuse existing
    except Exception:
        pass

    flags = [
        f"--remote-debugging-port={debug_port}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--no-sandbox", "--lang=en-US",
    ]
    if headless:
        flags.append("--headless=new")

    proc = await asyncio.create_subprocess_exec(
        BROWSER_PATH,
        *flags,
        "https://voice.google.com/u/0/messages",
    )

    for _ in range(30):
        try:
            data = urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json").read()
            info = json.loads(data)
            for t in info:
                if t["type"] == "page" and "DevTools" not in t.get("title", ""):
                    return t["webSocketDebuggerUrl"], proc
            break
        except Exception:
            await asyncio.sleep(0.5)

    raise RuntimeError("Chrome failed to start")


# ---------------------------------------------------------------------------
# Google Voice API
# ---------------------------------------------------------------------------

class GoogleVoiceCDP:
    """Google Voice API via raw CDP."""

    MESSAGES_URL = "https://voice.google.com/u/0/messages"
    VOICEMAIL_URL = "https://voice.google.com/u/0/voicemail"

    def __init__(self, debug_port: int = 9222, headless: bool = True):
        self.port = debug_port
        self.headless = headless
        self.client: CDPClient | None = None
        self.proc = None

    async def connect(self) -> bool:
        """Launch Chrome and connect via CDP."""
        import websockets

        ws_url, proc = await launch_browser(self.port, self.headless)
        self.proc = proc

        self.client = CDPClient()
        self.client.ws = await websockets.connect(ws_url)

        await asyncio.sleep(5)

        state = await self.client.ev("JSON.stringify({url:location.href,title:document.title})")
        log_action("connect", title=state.get("title"), url=state.get("url"))
        output({"status": "connected", "title": state.get("title"), "url": state.get("url")})
        return True

    async def disconnect(self):
        if self.client and self.client.ws:
            await self.client.ws.close()
        if self.proc:
            self.proc.terminate()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc):
        await self.disconnect()

    # ---- read conversations -----------------------------------------------

    async def get_conversations(self, limit: int = 10) -> list[Conversation]:
        """Get recent conversation threads with full context.

        Classifies each thread by type:
          - "direct":  two-party chat (itemId starts with t.)
          - "group":   group text (itemId starts with g.)
          - "voicemail": voicemail messages (from /voicemail page)

        Each Conversation includes:
          - thread_url: full URL for re-opening the thread
          - thread_type: classification for AI routing
          - messages: list of {from, text, direction} dicts for conversation history
          - message_count: total incoming message count (context depth indicator)
        """
        await self.client.navigate(self.MESSAGES_URL)
        await asyncio.sleep(3)

        # Step 1: Get thread list with URLs, participants, and type classification
        js_code = r"""JSON.stringify(
            Array.from(document.querySelectorAll('li.list-item'))
                .map(el => {
                    const text = el.innerText.trim();
                    const lines = text.split('\n').map(l=>l.trim()).filter(Boolean);
                    // Skip icon-only lines
                    const content = lines.filter(l => !/^(person|R|J|C|M|A|V|T|B|K|D)$/.test(l));

                    // Get participants from annotation element (handles groups properly)
                    const annEl = el.querySelector('gv-annotation.participants');
                    const rawParticipants = annEl ? annEl.innerText.trim() : content[0] || '';
                    const participants = rawParticipants.split(',').map(p=>p.trim()).filter(Boolean);

                    // Extract thread URL from the link to get itemId for type classification
                    const link = el.querySelector('a[href*="itemId"]');
                    const href = link ? link.getAttribute('href') : '';
                    const itemId = new URLSearchParams(href.split('?')[1] || '').get('itemId') || '';

                    // Classify thread type from itemId prefix
                    let threadType = 'direct';  // default: two-party chat (t.)
                    if (itemId.startsWith('g.')) {
                        threadType = 'group';    // group text (g.)
                    }

                    const phone = content.find(l => /\(?[0-9]{3}\)?/.test(l)) || '';
                    const timestamp = content.find(l => /[apAP][mM]$/.test(l)) || '';

                    return {participants, threadUrl: href, itemId, threadType, phone, timestamp};
                }).slice(0, LIMIT_PLACEHOLDER)
        )"""
        js_code = js_code.replace("LIMIT_PLACEHOLDER", str(limit))

        threads_meta = await self.client.ev(js_code)

        # Step 2: For each thread, click into it and extract messages with sender info
        MAX_MSGS_PER_THREAD = 8  # increased for richer AI context
        convs = []
        for idx, meta in enumerate(threads_meta):
            # Click on this thread to open it
            await self.client._send("Runtime.evaluate", {
                "expression": f"document.querySelectorAll('li.list-item')[{idx}].querySelector('.thread-info-content, .thread-details, a').click()",
                "returnByValue": True
            })
            await asyncio.sleep(2)

            # Extract ALL messages (incoming + outgoing) with sender/direction info
            # This gives AI full conversation context to decide actions
            bubbles_js = r"""JSON.stringify(
                Array.from(document.querySelectorAll('.full-container'))
                    .map(el => {
                        const bubble = el.querySelector('.bubble');
                        if (!bubble) return null;
                        const text = bubble.innerText.trim();
                        // Determine direction: outgoing has 'outgoing' class, incoming has 'incoming'
                        const isOutgoing = el.classList.contains('outgoing') || el.classList.contains('sent');
                        const isIncoming = el.classList.contains('incoming') || el.classList.contains('received');

                        // Try multiple selectors for sender name (Google Voice uses different classes)
                        let sender = '';
                        if (!isOutgoing) {
                            // PRIMARY: Look for hidden accessibility div with "Message from X, ..."
                            const hiddenDiv = el.querySelector('.cdk-visually-hidden');
                            if (hiddenDiv) {
                                const match = hiddenDiv.innerText.match(/^Message from\s+(.+?),/i);
                                if (match) sender = match[1].trim();
                            }
                            // FALLBACK: Check all possible sender-name locations inside the message container
                            if (!sender) {
                                const candidates = [
                                    '.participant',
                                    '.sender-name',
                                    '[class*="from"]',
                                    '[class*="name"]',
                                    'span[class*="participant"]',
                                    'div[class*="label"]',
                                    '.message-sender',
                                ];
                                for (const sel of candidates) {
                                    const found = el.querySelector(sel);
                                    if (found && found.innerText.trim().length > 0) {
                                        sender = found.innerText.trim();
                                        break;
                                    }
                                }
                            }
                            // LAST RESORT: try ALL spans/divs for phone numbers or names
                            if (!sender) {
                                const allChildren = Array.from(el.querySelectorAll('span, div'));
                                for (const child of allChildren) {
                                    const t = child.innerText.trim();
                                    // Look for phone number patterns or non-empty labels
                                    if (/\(?[0-9]{3}\)?/.test(t) || /^[A-Z][a-z]/.test(t)) {
                                        // Extract just the first line (sender name/phone, not timestamp/message)
                                        const lines = t.split('\n').map(l=>l.trim()).filter(Boolean);
                                        let s = lines[0] || t;
                                        // Strip "Message from X, ..." prefix to get clean sender
                                        const match2 = s.match(/^Message from\s+(.+?),/i);
                                        if (match2) s = match2[1].trim();
                                        sender = s;
                                        break;
                                    }
                                }
                            }
                        }

                        return {text: text || '', direction: isOutgoing ? 'outgoing' : (isIncoming ? 'incoming' : 'unknown'), from: sender};
                    })
                    .filter(m => m && m.text.length > 0)
            )"""
            all_messages = await self.client.ev(bubbles_js) or []

            # Determine the "other person" label for direct threads (fallback when DOM has no sender)
            # For direct chats: participants list may include phone numbers, "+N", and MFA labels
            # Strip those to get clean name(s). If only 1 real name remains, use it as fallback.
            import re as _re
            participant_names = [
                p for p in meta.get("participants", [])
                if not _re.match(r'^\(?[0-9]', p)   # strip phone numbers like (207)... or +1...
                and 'MFA' not in p                    # strip MFA labels
                and not _re.match(r'^\+\d+$', p)     # strip "+4" style group indicators
            ]
            direct_other_name = participant_names[0] if len(participant_names) == 1 else ""

            # Build a set of known phone numbers from participants (for group chat sender matching)
            participant_phones = [
                p for p in meta.get("participants", [])
                if _re.match(r'^\(?[0-9]', p) and 'MFA' not in p
            ]

            # Filter out noise: reactions, emoji-only, liked/disliked messages
            clean_msgs = []
            for msg in all_messages:
                text = msg["text"]
                text_stripped = text.strip()
                text_lower = text_stripped.lower()
                # Skip reaction-only entries (Loved, Liked, Reacted, Laughed, Disliked)
                if text_lower.startswith(("loved", "liked", "reacted", "laughed", "disliked")):
                    continue
                # Skip emoji-only messages (strip all non-emoji chars and check)
                stripped = _re.sub(r'[\w\s]', '', text).strip()
                if len(text) <= 4 and not text.isascii():
                    continue
                # Skip "to \"...\"" reaction references (Google Voice reaction metadata)
                if text_lower.startswith("to "):
                    continue
                if len(msg["text"]) > 0:
                    sender_label = msg.get("from", "")
                    # Normalize sender: strip ALL whitespace variants (regular, zero-width, thin spaces) for phone matching
                    sender_cleaned = _re.sub(r'[\s\u200b\u200a\u200c\u200d\ufeff]+', '', sender_label)
                    if not sender_label:
                        # Fallback: use direct chat partner name, or "You" for outgoing
                        if msg["direction"] == "outgoing":
                            sender_label = "You"
                        elif direct_other_name:
                            sender_label = direct_other_name
                        else:
                            sender_label = "Other"
                    # Normalize phone-like senders to standard (XXX) XXX-XXXX format
                    # Strip everything except digits for comparison
                    sender_digits = _re.sub(r'[^\d]', '', sender_label)
                    if len(sender_digits) == 10:
                        # Format as (XXX) XXX-XXXX
                        sender_label = f"({sender_digits[:3]}) {sender_digits[3:6]}-{sender_digits[6:]}"
                    elif participant_phones and sender_digits:
                        matched_phone = None
                        for p in participant_phones:
                            p_digits = _re.sub(r'[^\d]', '', p)
                            if p_digits and sender_digits == p_digits:
                                matched_phone = p
                                break
                        if matched_phone:
                            sender_label = matched_phone
                    clean_msgs.append({
                        "from": sender_label,
                        "text": msg["text"],
                        "direction": msg["direction"],
                    })

            # Take last N messages for AI context window
            recent = clean_msgs[-MAX_MSGS_PER_THREAD:] if clean_msgs else []
            snippet = recent[-1]["text"] if recent else (meta["participants"][0] if meta.get("participants") else "")

            convs.append(Conversation(
                thread_id=meta.get("itemId", f"thread_{idx}"),
                thread_url=meta.get("threadUrl", self.MESSAGES_URL),
                thread_type=meta.get("threadType", "direct"),
                participants=[clean(p) for p in meta.get("participants", [])],
                last_message=clean(snippet),
                timestamp=meta.get("timestamp", ""),
                iso_timestamp=resolve_timestamp(meta.get("timestamp", "now")),
                snippet=clean(snippet),
                messages=[{"from": clean(m["from"]), "text": clean(m["text"]), "direction": m["direction"]} for m in recent],
                message_count=len(clean_msgs),  # total incoming count for context depth
            ))

            # Navigate back to list view for next thread
            await self.client.navigate(self.MESSAGES_URL)
            await asyncio.sleep(2)

        log_action("conversations_read", count=len(convs), threads=[c.participants[0] if c.participants else '?' for c in convs])
        output({
            "action": "conversations",
            "count": len(convs),
            "threads": [asdict(c) for c in convs],
        })
        return convs

    # ---- open thread + reply ----------------------------------------------

    async def reply_to_thread(self, thread_index: int, body: str) -> MessageResult:
        """Reply to a conversation by its index (0 = most recent)."""
        await self.client.navigate(self.MESSAGES_URL)
        await asyncio.sleep(3)

        js_code = r"""JSON.stringify(
            (() => {
                const items = Array.from(document.querySelectorAll('li.list-item'));
                if (items[IDX]) {
                    const container = items[IDX].querySelector('[class*="container"]');
                    (container || items[IDX]).click();
                    return true;
                }
                return false;
            })()
        )"""
        js_code = js_code.replace("IDX", str(thread_index))

        clicked = await self.client.ev(js_code)

        if not clicked:
            err = f"Thread #{thread_index} not found"
            log_action("reply", thread_index=thread_index, body=body, success=False, error=err)
            output({"action": "reply", "success": False, "error": err})
            return MessageResult(success=False, error=err)

        await asyncio.sleep(3)

        escaped_body = body.replace("\\", "\\\\").replace('"', '\\"')
        typed = await self.client.ev(f"""JSON.stringify(
            (() => {{
                const tas = document.querySelectorAll('textarea');
                for (const ta of tas) {{
                    if (ta.placeholder === "Type a message") {{
                        ta.value = "{escaped_body}";
                        ta.dispatchEvent(new Event('input', {{bubbles: true}}));
                        return {{typed: true, len: ta.value.length}};
                    }}
                }}
                return null;
            }})()
        )""")

        await asyncio.sleep(1)
        sent = await self.client.ev("""JSON.stringify(
            (() => {
                const btns = document.querySelectorAll('button, [role="button"]');
                for (const b of btns) {
                    if (b.getAttribute('aria-label') === 'Send message' || 
                        (b.innerText.trim().toLowerCase() === 'send' && b.className.includes('send-button'))) {
                        b.click();
                        return true;
                    }
                }
                return false;
            })()
        )""")

        await asyncio.sleep(3)

        result = MessageResult(success=True, body=body, timestamp=time.time())
        log_action("reply", thread_index=thread_index, body=body, success=True, typed=typed, sent=sent)
        output({
            "action": "reply",
            "success": True,
            "thread_index": thread_index,
            "body": body,
            "typed": typed,
            "sent": sent,
        })
        return result

    # ---- resolve person name to thread index ------------------------------

    async def find_thread_by_name(self, query: str) -> list[dict]:
        """Find threads matching a person name. Returns [{thread_index, participants, last_message}]."""
        await self.client.navigate(self.MESSAGES_URL)
        await asyncio.sleep(3)

        escaped_query = query.replace("\\", "\\\\").replace('"', '\\"')
        result = await self.client.ev(f"""JSON.stringify(
            Array.from(document.querySelectorAll('li.list-item'))
                .map((el, i) => {{
                    const text = el.innerText.trim();
                    const lines = text.split('\\n').map(l=>l.trim()).filter(Boolean);
                    const content = lines.filter(l => !/^(person|R|J|C|M|A|V|T|B|K|D)$/.test(l));
                    const name = content[0] || '';
                    const msgLines = content.filter(l =>
                        l.length > 1 &&
                        !/^[.,!?;:]+$/.test(l) &&
                        !/\\d{{4}}/.test(l) &&
                        !/[apAP][mM]$/.test(l) &&
                        !/^You:/i.test(l) &&
                        !/^Loved/i.test(l) &&
                        !/^liked/i.test(l)
                    );
                    return {{index: i, participants: name, last_message: msgLines[msgLines.length - 1] || name}};
                }}).filter(t => t.participants.toLowerCase().includes("{escaped_query}".toLowerCase()))
        )""")

        matches = result if isinstance(result, list) else []
        log_action("resolve_thread", query=query, matches=len(matches))
        output({
            "action": "resolve_thread",
            "query": query,
            "matches": len(matches),
            "threads": matches,
        })
        return matches

    # ---- read voicemails --------------------------------------------------

    async def get_voicemails(self, limit: int = 10) -> list[Voicemail]:
        """Get recent voicemails with transcriptions.

        Uses DOM selectors for reliable parsing:
          .participant   → caller name or phone number
          .timestamp     → relative time (e.g. 'Tue 5:29 PM')
          .transcription → AI-transcribed text body
          .duration      → call length (e.g. '00:34')
        """
        await self.client.navigate(self.VOICEMAIL_URL)
        await asyncio.sleep(3)

        js_code = r"""JSON.stringify(
            Array.from(document.querySelectorAll('li.list-item'))
                .map(el => {
                    // Caller name or phone from .participant class inside .title
                    const participantEl = el.querySelector('.title .participant');
                    const name = participantEl ? participantEl.innerText.trim() : '';

                    // Timestamp from .timestamp class inside thread-info-content-call-info
                    const tsEl = el.querySelector('.thread-info-content-call-info .timestamp');
                    const timestamp = tsEl ? tsEl.innerText.trim() : '';

                    // Transcription text from .transcription class inside .subtitle
                    const transEl = el.querySelector('.subtitle .transcription');
                    const transcription = transEl ? transEl.innerText.trim() : '';

                    // Duration if available
                    const durEl = el.querySelector('.duration');
                    const duration = durEl ? durEl.innerText.trim() : '';

                    return {name, timestamp, transcription, duration};
                }).slice(0, LIMIT_PLACEHOLDER)
        )"""
        js_code = js_code.replace("LIMIT_PLACEHOLDER", str(limit))

        result = await self.client.ev(js_code)

        vms = []
        for item in result:
            raw_name = clean(item.get("name", ""))
            # If name is a phone number, use it as phone; otherwise extract digits from transcription
            if re := __import__("re"):
                phone_match = re.search(r'\(?[0-9]{3}\)?[-\s]?[0-9]{3}[-\s]?[0-9]{4}', raw_name)
                phone = phone_match.group(0) if phone_match else raw_name
            else:
                phone = raw_name

            vms.append(Voicemail(
                phone=phone,
                timestamp=item.get("timestamp", ""),
                iso_timestamp=resolve_timestamp(item.get("timestamp", "now")),
                transcription=clean(item.get("transcription", "")),
                raw_text=f"{raw_name} • {item.get('duration', '')}" if not phone_match else f"{phone}",
            ))

        log_action("voicemails_read", count=len(vms))
        output({
            "action": "voicemails",
            "count": len(vms),
            "items": [asdict(vm) for vm in vms],
        })
        return vms


# ---------------------------------------------------------------------------
# Worker mode — write normalized JSON to staging queue (default behavior)
# ---------------------------------------------------------------------------

async def run_worker(gv: GoogleVoiceCDP) -> None:
    """Ingest conversations + voicemails, dedup, write to .staging_queue/inbox_sms.json.

    Each message now includes:
      - thread_type: "direct", "group", or "voicemail" (for AI routing)
      - conversation_context: last N messages with sender/direction for AI context
      - action_hint: suggested action based on thread type and recency
    """
    import hashlib

    now = datetime.now(timezone.utc)
    ledger = load_ledger()
    last_sync = ledger.get("google_voice", "")

    # Fetch data from Google Voice
    convs = await gv.get_conversations(limit=20)
    vms = await gv.get_voicemails(limit=10)

    # Build message list in gmail_worker-compatible format with AI context
    messages = []

    for c in convs:
        sender = ", ".join(c.participants)

        # Use multi-message context if available, otherwise just last_message
        msgs = list(c.messages) if c.messages else [{"from": "Other", "text": clean(c.last_message), "direction": "incoming"}]

        # Filter out noise from all messages
        import re as _re
        clean_msgs = []
        for msg in msgs:
            text = msg["text"] if isinstance(msg, dict) else str(msg)
            text_stripped = text.strip()
            text_lower = text_stripped.lower()
            # Skip social media reactions ("Loved", "liked", "Reacted", "Laughed at", "Disliked")
            if text_lower.startswith(("loved", "liked", "reacted", "laughed", "disliked")):
                continue
            # Skip "to \"...\"" reaction references (Google Voice reaction metadata)
            if text_lower.startswith("to "):
                continue
            # If body is just the sender name, skip it (no actual message content)
            if text.strip() == sender.strip():
                continue
            clean_msgs.append(msg if isinstance(msg, dict) else {"from": "Other", "text": text, "direction": "incoming"})

        if not clean_msgs:
            continue

        # Build conversation context string for AI: shows who said what in order
        context_lines = []
        for msg in clean_msgs:
            direction_label = msg.get("direction", "unknown")
            sender_label = msg.get("from", "Other")
            text = msg["text"]
            if direction_label == "outgoing":
                context_lines.append(f"You: {text}")
            else:
                context_lines.append(f"{sender_label}: {text}")

        body = "\n".join(context_lines)

        # Determine action hint based on thread type and message count
        if c.thread_type == "group":
            action_hint = "review_group_context"  # group threads need full context review
        elif c.message_count > 5:
            action_hint = "review_long_thread"   # long threads may need summary
        else:
            action_hint = "direct_reply_or_ignore"  # simple direct chat

        msg = {
            "message_id": f"gv_{c.thread_type}_{c.thread_id}",
            "date": c.iso_timestamp,
            "sender": sender,
            "subject": f"[{c.thread_type.upper()}] {sender}" if c.thread_type != "direct" else "",
            "body_plain": body,
            "_filtered_weight": 85,
            "_filter_tags": ["sms", c.thread_type],
            "account_id": "google_voice",
            # AI context fields
            "thread_type": c.thread_type,
            "thread_url": c.thread_url,
            "conversation_context": clean_msgs,  # list of {from, text, direction}
            "message_count": c.message_count,
            "action_hint": action_hint,
        }
        messages.append(msg)

    for vm in vms:
        # Use phone + timestamp as unique ID (phone alone causes dedup collisions)
        safe_phone = vm.phone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
        safe_time = vm.iso_timestamp[:16].replace(':', '').replace('-', '')  # e.g. 20260610T2145
        msg_id = f"gv_voicemail_{safe_phone}_{safe_time}"

        # Use caller name from raw_text (strip duration suffix like "• 00:45")
        import re as _re
        sender_raw = clean(vm.raw_text) if vm.raw_text else clean(vm.phone)
        sender_name = _re.sub(r'\s*•\s*[0-9]{2}:[0-9]{2}\s*', '', sender_raw).strip()
        msg = {
            "message_id": msg_id,
            "date": vm.iso_timestamp,
            "sender": sender_name,
            "subject": f"[VOICEMAIL] {sender_name}",
            "body_plain": f"[VOICEMAIL] {clean(vm.transcription)}",
            "_filtered_weight": 95,
            "_filter_tags": ["sms", "voicemail"],
            "account_id": "google_voice",
            # AI context fields
            "thread_type": "voicemail",
            "conversation_context": [{"from": sender_name, "text": clean(vm.transcription), "direction": "incoming"}],
            "action_hint": "review_voicemail",  # voicemails always need review
        }
        messages.append(msg)

    # Dedup: compute hash from stable fields only (exclude iso_timestamp which shifts)
    stable_content = [(m["sender"], m["body_plain"]) for m in messages]
    msg_hash = hashlib.md5(json.dumps(stable_content, sort_keys=True).encode()).hexdigest()
    prev_hash = ledger.get("google_voice_hash", "")

    if msg_hash == prev_hash and last_sync:
        print(f"\nNo new messages since {last_sync}")
        log_action("worker", status="no_new_messages", last_sync=last_sync)
        return

    # Write to staging queue
    batch = {
        "batch": {
            "account": "google_voice",
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "weight": 85,
            "count": len(messages),
        },
        "messages": messages,
    }

    staging_path = os.path.join(STAGING_DIR, "inbox_sms.json")
    os.makedirs(STAGING_DIR, exist_ok=True)
    with open(staging_path, "w", encoding="utf-8") as f:
        json.dump([batch], f, indent=2)

    # Update ledger
    ledger["google_voice"] = now.isoformat()
    ledger["google_voice_hash"] = msg_hash
    save_ledger(ledger)

    print(f"\nWrote {len(messages)} messages to {staging_path}")
    log_action("worker", status="success", count=len(messages), path=staging_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

async def main():
    import argparse

    p = argparse.ArgumentParser(description="Google Voice CDP API")
    p.add_argument("--body", type=str, default="Hello from CDP!", help="Reply message body")
    p.add_argument("--reply-to", type=str, help="Reply to person by name (resolves to thread automatically)")
    p.add_argument("--no-headless", action="store_true", help="Run browser in visible mode and wait 300s for manual login")
    args = p.parse_args()

    async with GoogleVoiceCDP(headless=not args.no_headless) as gv:

        # Visible mode — wait for user to log in
        if args.no_headless:
            print("Chrome launched. You have 300 seconds to log into Google Voice...")
            await asyncio.sleep(300)
            print("Login window closed. Proceeding with scrape.")

        # Reply mode — resolve person then send
        if args.reply_to:
            matches = await gv.find_thread_by_name(args.reply_to)
            if not matches:
                output({"action": "reply", "success": False, "error": f"No thread found for '{args.reply_to}'"})
                return

            # Use first match (or exact match if available)
            target = next((m for m in matches if m["participants"].lower() == args.reply_to.lower()), matches[0])
            await gv.reply_to_thread(target["index"], args.body)

        # Default: worker mode — ingest and write to staging queue
        else:
            await run_worker(gv)


if __name__ == "__main__":
    asyncio.run(main())
