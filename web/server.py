#!/usr/bin/env python3
"""
Om Web — Mobile-friendly web interface for Om agent.
Serves a chat UI and proxies AI requests to Gemini/Groq/Claude.
"""
import os
import sys
import json
import subprocess
import re
import uuid
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# ── Config ────────────────────────────────────────────────────────────────────

ROOT_DIR = Path.home() / ".om-projects"
ROOT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Om", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Provider detection ────────────────────────────────────────────────────────

def detect_provider():
    forced = os.environ.get("CREATOR_PROVIDER", "").lower()

    if forced == "claude" or (not forced and os.environ.get("ANTHROPIC_API_KEY")):
        try:
            import anthropic
            return "claude", os.environ.get("CREATOR_MODEL", "claude-sonnet-4-6"), anthropic.Anthropic()
        except Exception:
            pass

    if forced == "gemini" or (not forced and os.environ.get("GEMINI_API_KEY")):
        try:
            from google import genai
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            return "gemini", os.environ.get("CREATOR_MODEL", "gemini-2.5-flash"), genai.Client(api_key=key)
        except Exception:
            pass

    if forced == "groq" or (not forced and os.environ.get("GROQ_API_KEY")):
        try:
            import groq
            return "groq", os.environ.get("CREATOR_MODEL", "llama-3.3-70b-versatile"), groq.Groq()
        except Exception:
            pass

    return "demo", "demo", None

PROVIDER, MODEL, CLIENT = detect_provider()


# ── Tool implementations ──────────────────────────────────────────────────────

class ProjectState:
    def __init__(self):
        self.active_project = "default"
        self.mode = "architect"

    @property
    def project_path(self) -> Path:
        p = ROOT_DIR / self.active_project
        p.mkdir(parents=True, exist_ok=True)
        return p

state = ProjectState()


def tool_create_file(path: str, content: str) -> str:
    full = state.project_path / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    lines = content.count("\n") + 1
    return f"Created {path} ({lines} lines, {len(content)} chars)"

def tool_read_file(path: str) -> str:
    for candidate in [state.project_path / path, Path(path)]:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")[:50000]
    return f"Error: file not found: {path}"

def tool_edit_file(path: str, find: str, replace: str) -> str:
    full = state.project_path / path
    if not full.is_file():
        return f"Error: file not found: {path}"
    content = full.read_text(encoding="utf-8")
    if find not in content:
        return f"Error: search string not found in {path}"
    full.write_text(content.replace(find, replace, 1), encoding="utf-8")
    return f"Edited {path}"

def tool_run_command(command: str, working_dir: str = "") -> str:
    cwd = state.project_path / working_dir if working_dir else state.project_path
    cwd.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(command, shell=True, cwd=str(cwd),
                                capture_output=True, text=True, timeout=60)
        out = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            out += f"\n[exit code {result.returncode}]"
        return out[:8000] or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: timed out after 60s"
    except Exception as e:
        return f"Error: {e}"

def tool_list_directory(path: str = "") -> str:
    target = state.project_path / path if path else state.project_path
    if not target.exists():
        return f"Not found: {path}"
    skip = {"node_modules", "__pycache__", ".git", "venv", "target", "build"}
    def walk(d, prefix="", depth=0):
        if depth > 3:
            return [f"{prefix}..."]
        lines = []
        for e in sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
            if e.name.startswith(".") or e.name in skip:
                continue
            if e.is_dir():
                lines.append(f"{prefix}📁 {e.name}/")
                lines.extend(walk(e, prefix + "  ", depth + 1))
            else:
                sz = e.stat().st_size
                lines.append(f"{prefix}📄 {e.name} [{sz:,}B]")
        return lines
    return "\n".join(walk(target)) or "(empty)"

def tool_search_files(pattern: str, path: str = "", file_glob: str = "*") -> str:
    target = state.project_path / path if path else state.project_path
    results = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"Invalid regex: {e}"
    skip = {"node_modules", "__pycache__", ".git", "venv"}
    for fpath in target.rglob(file_glob):
        if not fpath.is_file() or any(s in str(fpath) for s in skip):
            continue
        try:
            for i, line in enumerate(fpath.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if regex.search(line):
                    rel = fpath.relative_to(state.project_path)
                    results.append(f"{rel}:{i}: {line.strip()[:120]}")
                    if len(results) >= 30:
                        return "\n".join(results)
        except Exception:
            pass
    return "\n".join(results) if results else "No matches."

def tool_think(thought: str) -> str:
    return "Planning recorded."

def tool_architect(title: str, content: str, diagram: str = "") -> str:
    return f"Architecture plan: {title}"

TOOL_DISPATCH = {
    "create_file": lambda p: tool_create_file(p["path"], p["content"]),
    "read_file": lambda p: tool_read_file(p["path"]),
    "edit_file": lambda p: tool_edit_file(p["path"], p["find"], p["replace"]),
    "run_command": lambda p: tool_run_command(p["command"], p.get("working_dir", "")),
    "list_directory": lambda p: tool_list_directory(p.get("path", "")),
    "search_files": lambda p: tool_search_files(p["pattern"], p.get("path", ""), p.get("file_glob", "*")),
    "think": lambda p: tool_think(p["thought"]),
    "architect": lambda p: tool_architect(p["title"], p["content"], p.get("diagram", "")),
}


# ── Tool schemas ──────────────────────────────────────────────────────────────

OPENAI_TOOLS = [
    {"type": "function", "function": {"name": "create_file", "description": "Create or overwrite a file. Write complete working content.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Find-and-replace edit.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "find": {"type": "string"}, "replace": {"type": "string"}}, "required": ["path", "find", "replace"]}}},
    {"type": "function", "function": {"name": "run_command", "description": "Execute a shell command.", "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "working_dir": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "list_directory", "description": "List files.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "search_files", "description": "Search with regex.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}, "file_glob": {"type": "string"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "think", "description": "Plan before acting.", "parameters": {"type": "object", "properties": {"thought": {"type": "string"}}, "required": ["thought"]}}},
    {"type": "function", "function": {"name": "architect", "description": "Output architecture plan.", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}, "diagram": {"type": "string"}}, "required": ["title", "content"]}}},
]

SYSTEM_PROMPT = """You are Om — a world-class solution architect and builder. You build production-grade software: games, AI agents, full-stack apps, mobile apps, systems, data pipelines, infrastructure.

Rules:
- Write COMPLETE, working code. Never stubs or placeholders.
- After creating code, run it to verify it works.
- Use the think tool to plan complex tasks.
- Use the architect tool to show designs.
- Use modern best practices."""


# ── Gemini provider ───────────────────────────────────────────────────────────

def _build_gemini_tools():
    from google.genai import types
    declarations = []
    for t in OPENAI_TOOLS:
        f = t["function"]
        params = f["parameters"]
        schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                k: types.Schema(type=types.Type.STRING, description=v.get("description", ""))
                for k, v in params.get("properties", {}).items()
            },
            required=params.get("required", []),
        )
        declarations.append(types.FunctionDeclaration(
            name=f["name"], description=f["description"], parameters=schema,
        ))
    return types.Tool(function_declarations=declarations)


def run_gemini(messages: list) -> tuple[str, list]:
    from google.genai import types

    gemini_tool = _build_gemini_tools()
    gemini_contents = []

    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            if isinstance(content, str):
                gemini_contents.append(types.Content(role="user", parts=[types.Part.from_text(text=content)]))
            elif isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        parts.append(types.Part.from_function_response(
                            name=item.get("_tool_name", "unknown"),
                            response={"result": item.get("content", "")},
                        ))
                if parts:
                    gemini_contents.append(types.Content(role="user", parts=parts))
        elif role == "assistant":
            if isinstance(content, str):
                gemini_contents.append(types.Content(role="model", parts=[types.Part.from_text(text=content)]))
            elif isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            parts.append(types.Part.from_text(text=item["text"]))
                        elif item.get("type") == "tool_call":
                            parts.append(types.Part.from_function_call(name=item["name"], args=item.get("args", {})))
                if parts:
                    gemini_contents.append(types.Content(role="model", parts=parts))

    tool_events = []
    full_text = ""

    for iteration in range(15):
        response = CLIENT.models.generate_content(
            model=MODEL, contents=gemini_contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT, tools=[gemini_tool], temperature=0.7,
            ),
        )

        assistant_parts = []
        tool_calls = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.text:
                    full_text += part.text
                    assistant_parts.append({"type": "text", "text": part.text})
                elif part.function_call:
                    fc = part.function_call
                    args = dict(fc.args) if fc.args else {}
                    tool_calls.append({"name": fc.name, "args": args})
                    assistant_parts.append({"type": "tool_call", "name": fc.name, "args": args})

        messages.append({"role": "assistant", "content": assistant_parts if assistant_parts else full_text})
        gemini_contents.append(types.Content(role="model", parts=response.candidates[0].content.parts))

        if not tool_calls:
            break

        result_parts_gemini = []
        result_parts_ours = []
        for tc in tool_calls:
            try:
                result = TOOL_DISPATCH[tc["name"]](tc["args"])
            except Exception as e:
                result = f"Error: {e}"
            tool_events.append({"tool": tc["name"], "args": tc["args"], "result": result})
            result_parts_gemini.append(types.Part.from_function_response(name=tc["name"], response={"result": result}))
            result_parts_ours.append({"type": "tool_result", "_tool_name": tc["name"], "content": result})

        gemini_contents.append(types.Content(role="user", parts=result_parts_gemini))
        messages.append({"role": "user", "content": result_parts_ours})

    return full_text, tool_events, messages


# ── Groq provider ────────────────────────────────────────────────────────────

def run_groq(messages: list) -> tuple[str, list]:
    oai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            if isinstance(content, str):
                oai_messages.append({"role": "user", "content": content})
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        oai_messages.append({"role": "tool", "tool_call_id": item.get("tool_call_id", ""), "content": item.get("content", "")})
        elif role == "assistant":
            if isinstance(content, str):
                oai_messages.append({"role": "assistant", "content": content})
            elif isinstance(content, list):
                text_parts = []
                tc_list = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item["text"])
                        elif item.get("type") == "tool_call":
                            tc_list.append({"id": item.get("id", ""), "type": "function", "function": {"name": item["name"], "arguments": json.dumps(item.get("args", {}))}})
                msg_d = {"role": "assistant", "content": "".join(text_parts) or None}
                if tc_list:
                    msg_d["tool_calls"] = tc_list
                oai_messages.append(msg_d)

    tool_events = []
    full_text = ""

    for iteration in range(10):
        response = CLIENT.chat.completions.create(
            model=MODEL, messages=oai_messages, tools=OPENAI_TOOLS,
            tool_choice="auto", max_tokens=8192, temperature=0.7,
        )
        choice = response.choices[0]
        msg = choice.message

        if msg.content:
            full_text += msg.content

        assistant_parts = []
        if msg.content:
            assistant_parts.append({"type": "text", "text": msg.content})

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                tool_calls.append({"id": tc.id, "name": tc.function.name, "args": args})
                assistant_parts.append({"type": "tool_call", "id": tc.id, "name": tc.function.name, "args": args})

        messages.append({"role": "assistant", "content": assistant_parts if assistant_parts else (msg.content or "")})
        oai_msg = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            oai_msg["tool_calls"] = [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in msg.tool_calls]
        oai_messages.append(oai_msg)

        if not tool_calls:
            break

        result_parts = []
        for tc in tool_calls:
            try:
                result = TOOL_DISPATCH[tc["name"]](tc["args"])
            except Exception as e:
                result = f"Error: {e}"
            tool_events.append({"tool": tc["name"], "args": tc["args"], "result": result})
            oai_messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
            result_parts.append({"type": "tool_result", "tool_call_id": tc["id"], "_tool_name": tc["name"], "content": result})
        messages.append({"role": "user", "content": result_parts})

    return full_text, tool_events, messages


# ── Claude provider ───────────────────────────────────────────────────────────

CLAUDE_TOOLS = [
    {"name": t["function"]["name"], "description": t["function"]["description"],
     "input_schema": t["function"]["parameters"]}
    for t in OPENAI_TOOLS
]

def run_claude(messages: list) -> tuple[str, list]:
    tool_events = []
    full_text = ""

    for iteration in range(15):
        response = CLIENT.messages.create(
            model=MODEL, max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=CLAUDE_TOOLS, messages=messages,
        )
        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
        full_text += "".join(text_parts)
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                try:
                    result = TOOL_DISPATCH[block.name](block.input)
                except Exception as e:
                    result = f"Error: {e}"
                tool_events.append({"tool": block.name, "args": block.input, "result": result})
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        messages.append({"role": "user", "content": tool_results})

    return full_text, tool_events, messages


# ── Session storage ───────────────────────────────────────────────────────────

sessions = {}  # session_id -> {"messages": [], "project": str, "mode": str}


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text()

@app.get("/api/status")
async def api_status():
    return {"provider": PROVIDER, "model": MODEL, "project": state.active_project, "mode": state.mode}

@app.post("/api/chat")
async def api_chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id", str(uuid.uuid4()))
    mode = data.get("mode", state.mode)
    project = data.get("project", state.active_project)

    if not user_message:
        return JSONResponse({"error": "Empty message"}, status_code=400)

    state.mode = mode
    state.active_project = project
    state.project_path  # ensure dir exists

    # Get or create session
    if session_id not in sessions:
        sessions[session_id] = {"messages": [], "project": project, "mode": mode}
    session = sessions[session_id]
    session["messages"].append({"role": "user", "content": user_message})

    if PROVIDER == "demo":
        reply = f"I'm running in demo mode. To use my full power, set up a free API key:\n\n**Gemini (free):** Get a key at aistudio.google.com, then set `GEMINI_API_KEY`\n**Groq (free):** Get a key at console.groq.com, then set `GROQ_API_KEY`\n\nYou asked: {user_message}"
        session["messages"].append({"role": "assistant", "content": reply})
        return {"reply": reply, "tool_events": [], "session_id": session_id}

    try:
        if PROVIDER == "gemini":
            reply, tool_events, session["messages"] = run_gemini(session["messages"])
        elif PROVIDER == "groq":
            reply, tool_events, session["messages"] = run_groq(session["messages"])
        elif PROVIDER == "claude":
            reply, tool_events, session["messages"] = run_claude(session["messages"])
        else:
            reply, tool_events = "Provider not configured.", []
    except Exception as e:
        reply = f"Error: {e}"
        tool_events = []

    return {"reply": reply, "tool_events": tool_events, "session_id": session_id}

@app.post("/api/project")
async def set_project(request: Request):
    data = await request.json()
    name = re.sub(r"[^\w\-.]", "_", data.get("name", "default"))
    state.active_project = name
    state.project_path
    return {"project": name, "path": str(state.project_path)}

@app.get("/api/files")
async def get_files():
    return {"tree": tool_list_directory(), "project": state.active_project}

@app.get("/api/file/{path:path}")
async def get_file(path: str):
    content = tool_read_file(path)
    return {"path": path, "content": content}


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"\n  ॐ Om Web — running on http://0.0.0.0:{port}")
    print(f"  Provider: {PROVIDER} ({MODEL})")
    print(f"  Projects: {ROOT_DIR}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
