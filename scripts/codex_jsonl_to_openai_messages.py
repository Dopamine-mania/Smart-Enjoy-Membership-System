#!/usr/bin/env python3
"""
Convert a Codex CLI session JSONL (rollout-*.jsonl) into an "OpenAI messages" JSON
format required by the review manual.

Input:  Codex session JSONL exported by Codex CLI (one JSON object per line).
Output: A single JSON file:
  {
    "messages": [...],
    "meta": {"session_meta": {...}, "turn_contexts": [...], "token_counts": null}
  }
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


_RE_EXIT_CODE = re.compile(r"^Process exited with code (\d+)\s*$", re.M)
_RE_WALL_TIME = re.compile(r"^Wall time:\s*([0-9.]+)\s*s\s*$", re.M)


def _role_map(role: str) -> str:
    # The review manual enumerates role as user/assistant/tool. Codex exports also
    # contain developer/system messages; map them to user for compatibility.
    if role in ("developer", "system"):
        return "user"
    if role in ("user", "assistant", "tool"):
        return role
    return role or "user"


def _to_text_content(items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for it in items or []:
        t = it.get("type")
        if t in ("input_text", "output_text", "text"):
            out.append({"type": "text", "text": it.get("text", "")})
        else:
            # Preserve unknown content as text to keep schema stable.
            out.append({"type": "text", "text": json.dumps(it, ensure_ascii=False)})
    return out


def _parse_tool_output_metadata(output: str) -> Dict[str, Any]:
    md: Dict[str, Any] = {}
    m = _RE_EXIT_CODE.search(output or "")
    if m:
        md["exit_code"] = int(m.group(1))
    m = _RE_WALL_TIME.search(output or "")
    if m:
        try:
            md["duration_seconds"] = float(m.group(1))
        except ValueError:
            pass
    return md


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def convert(path: Path) -> Dict[str, Any]:
    session_meta: Optional[Dict[str, Any]] = None
    turn_contexts: List[Dict[str, Any]] = []
    messages: List[Dict[str, Any]] = []

    for obj in _iter_jsonl(path):
        t = obj.get("type")
        payload = obj.get("payload") or {}

        if t == "session_meta":
            session_meta = payload
            # The manual expects a git object even if empty.
            session_meta.setdefault("git", {})
            continue

        if t == "turn_context":
            turn_contexts.append(payload)
            continue

        if t != "response_item":
            # Ignore event_msg/compacted/etc. The manual requires tool calls and
            # final messages; non-message telemetry is optional.
            continue

        p_type = payload.get("type")

        if p_type == "message":
            role = _role_map(payload.get("role", "user"))
            content = _to_text_content(payload.get("content") or [])
            messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )
            continue

        if p_type == "function_call":
            call_id = payload.get("call_id") or ""
            name = payload.get("name") or ""
            arguments = payload.get("arguments") or ""
            messages.append(
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "tool_call_id": call_id,
                            "name": name,
                            "arguments": arguments,
                        }
                    ],
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {"name": name, "arguments": arguments},
                        }
                    ],
                }
            )
            continue

        if p_type == "function_call_output":
            call_id = payload.get("call_id") or ""
            output = payload.get("output") or ""
            md = _parse_tool_output_metadata(output)
            msg: Dict[str, Any] = {
                "role": "tool",
                "tool_call_id": call_id,
                "content": [{"type": "text", "text": output}],
            }
            if md:
                msg["metadata"] = md
            messages.append(msg)
            continue

        # Unknown response item payload; keep as text so the JSON remains valid.
        messages.append(
            {
                "role": "assistant",
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
            }
        )

    meta = {
        "session_meta": session_meta or {"git": {}},
        "turn_contexts": turn_contexts,
        "token_counts": None,
    }
    return {"messages": messages, "meta": meta}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="Codex rollout JSONL file")
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output JSON path (OpenAI messages format)",
    )
    args = ap.parse_args()

    out = convert(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

