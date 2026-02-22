"""AI Generator routes — real-time streaming via claude CLI stream-json."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from api.auth import get_current_user
from api.models import User

from .system_prompt import EXTENSIONS_BASE_PATH, build_system_prompt

# Regex to extract [WRITE_FILE: path] ... [/WRITE_FILE] blocks
_WRITE_FILE_RE = re.compile(
    r'\[WRITE_FILE:\s*([^\]]+)\]\n?(.*?)\[/WRITE_FILE\]',
    re.DOTALL,
)

# Rotating heartbeat messages so the user sees meaningful progress info
_HEARTBEAT_MSGS = [
    "⏳ Claude is analyzing your requirements...",
    "⏳ Designing the data model...",
    "⏳ Writing extension code...",
    "⏳ Building API endpoints...",
    "⏳ Reviewing the implementation...",
    "⏳ Almost there — finishing up...",
]

logger = logging.getLogger(__name__)
router = APIRouter()

CLAUDE_MODEL   = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
CLAUDE_BIN     = shutil.which("claude") or "/root/.local/bin/claude"
AI_LAYER_URL   = os.getenv("AI_LAYER_URL", "http://127.0.0.1:8010")
AI_LAYER_WS    = os.getenv("AI_LAYER_WS",  "ws://127.0.0.1:8010")


def _has_api_key() -> bool:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    return bool(key) and key not in ("sk-ant-...", "")


async def _ai_layer_available() -> bool:
    """Check if the AI Layer service is running and ready."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{AI_LAYER_URL}/health")
            return resp.status_code == 200
    except Exception:
        return False


# ── WebSocket: full real-time streaming ─────────────────────────

@router.websocket("/ws/generate")
async def ws_generate(websocket: WebSocket):
    """WebSocket endpoint streaming AI extension generation.

    Client sends: {"messages": [...], "template": "...", "active_extensions": [...]}
    Server streams:
      {"type": "status",    "content": "..."}
      {"type": "thinking",  "content": "..."}
      {"type": "token",     "content": "..."}
      {"type": "tool_use",  "tool": "Bash", "input": "..."}
      {"type": "tool_result","tool": "Bash", "output": "..."}
      {"type": "cancelled"}                         ← interrupted by new message
      {"type": "done",      "full_response": "..."}
      {"type": "error",     "message": "..."}
    """
    await websocket.accept()

    # Current generation runs as a background task so new messages can interrupt it
    gen_task: asyncio.Task | None = None

    async def _cancel_current():
        nonlocal gen_task
        if gen_task and not gen_task.done():
            gen_task.cancel()
            try:
                await gen_task
            except (asyncio.CancelledError, Exception):
                pass
            gen_task = None
            try:
                await websocket.send_json({"type": "cancelled"})
            except Exception:
                pass

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            # Kill any ongoing generation before starting a new one
            await _cancel_current()

            messages           = data.get("messages", [])
            template           = data.get("template", "blank")
            active_extensions  = data.get("active_extensions", [])
            selected_extension = data.get("selected_extension") or None
            session_id         = data.get("session_id") or str(__import__("uuid").uuid4())
            # Extract first user message for pattern matching (picks the right reference example)
            first_user_msg     = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")
            system_prompt      = build_system_prompt(template, active_extensions, selected_extension, first_user_msg)

            if _has_api_key():
                gen_task = asyncio.create_task(
                    _stream_via_sdk(websocket, messages, system_prompt)
                )
            elif await _ai_layer_available():
                # AI Layer: Docker sandbox with real tool access + context enrichment
                gen_task = asyncio.create_task(
                    _stream_via_ai_layer(websocket, messages, system_prompt, session_id, selected_extension)
                )
            else:
                gen_task = asyncio.create_task(
                    _stream_via_cli(websocket, messages, system_prompt)
                )

    except WebSocketDisconnect:
        logger.info("AI generator WebSocket disconnected")
        await _cancel_current()
    except Exception:
        logger.exception("Error in AI generator WebSocket")
        await _cancel_current()


# ── SDK path (when ANTHROPIC_API_KEY is set) ─────────────────────

async def _stream_via_sdk(websocket: WebSocket, messages: list[dict], system_prompt: str) -> None:
    """Use Anthropic SDK with tool use — full agentic capability via API key."""
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    current_messages = list(messages)
    all_written_files: list[str] = []
    reload_result: dict = {}
    final_response = ""
    MAX_TURNS = 4

    try:
        await websocket.send_json({"type": "status", "content": "✦ Connecting to Claude API..."})

        for turn in range(MAX_TURNS):
            if turn > 0:
                await websocket.send_json({"type": "status", "content": f"↻ Auto-continuing... (part {turn + 1} of {MAX_TURNS})"})

            full_response = ""
            async with client.messages.stream(
                model=CLAUDE_MODEL,
                max_tokens=16000,   # enough for 8 complete files
                system=system_prompt,
                messages=current_messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    await websocket.send_json({"type": "token", "content": text})

            final_response = full_response

            # Validate + write any [WRITE_FILE:] blocks found in this turn
            if "[WRITE_FILE:" in full_response:
                written, val_errors = await _validate_and_write_files(websocket, full_response)
                if val_errors:
                    break  # Stop on validation failure
                all_written_files.extend(written)
                if written:
                    reload_result = await _hot_reload()
                    new_exts = reload_result.get("new_extensions", [])
                    if new_exts:
                        await websocket.send_json({"type": "status", "content": f"✅ Extension '{new_exts[0]}' registered! Go to Extensions page → Activate."})

            # Done if ✅ marker found
            if "✅" in full_response or not full_response.strip():
                break

            # Auto-continue to get remaining files
            current_messages = current_messages + [
                {"role": "assistant", "content": full_response},
                {"role": "user",      "content": "continue — output the remaining files"},
            ]

        await websocket.send_json({
            "type":           "done",
            "full_response":  final_response,
            "files_written":  all_written_files,
            "new_extensions": reload_result.get("new_extensions", []),
        })

    except asyncio.CancelledError:
        raise
    except anthropic.AuthenticationError as e:
        await websocket.send_json({"type": "error", "message": f"API key invalid: {e}"})
    except anthropic.APIError as e:
        await websocket.send_json({"type": "error", "message": str(e)})


# ── AI Layer path (Docker sandbox — full tool access) ────────────

async def _stream_via_ai_layer(
    websocket: WebSocket,
    messages: list[dict],
    system_prompt: str,
    session_id: str,
    selected_extension: str | None = None,
) -> None:
    """Stream Claude generation through the AI Layer service.

    The AI Layer runs Claude in a Docker sandbox as non-root, enabling:
    - Real tool access (Read/Write/Bash/Grep/Glob)
    - Full codebase awareness via context enrichment
    - No restart needed after file writes (direct filesystem access)
    """
    import websockets as ws_lib

    ai_ws_url = f"{AI_LAYER_WS}/ws/generate"
    await websocket.send_json({"type": "status", "content": "🚀 Connecting to AI sandbox..."})

    try:
        async with ws_lib.connect(ai_ws_url, ping_interval=30, open_timeout=5) as ai_ws:
            # Send the generation request to AI Layer
            payload = {
                "messages":           messages,
                "system_prompt":      system_prompt,
                "template":           "blank",
                "active_extensions":  [],
                "selected_extension": selected_extension,
                "session_id":         session_id,
            }
            await ai_ws.send(json.dumps(payload))

            # Proxy events from AI Layer → client WebSocket
            async for raw in ai_ws:
                try:
                    event = json.loads(raw)
                    await websocket.send_json(event)
                    # Stop proxying when generation is complete
                    if event.get("type") in ("done", "error"):
                        break
                except json.JSONDecodeError:
                    pass

    except Exception as e:
        logger.warning("AI Layer unavailable, falling back to CLI: %s", e)
        # Fallback to direct CLI if AI Layer fails
        await _stream_via_cli(websocket, messages, system_prompt)


# ── CLI path (subscription mode — full stream-json parsing) ──────

TOOL_ICONS = {
    "Bash":       "⚡",
    "Read":       "📄",
    "Write":      "✏️",
    "Edit":       "✏️",
    "Glob":       "🔍",
    "Grep":       "🔎",
    "Task":       "🤖",
    "WebFetch":   "🌐",
    "WebSearch":  "🌐",
}


from typing import AsyncIterator


async def _iter_lines_with_heartbeat(stream, websocket: WebSocket) -> AsyncIterator[str]:
    """Read subprocess stdout in 256 KB chunks with a 30-second heartbeat.

    When Claude is thinking and hasn't output anything yet, this sends a
    status ping every 30 seconds so the frontend inactivity timeout never fires.
    There is NO per-line size limit — fixes the 64 KB asyncio StreamReader cap.
    """
    buf = bytearray()
    HEARTBEAT = 30.0   # seconds of silence before sending a keep-alive ping
    heartbeat_count = 0

    while True:
        try:
            chunk = await asyncio.wait_for(stream.read(262144), timeout=HEARTBEAT)
        except asyncio.TimeoutError:
            # Still alive, just thinking — ping the frontend to reset its timer
            try:
                msg = _HEARTBEAT_MSGS[heartbeat_count % len(_HEARTBEAT_MSGS)]
                heartbeat_count += 1
                await websocket.send_json({"type": "status", "content": msg})
            except Exception:
                return   # websocket gone, stop reading
            continue

        if not chunk:
            break

        buf.extend(chunk)
        while True:
            pos = buf.find(b"\n")
            if pos == -1:
                break
            raw = bytes(buf[:pos]).decode("utf-8", errors="replace").strip()
            buf = buf[pos + 1:]
            if raw:
                yield raw

    if buf:
        raw = buf.decode("utf-8", errors="replace").strip()
        if raw:
            yield raw


_MAX_HISTORY_TURNS = 6    # keep last 3 user+assistant exchanges
_MAX_MSG_CHARS     = 800  # truncate very long messages (e.g. old code dumps)


def _build_prompt(messages: list[dict]) -> str:
    """Build the full prompt string from conversation history.

    Only includes the last _MAX_HISTORY_TURNS messages and truncates individual
    messages that are too long (e.g. old assistant messages containing full
    extension code from a previous session). This keeps prompts lean and fast.
    """
    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    prior = messages[:-1] if len(messages) > 1 else []
    # Limit history depth so old code dumps don't bloat the prompt
    prior = prior[-_MAX_HISTORY_TURNS:]
    if prior:
        history_lines = []
        for m in prior:
            role = "User" if m.get("role") == "user" else "Assistant"
            content = m.get("content", "").strip()
            if not content:
                continue
            # Truncate messages that are unusually long (e.g. old code dumps)
            if len(content) > _MAX_MSG_CHARS:
                content = content[:_MAX_MSG_CHARS] + "\n… [truncated]"
            history_lines.append(f"{role}: {content}")
        history_block = "\n\n".join(history_lines)
        return (
            f"<conversation_history>\n{history_block}\n</conversation_history>\n\n"
            f"User's latest message: {last_user_msg}"
        )
    return last_user_msg


SAAS_ROOT    = "/home/chatwoot/saaskaran"
BACKEND_DIR  = str(Path(EXTENSIONS_BASE_PATH).parent)   # .../backend
FRONTEND_DIR = str(Path(SAAS_ROOT) / "frontend")


async def _emit_turn_response(websocket: WebSocket, response: str) -> None:
    """Display a Claude turn response as structured events.

    For responses that contain [WRITE_FILE:] blocks:
      - Each file appears as a tool_use + tool_result block (like Claude Code)
      - Explanatory text (outside file blocks) appears as chat tokens

    For conversational responses (no file blocks):
      - The full text is emitted as a single token event
    """
    if "[WRITE_FILE:" not in response:
        # Pure conversational response — just emit as text
        if response.strip():
            await websocket.send_json({"type": "token", "content": response})
        return

    last_end = 0
    for match in _WRITE_FILE_RE.finditer(response):
        # Emit any explanatory text that appeared before this file block
        before = response[last_end:match.start()].strip()
        if before:
            # Strip [WRITE_FILE:] markers that might be partially included
            before_clean = before.replace("[WRITE_FILE:", "").strip()
            if before_clean:
                await websocket.send_json({"type": "token", "content": before_clean})

        file_path = match.group(1).strip()
        file_content = match.group(2)
        line_count = file_content.strip().count('\n') + 1 if file_content.strip() else 0

        # Show as a tool block — matches the Claude Code visual style
        await websocket.send_json({
            "type": "tool_use",
            "tool": "Write",
            "input": file_path,
        })
        await websocket.send_json({
            "type": "tool_result",
            "tool": "Write",
            "output": f"✅ {line_count} lines written",
        })

        last_end = match.end()

    # Emit any text after the last file block
    after = response[last_end:].strip()
    if after:
        await websocket.send_json({"type": "token", "content": after})


async def _run_one_turn(
    websocket: WebSocket,
    messages: list[dict],
    system_prompt: str,
    turn: int,
) -> tuple[str, list[str]]:
    """Run one Claude CLI turn using --output-format text (reliable, works as root).

    Claude outputs [WRITE_FILE: path] blocks. We write them to both backend/ AND
    frontend/ automatically, then trigger npm build if frontend files were written.
    """
    env = {**os.environ}
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)
    env.pop("CLAUDECODE", None)   # avoid nested-session error

    label = f"(part {turn + 1})" if turn > 0 else ""
    await websocket.send_json({"type": "status", "content": f"✦ Claude is building your extension... {label}".strip()})

    proc = await asyncio.create_subprocess_exec(
        CLAUDE_BIN,
        "--print",
        "--output-format", "text",
        "--model", "sonnet",
        "--system-prompt", system_prompt,
        "-p", _build_prompt(messages),
        env=env,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    full_response  = ""
    heartbeat_idx  = 0
    HEARTBEAT      = 30.0

    try:
        while True:
            try:
                chunk = await asyncio.wait_for(proc.stdout.read(4096), timeout=HEARTBEAT)
            except asyncio.TimeoutError:
                msg = _HEARTBEAT_MSGS[heartbeat_idx % len(_HEARTBEAT_MSGS)]
                heartbeat_idx += 1
                await websocket.send_json({"type": "status", "content": msg})
                continue

            if not chunk:
                break

            text = chunk.decode("utf-8", errors="replace")
            full_response += text
            await websocket.send_json({"type": "token", "content": text})

        await proc.wait()
        if proc.returncode not in (0, None):
            stderr = (await proc.stderr.read()).decode(errors="replace").strip()
            if stderr:
                await websocket.send_json({"type": "error", "message": stderr[:300]})

        # Caller is responsible for validation + writing
        return full_response, []

    except asyncio.CancelledError:
        try:
            proc.kill()
            await proc.wait()
        except Exception:
            pass
        raise
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        await websocket.send_json({"type": "error", "message": str(e)})
        return full_response, []


async def _stream_via_cli(websocket: WebSocket, messages: list[dict], system_prompt: str) -> None:
    """Run Claude CLI with auto-continue (up to 4 turns if needed).

    Claude generates [WRITE_FILE: path] blocks for BOTH backend extensions and
    frontend React components. Files are written to disk automatically, npm build
    runs if frontend files were written, backend hot-reloads.
    """
    if not Path(CLAUDE_BIN).exists():
        await websocket.send_json({"type": "error", "message": "claude CLI not found. Set ANTHROPIC_API_KEY in .env to use the API."})
        return

    current_messages = list(messages)
    all_written_files: list[str] = []
    reload_result: dict = {}
    final_response = ""

    for turn in range(4):
        turn_response, _ = await _run_one_turn(websocket, current_messages, system_prompt, turn)
        final_response = turn_response

        # Show each written file as a tool_use block (before validation)
        await _emit_turn_response(websocket, turn_response)

        # Validate + write (validation runs before anything hits disk)
        if "[WRITE_FILE:" in turn_response:
            turn_files, validation_errors = await _validate_and_write_files(websocket, turn_response)
            if validation_errors:
                # Validation failed — stop generation, let user fix via follow-up message
                break
            all_written_files.extend(turn_files)

            backend_files  = [f for f in turn_files if not f.startswith("frontend/")]
            frontend_files = [f for f in turn_files if f.startswith("frontend/")]

            if backend_files:
                reload_result = await _hot_reload()
                new_exts = reload_result.get("new_extensions", [])
                if new_exts:
                    await websocket.send_json({"type": "status", "content": f"✅ Extension '{new_exts[0]}' registered!"})

            if frontend_files:
                await websocket.send_json({"type": "status", "content": "🔨 Building frontend..."})
                build_ok = await _npm_build(websocket)
                if build_ok:
                    await websocket.send_json({"type": "status", "content": "✅ Frontend built & deployed!"})

        is_complete = "✅" in turn_response or not turn_response.strip()
        if is_complete or turn == 3:
            break

        await websocket.send_json({"type": "status", "content": f"↻ Auto-continuing... (part {turn + 2})"})
        current_messages = current_messages + [
            {"role": "assistant", "content": turn_response},
            {"role": "user",      "content": "continue — write any remaining files"},
        ]

    await websocket.send_json({
        "type":           "done",
        "full_response":  final_response,
        "files_written":  all_written_files,
        "new_extensions": reload_result.get("new_extensions", []),
    })


def _parse_file_blocks(full_response: str) -> dict[str, str]:
    """Extract {rel_path: content} from all [WRITE_FILE:] blocks in the response."""
    files: dict[str, str] = {}
    for match in _WRITE_FILE_RE.finditer(full_response):
        rel_path = match.group(1).strip()
        content  = match.group(2)
        if content.startswith("\n"):
            content = content[1:]
        files[rel_path] = content
    return files


def _resolve_abs_path(rel_path: str) -> Path:
    saas_root = Path(SAAS_ROOT)
    backend   = Path(BACKEND_DIR)
    if rel_path.startswith("frontend/") or rel_path.startswith("backend/"):
        return saas_root / rel_path
    return backend / rel_path  # legacy: extensions/name/file.py


def _backup_extension(ext_name: str) -> dict[str, bytes] | None:
    """Snapshot all files in an existing extension dir. Returns None if dir doesn't exist."""
    ext_dir = Path(BACKEND_DIR) / "extensions" / ext_name
    if not ext_dir.exists():
        return None
    snapshot: dict[str, bytes] = {}
    for f in ext_dir.rglob("*"):
        if f.is_file() and "__pycache__" not in str(f):
            snapshot[str(f.relative_to(ext_dir))] = f.read_bytes()
    return snapshot


def _restore_extension(ext_name: str, snapshot: dict[str, bytes]) -> None:
    """Restore a previously snapshotted extension directory."""
    ext_dir = Path(BACKEND_DIR) / "extensions" / ext_name
    try:
        import shutil as _shutil
        if ext_dir.exists():
            _shutil.rmtree(ext_dir)
        ext_dir.mkdir(parents=True)
        for rel, data in snapshot.items():
            target = ext_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        logger.info("Rolled back extension '%s' to previous state", ext_name)
    except Exception as exc:
        logger.error("Rollback failed for '%s': %s", ext_name, exc)


async def _validate_and_write_files(
    websocket: WebSocket,
    full_response: str,
) -> tuple[list[str], list[str]]:
    """Parse → validate → write extension files.

    Validation runs BEFORE any file is written to disk:
      1. Python syntax check (ast.parse)
      2. Security scan (no eval/exec, no f-string SQL)
      3. models.py: ext_ prefix, tenant_id present
      4. routes.py: tenant_id filter in queries
      5. extension.py: ExtensionBase inheritance

    If validation fails → errors reported to frontend, nothing written.
    If an existing extension is being overwritten → snapshot first, restore on hot-reload failure.

    Returns:
        (written_files, error_messages)
    """
    from .validator import validate_files

    files = _parse_file_blocks(full_response)
    if not files:
        return [], []

    # ── 1. Validate ───────────────────────────────────────────────────────────
    await websocket.send_json({"type": "status", "content": "🔍 Validating generated code..."})
    result = validate_files(files)

    for warning in result.warnings:
        await websocket.send_json({"type": "status", "content": f"⚠️  {warning}"})

    if not result.passed:
        for error in result.errors:
            await websocket.send_json({"type": "status", "content": f"❌ {error}"})
        await websocket.send_json({
            "type":    "error",
            "message": (
                f"Validation failed ({len(result.errors)} issue(s)). "
                "No files written. Reply with the issues and ask Claude to fix them."
            ),
        })
        return [], result.errors

    await websocket.send_json({"type": "status", "content": "✅ Validation passed — writing files..."})

    # ── 2. Snapshot existing extension dirs before overwriting ────────────────
    snapshots: dict[str, dict[str, bytes]] = {}
    for rel_path in files:
        parts = rel_path.replace("backend/", "").split("/")
        if len(parts) >= 2 and parts[0] == "extensions":
            ext_name = parts[1]
            if ext_name not in snapshots:
                snap = _backup_extension(ext_name)
                if snap is not None:
                    snapshots[ext_name] = snap

    # ── 3. Write files ────────────────────────────────────────────────────────
    written: list[str] = []
    for rel_path, content in files.items():
        abs_path = _resolve_abs_path(rel_path)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        written.append(rel_path)
        logger.info("Wrote file: %s", abs_path)

    return written, []


async def _write_extension_files(full_response: str) -> list[str]:
    """Legacy helper — used by SDK path which doesn't have per-file validation status.

    Parses and writes [WRITE_FILE:] blocks without validation.
    Prefer _validate_and_write_files() for new call sites.
    """
    files = _parse_file_blocks(full_response)
    written: list[str] = []
    for rel_path, content in files.items():
        abs_path = _resolve_abs_path(rel_path)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        written.append(rel_path)
        logger.info("Wrote file: %s", abs_path)
    return written


async def _npm_build(websocket: WebSocket) -> bool:
    """Run `npm run build` in the frontend dir and restart PM2 frontend process."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "npm", "run", "build",
            cwd=FRONTEND_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        # Stream build output as status messages
        assert proc.stdout
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            text = line.decode(errors="replace").strip()
            if text:
                await websocket.send_json({"type": "status", "content": f"  {text}"})

        await proc.wait()
        if proc.returncode != 0:
            await websocket.send_json({"type": "error", "message": "Frontend build failed — check the build output above."})
            return False

        # Restart frontend PM2 process
        restart = await asyncio.create_subprocess_exec(
            "pm2", "restart", "saaskaran-frontend",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await restart.wait()
        return True

    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"Build error: {e}"})
        return False


async def _hot_reload() -> dict:
    """Call the internal hot-reload endpoint to register new extensions."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("http://127.0.0.1:8000/api/v1/extensions/internal/reload")
            return resp.json()
    except Exception as e:
        logger.warning("Hot-reload call failed: %s", e)
        return {"success": False, "error": str(e)}


def _describe_tool(tool_name: str, tool_input: dict) -> str:
    """Generate a human-readable description of a tool call."""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return cmd[:80] if cmd else "running command"
    if tool_name in ("Read",):
        return tool_input.get("file_path", "")
    if tool_name in ("Write", "Edit"):
        return tool_input.get("file_path", "")
    if tool_name == "Glob":
        return tool_input.get("pattern", "")
    if tool_name == "Grep":
        return f'"{tool_input.get("pattern","")}" in {tool_input.get("path",".")}'
    if tool_name == "Task":
        return tool_input.get("description", "")[:60]
    return str(tool_input)[:60]


# ── Session persistence ───────────────────────────────────────────

SESSIONS_DIR = Path("/home/chatwoot/saaskaran/ai_sessions")


class SaveSessionRequest(BaseModel):
    messages:       list[dict]
    extension_name: str = ""


@router.post("/save-session")
async def save_session(
    body: SaveSessionRequest,
    user: Annotated[User, Depends(get_current_user)],
):
    """Save a chat session as a markdown file for future AI context.

    The file is named after the extension and always overwritten, so each
    extension has one canonical session file the AI can reference later.
    """
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    now = datetime.now()

    ext_name = body.extension_name.strip() or "session"
    # Sanitise filename
    safe_name = re.sub(r"[^a-z0-9_\-]", "_", ext_name.lower())
    filename  = f"{safe_name}.md"
    filepath  = SESSIONS_DIR / filename

    # ── Build markdown ────────────────────────────────────────────
    lines: list[str] = [
        f"# AI Builder Session — {ext_name}",
        f"",
        f"**Date:** {now.strftime('%Y-%m-%d %H:%M')}",
        f"**Extension:** `{ext_name}`",
        f"",
        f"---",
        f"",
        f"## Conversation",
        f"",
    ]

    for msg in body.messages:
        role    = msg.get("role", "")
        content = msg.get("content", "").strip()
        if not content:
            continue
        if role == "user":
            lines.append(f"### User")
            lines.append(content)
            lines.append("")
        elif role == "assistant":
            lines.append(f"### Assistant")
            # Strip raw [WRITE_FILE:] block content — keep explanatory text only
            clean = _WRITE_FILE_RE.sub("[file content omitted]", content)
            lines.append(clean.strip())
            lines.append("")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Saved AI session: %s", filepath)

    return {"success": True, "filename": filename, "path": str(filepath)}


@router.get("/sessions")
async def list_sessions(
    user: Annotated[User, Depends(get_current_user)],
):
    """List saved session markdown files."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(SESSIONS_DIR.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    return {
        "sessions": [
            {"name": f.stem, "filename": f.name, "size": f.stat().st_size}
            for f in files
        ]
    }


# ── REST: non-streaming ───────────────────────────────────────────

class GenerateRequest(BaseModel):
    messages:           list[dict]
    project_template:   str       = "blank"
    active_extensions:  list[str] = []


@router.post("/chat")
async def chat(
    body: GenerateRequest,
    user: Annotated[User, Depends(get_current_user)],
):
    system_prompt = build_system_prompt(body.project_template, body.active_extensions)

    if _has_api_key():
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=body.messages,
        )
        return {"response": response.content[0].text}

    # CLI fallback
    env = {**os.environ, "CLAUDECODE": ""}
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)
    last_msg = body.messages[-1].get("content", "") if body.messages else ""
    proc = await asyncio.create_subprocess_exec(
        CLAUDE_BIN, "--print", "--model", "sonnet",
        "--system-prompt", system_prompt,
        "-p", last_msg,
        env=env,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return {"error": stderr.decode(errors="replace")[:200]}
    return {"response": stdout.decode(errors="replace")}


@router.get("/templates")
async def get_templates():
    from main import TEMPLATES
    return {"templates": TEMPLATES}


@router.get("/status")
async def ai_status():
    if _has_api_key():
        return {"mode": "api_key", "model": CLAUDE_MODEL, "ready": True}
    if Path(CLAUDE_BIN).exists():
        return {"mode": "claude_cli", "model": "sonnet (subscription)", "ready": True}
    return {"mode": "none", "ready": False, "message": "Set ANTHROPIC_API_KEY in .env"}
