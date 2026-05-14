#!/usr/bin/env python3
"""
Om — God-tier solution architect & builder.
Multi-provider: Gemini (free), Groq (free), Claude (paid), or demo mode.
"""
import os
import sys
import json
import subprocess
import re
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table

# ── Config ────────────────────────────────────────────────────────────────────

ROOT_DIR = Path.home() / ".workspace" / "projects"
ROOT_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR = Path.home() / ".workspace" / ".sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

DEMO_MODE = os.environ.get("CREATOR_DEMO", "").lower() in ("1", "true", "yes") or "--demo" in sys.argv

console = Console()


# ── Provider detection ────────────────────────────────────────────────────────

def detect_provider() -> tuple[str, str, object]:
    """Detect which AI provider to use based on available API keys.
    Returns (provider_name, model_id, client_object).
    Priority: explicit CREATOR_PROVIDER env > Anthropic > Gemini > Groq > demo.
    """
    forced = os.environ.get("CREATOR_PROVIDER", "").lower()

    # Anthropic / Claude
    if forced == "claude" or (not forced and os.environ.get("ANTHROPIC_API_KEY")):
        try:
            import anthropic
            return "claude", os.environ.get("CREATOR_MODEL", "claude-sonnet-4-6"), anthropic.Anthropic()
        except Exception:
            pass

    # Google Gemini (free tier: 15 RPM, 1M TPM)
    if forced == "gemini" or (not forced and os.environ.get("GEMINI_API_KEY")):
        try:
            from google import genai
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            client = genai.Client(api_key=api_key)
            return "gemini", os.environ.get("CREATOR_MODEL", "gemini-2.5-flash"), client
        except Exception:
            pass

    # Groq (free tier: 30 RPM, 6000 TPM on llama)
    if forced == "groq" or (not forced and os.environ.get("GROQ_API_KEY")):
        try:
            import groq
            return "groq", os.environ.get("CREATOR_MODEL", "llama-3.3-70b-versatile"), groq.Groq()
        except Exception:
            pass

    return "demo", "demo", None


PROVIDER, MODEL, CLIENT = detect_provider()
if PROVIDER == "demo":
    DEMO_MODE = True


# ── Domain modes ──────────────────────────────────────────────────────────────

MODES = {
    "architect": {
        "label": "Solution Architect", "icon": "🏗️",
        "focus": """You are in Solution Architect mode. Focus on:
- System design, trade-off analysis, scalability patterns
- Technology selection with clear justification
- Architecture Decision Records (ADRs)
- Diagramming (ASCII/Mermaid), API contracts, data models
- Cost estimation and operational concerns"""
    },
    "game": {
        "label": "Game Development", "icon": "🎮",
        "focus": """You are in Game Development mode. Focus on:
- Entity-Component-System (ECS) architecture, game loops, fixed vs variable timestep
- Rendering pipelines (forward/deferred), shader programming, PBR materials
- Physics engines (collision detection, rigid body, spatial partitioning)
- Multiplayer networking (client prediction, server reconciliation, lag compensation)
- Engine patterns: Unreal (Blueprints + C++), Unity (MonoBehaviour/DOTS), Godot (GDScript/C#)
- Asset pipelines, LOD systems, streaming, memory budgets
- Audio systems, animation state machines, procedural generation
- Build complete, playable prototypes — not stubs"""
    },
    "ai": {
        "label": "AI / ML / Agents", "icon": "🧠",
        "focus": """You are in AI/ML/Agents mode. Focus on:
- Transformer architectures, attention mechanisms, tokenization
- RAG pipelines (chunking, embedding, vector stores, reranking)
- Agentic systems (tool use, planning, memory, multi-agent orchestration)
- Fine-tuning (LoRA, QLoRA, RLHF, DPO), evaluation frameworks
- MLOps (experiment tracking, model registry, serving, monitoring)
- LLM application patterns (prompt engineering, chain-of-thought, structured output)
- Computer vision, NLP, speech, multimodal systems
- Deployment (ONNX, TensorRT, quantization, batching)"""
    },
    "web": {
        "label": "Full-Stack Web", "icon": "🌐",
        "focus": """You are in Full-Stack Web mode. Focus on:
- Frontend: React/Next.js, Vue/Nuxt, Svelte, TypeScript, state management, SSR/SSG
- Backend: FastAPI, Express, Django, GraphQL, REST API design
- Databases: PostgreSQL, MongoDB, Redis, query optimization, migrations
- Auth: OAuth2, JWT, session management, RBAC/ABAC
- Real-time: WebSockets, SSE, pub/sub
- Deployment: Docker, CI/CD, CDN, edge computing
- Performance: caching strategies, lazy loading, bundle optimization"""
    },
    "mobile": {
        "label": "Mobile Development", "icon": "📱",
        "focus": """You are in Mobile Development mode. Focus on:
- Cross-platform: React Native, Flutter, Kotlin Multiplatform
- Native iOS (Swift/SwiftUI) and Android (Kotlin/Jetpack Compose)
- State management, navigation patterns, offline-first architecture
- Push notifications, deep linking, in-app purchases
- Performance profiling, memory management, battery optimization
- App store deployment, code signing, CI/CD for mobile"""
    },
    "systems": {
        "label": "Systems Programming", "icon": "⚙️",
        "focus": """You are in Systems Programming mode. Focus on:
- Rust: ownership, lifetimes, async, unsafe, FFI, no_std
- C/C++: modern C++ (17/20/23), RAII, smart pointers, move semantics
- Concurrency: lock-free data structures, channels, async runtimes
- Memory: allocators, cache optimization, SIMD, zero-copy
- OS concepts: syscalls, file systems, networking, IPC
- Embedded: bare metal, RTOS, HAL, DMA, interrupt handling
- Performance: profiling, benchmarking, optimization techniques"""
    },
    "data": {
        "label": "Data Engineering", "icon": "📊",
        "focus": """You are in Data Engineering mode. Focus on:
- Pipelines: Apache Spark, Flink, Beam, Airflow, Dagster
- Storage: data lakes, warehouses (Snowflake, BigQuery, Redshift)
- Streaming: Kafka, Kinesis, Pulsar, event sourcing, CQRS
- Modeling: star schema, data vault, slowly changing dimensions
- Quality: Great Expectations, dbt tests, data contracts
- Analytics: OLAP, materialized views, approximate algorithms
- Visualization: dashboards, reporting, real-time analytics"""
    },
    "devops": {
        "label": "DevOps / Infrastructure", "icon": "🔧",
        "focus": """You are in DevOps/Infrastructure mode. Focus on:
- Containers: Docker, Kubernetes, Helm, service mesh (Istio)
- IaC: Terraform, Pulumi, CloudFormation, CDK
- CI/CD: GitHub Actions, Jenkins, ArgoCD, GitOps
- Observability: Prometheus, Grafana, OpenTelemetry, distributed tracing
- Cloud: AWS/GCP/Azure architecture, serverless, managed services
- Security: secrets management, network policies, compliance scanning
- SRE: SLOs/SLIs, incident response, chaos engineering, capacity planning"""
    },
}

# ── System prompt ─────────────────────────────────────────────────────────────

def build_system_prompt(mode: str, project_path: Path) -> str:
    mode_info = MODES.get(mode, MODES["architect"])
    return f"""You are Om — a world-class solution architect and builder. You design and build production-grade software across every domain: AAA games, agentic AI systems, full-stack platforms, embedded systems, data pipelines, mobile apps, infrastructure, and beyond.

## Current Context
- Mode: {mode_info['icon']} {mode_info['label']}
- Project workspace: {project_path}

{mode_info['focus']}

## Core Principles

### Architecture
- Start with the problem, not the technology. Understand constraints before proposing solutions.
- Design for the "-ilities": scalability, reliability, maintainability, observability, security.
- Prefer simple, boring technology that works over cutting-edge complexity.
- Make architectural decisions explicit — document WHY, not just WHAT.

### Building
- Write COMPLETE, PRODUCTION-QUALITY code. Never stubs, never placeholders, never "TODO".
- Every file must be syntactically valid and functionally complete.
- After creating code, ALWAYS run it to verify it works. Fix any issues.
- Include error handling, input validation, and edge cases.
- Use modern idioms and best practices for whatever language/framework.

### Problem Solving
1. THINK first — use the think tool to plan complex tasks before writing code.
2. Break large problems into phases. Build incrementally, verify each phase.
3. When something fails, READ the error, diagnose the root cause, then fix.

## Tools Available
- **create_file**: Write complete files to the project workspace
- **read_file**: Read existing files to understand code before modifying
- **edit_file**: Make surgical find-and-replace edits without rewriting entire files
- **run_command**: Execute shell commands — run code, install packages, test, build
- **list_directory**: Browse the project file tree
- **search_files**: Search across project files with regex patterns
- **think**: Plan your approach for complex multi-step tasks
- **architect**: Output structured architecture plans, diagrams, and design documents

## How to Work
For simple requests: act directly.
For complex requests:
1. think -> plan your approach, identify components, choose technologies
2. architect -> output the high-level design if the user needs visibility
3. create files -> build incrementally, core abstractions first
4. run and test -> verify everything works
5. iterate -> fix issues, add polish, ensure quality
"""


# ── Tool implementations ──────────────────────────────────────────────────────

class ProjectState:
    def __init__(self):
        self.active_project: str = "default"
        self.mode: str = "architect"
        self.messages: list = []

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
    console.print(f"  [green]✓[/] [cyan]{path}[/] [dim]({lines} lines, {len(content)} chars)[/]")
    return f"Created {path} ({lines} lines)"

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
    console.print(f"  [green]✓[/] Edited [cyan]{path}[/]")
    return f"Edited {path}"

def tool_run_command(command: str, working_dir: str = "") -> str:
    cwd = state.project_path / working_dir if working_dir else state.project_path
    cwd.mkdir(parents=True, exist_ok=True)
    console.print(f"  [yellow]$[/] [dim]{command}[/]")
    try:
        result = subprocess.run(command, shell=True, cwd=str(cwd),
                                capture_output=True, text=True, timeout=120)
        out = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            out += f"\n[exit code {result.returncode}]"
        preview = out.strip()[:500]
        if preview:
            style = "red" if result.returncode != 0 else "dim"
            console.print(f"  [{style}]{preview}[/{style}]")
        return out[:10000] or "(no output)"
    except subprocess.TimeoutExpired:
        console.print("  [red]Timed out (120s)[/]")
        return "Error: timed out after 120s"
    except Exception as e:
        return f"Error: {e}"

def tool_list_directory(path: str = "") -> str:
    target = state.project_path / path if path else state.project_path
    if not target.exists():
        return f"Directory not found: {path}"
    def walk(d: Path, prefix: str = "", depth: int = 0) -> list[str]:
        if depth > 4:
            return [f"{prefix}..."]
        entries = sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        lines = []
        skip = {"node_modules", "__pycache__", ".git", "venv", "target", "build"}
        for entry in entries:
            if entry.name.startswith(".") or entry.name in skip:
                continue
            if entry.is_dir():
                lines.append(f"{prefix}📁 {entry.name}/")
                lines.extend(walk(entry, prefix + "  ", depth + 1))
            else:
                size = entry.stat().st_size
                label = f"{size:,}B" if size < 10000 else f"{size // 1024}KB"
                lines.append(f"{prefix}📄 {entry.name} [{label}]")
        return lines
    lines = walk(target)
    return "\n".join(lines) if lines else "(empty)"

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
                    if len(results) >= 50:
                        return "\n".join(results)
        except Exception:
            pass
    return "\n".join(results) if results else "No matches found."

def tool_think(thought: str) -> str:
    console.print(Panel(Text(thought, style="italic dim"),
                        title="[dim]💭 Planning[/]", border_style="dim blue", padding=(0, 1)))
    return "Planning recorded. Proceed with implementation."

def tool_architect(title: str, content: str, diagram: str = "") -> str:
    parts = []
    if diagram:
        parts.append(Text(diagram, style="cyan"))
        parts.append(Text(""))
    parts.append(Text(content))
    combined = Text("\n").join(parts) if len(parts) > 1 else parts[0]
    console.print(Panel(combined, title=f"[bold cyan]📐 {title}[/]",
                        border_style="cyan", padding=(1, 2)))
    return "Architecture plan displayed."


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

# ── Tool schemas (OpenAI-compatible for Groq, also used by Gemini/Claude) ────

OPENAI_TOOLS = [
    {"type": "function", "function": {"name": "create_file", "description": "Create or overwrite a file in the project. Write complete working content.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Project-relative file path"}, "content": {"type": "string", "description": "Complete file content"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a file's contents.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Surgical find-and-replace edit on a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path"}, "find": {"type": "string", "description": "Exact string to find"}, "replace": {"type": "string", "description": "Replacement string"}}, "required": ["path", "find", "replace"]}}},
    {"type": "function", "function": {"name": "run_command", "description": "Execute a shell command. Use for running code, installing packages, testing.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Shell command"}, "working_dir": {"type": "string", "description": "Subdirectory (optional)"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "list_directory", "description": "List files in the project workspace.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Subdirectory (optional)"}}, "required": []}}},
    {"type": "function", "function": {"name": "search_files", "description": "Search project files with regex.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string", "description": "Regex pattern"}, "path": {"type": "string", "description": "Subdirectory (optional)"}, "file_glob": {"type": "string", "description": "File glob like *.py (optional)"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "think", "description": "Plan and reason about a complex task before acting.", "parameters": {"type": "object", "properties": {"thought": {"type": "string", "description": "Planning and reasoning"}}, "required": ["thought"]}}},
    {"type": "function", "function": {"name": "architect", "description": "Output an architecture plan or diagram.", "parameters": {"type": "object", "properties": {"title": {"type": "string", "description": "Plan title"}, "content": {"type": "string", "description": "Architecture description"}, "diagram": {"type": "string", "description": "ASCII diagram (optional)"}}, "required": ["title", "content"]}}},
]

CLAUDE_TOOLS = [
    {"name": t["function"]["name"], "description": t["function"]["description"],
     "input_schema": t["function"]["parameters"]}
    for t in OPENAI_TOOLS
]


# ══════════════════════════════════════════════════════════════════════════════
# ── PROVIDER: CLAUDE ──────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def run_turn_claude(messages: list) -> list:
    for _ in range(25):
        sys_prompt = build_system_prompt(state.mode, state.project_path)
        with CLIENT.messages.stream(
            model=MODEL, max_tokens=64000,
            thinking={"type": "adaptive"},
            system=[{"type": "text", "text": sys_prompt, "cache_control": {"type": "ephemeral"}}],
            tools=CLAUDE_TOOLS, messages=messages,
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    print(event.delta.text, end="", flush=True)
            final = stream.get_final_message()

        messages.append({"role": "assistant", "content": final.content})
        if final.stop_reason != "tool_use":
            print()
            break

        print()
        tool_results = []
        for block in final.content:
            if block.type == "tool_use":
                console.print(f"\n  [bold blue]🔧 {block.name}[/]")
                try:
                    result = TOOL_DISPATCH[block.name](block.input)
                except Exception as e:
                    result = f"Tool error: {e}"
                    console.print(f"  [red]{result}[/]")
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        messages.append({"role": "user", "content": tool_results})
    return messages


# ══════════════════════════════════════════════════════════════════════════════
# ── PROVIDER: GEMINI (free) ───────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

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


def run_turn_gemini(messages: list) -> list:
    from google.genai import types

    gemini_tool = _build_gemini_tools()
    sys_prompt = build_system_prompt(state.mode, state.project_path)

    # Convert our message format to Gemini format
    gemini_contents = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            if isinstance(content, str):
                gemini_contents.append(types.Content(role="user", parts=[types.Part.from_text(text=content)]))
            elif isinstance(content, list):
                # tool results
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
                            parts.append(types.Part.from_function_call(
                                name=item["name"], args=item.get("args", {}),
                            ))
                if parts:
                    gemini_contents.append(types.Content(role="model", parts=parts))

    for iteration in range(25):
        response = CLIENT.models.generate_content(
            model=MODEL,
            contents=gemini_contents,
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                tools=[gemini_tool],
                temperature=0.7,
            ),
        )

        # Process response parts
        assistant_parts = []
        tool_calls = []
        full_text = ""

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.text:
                    full_text += part.text
                    print(part.text, end="", flush=True)
                    assistant_parts.append({"type": "text", "text": part.text})
                elif part.function_call:
                    fc = part.function_call
                    args = dict(fc.args) if fc.args else {}
                    tool_calls.append({"name": fc.name, "args": args})
                    assistant_parts.append({"type": "tool_call", "name": fc.name, "args": args})

        # Save assistant message
        messages.append({"role": "assistant", "content": assistant_parts if assistant_parts else full_text})
        gemini_contents.append(types.Content(role="model", parts=response.candidates[0].content.parts))

        if not tool_calls:
            print()
            break

        # Execute tools and send results
        print()
        result_parts_gemini = []
        result_parts_ours = []
        for tc in tool_calls:
            console.print(f"\n  [bold blue]🔧 {tc['name']}[/]")
            try:
                result = TOOL_DISPATCH[tc["name"]](tc["args"])
            except Exception as e:
                result = f"Tool error: {e}"
                console.print(f"  [red]{result}[/]")

            result_parts_gemini.append(types.Part.from_function_response(
                name=tc["name"], response={"result": result},
            ))
            result_parts_ours.append({
                "type": "tool_result", "_tool_name": tc["name"], "content": result,
            })

        gemini_contents.append(types.Content(role="user", parts=result_parts_gemini))
        messages.append({"role": "user", "content": result_parts_ours})

    return messages


# ══════════════════════════════════════════════════════════════════════════════
# ── PROVIDER: GROQ (free) ────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def run_turn_groq(messages: list) -> list:
    sys_prompt = build_system_prompt(state.mode, state.project_path)

    # Convert to OpenAI-compatible message format
    oai_messages = [{"role": "system", "content": sys_prompt}]
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            if isinstance(content, str):
                oai_messages.append({"role": "user", "content": content})
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        oai_messages.append({
                            "role": "tool",
                            "tool_call_id": item.get("tool_call_id", ""),
                            "content": item.get("content", ""),
                        })
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
                            tc_list.append({
                                "id": item.get("id", ""),
                                "type": "function",
                                "function": {"name": item["name"], "arguments": json.dumps(item.get("args", {}))},
                            })
                msg_dict = {"role": "assistant", "content": "".join(text_parts) or None}
                if tc_list:
                    msg_dict["tool_calls"] = tc_list
                oai_messages.append(msg_dict)

    for iteration in range(15):
        response = CLIENT.chat.completions.create(
            model=MODEL,
            messages=oai_messages,
            tools=OPENAI_TOOLS,
            tool_choice="auto",
            max_tokens=8192,
            temperature=0.7,
        )

        choice = response.choices[0]
        msg = choice.message

        # Print text
        if msg.content:
            print(msg.content, end="", flush=True)

        # Save to our format
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

        # Add to OAI messages
        oai_msg = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            oai_msg["tool_calls"] = [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        oai_messages.append(oai_msg)

        if not tool_calls:
            print()
            break

        # Execute tools
        print()
        result_parts = []
        for tc in tool_calls:
            console.print(f"\n  [bold blue]🔧 {tc['name']}[/]")
            try:
                result = TOOL_DISPATCH[tc["name"]](tc["args"])
            except Exception as e:
                result = f"Tool error: {e}"
                console.print(f"  [red]{result}[/]")

            oai_messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
            result_parts.append({"type": "tool_result", "tool_call_id": tc["id"], "_tool_name": tc["name"], "content": result})

        messages.append({"role": "user", "content": result_parts})

    return messages


# ── Unified turn dispatcher ──────────────────────────────────────────────────

def run_turn(messages: list) -> list:
    if PROVIDER == "claude":
        return run_turn_claude(messages)
    elif PROVIDER == "gemini":
        return run_turn_gemini(messages)
    elif PROVIDER == "groq":
        return run_turn_groq(messages)
    else:
        console.print("[red]No provider configured.[/]")
        return messages


# ══════════════════════════════════════════════════════════════════════════════
# ── DEMO MODE ─────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def type_text(text: str, speed: float = 0.012):
    for char in text:
        print(char, end="", flush=True)
        if char in (".", "!", "?", "\n"):
            time.sleep(speed * 3)
        elif char in (",", ";", ":"):
            time.sleep(speed * 2)
        else:
            time.sleep(speed)
    print()

DEMO_SCENARIOS = {
    "snake": {
        "steps": [
            ("think", {"thought": "Let me plan a terminal Snake game in Python using curses.\n\nComponents:\n1. Game board with borders\n2. Snake entity (deque of positions, direction, growth)\n3. Food spawner (random, avoid snake body)\n4. Input handler (arrow keys, non-blocking)\n5. Game loop at ~10 FPS with collision detection\n6. Score tracking, progressive speed, game-over screen"}),
            ("architect", {"title": "Snake Game Architecture", "content": "Single-file Python game using curses.\n- GameState: board, snake deque, food position, score, direction\n- Input: non-blocking getch(), arrow key mapping\n- Update: move head, check wall/self collision, check food, grow/trim\n- Render: Unicode border, green snake, red food, yellow HUD\n- Loop: Input -> Update -> Render -> Sleep (100ms initial, speeds up)", "diagram": "┌────────────────────────────┐\n│  ████████████████████████  │\n│  █                      █  │\n│  █   ●●●●▸              █  │\n│  █            ◆         █  │\n│  █                      █  │\n│  ████████████████████████  │\n│  Score: 4   [q] quit       │\n└────────────────────────────┘\n\n  Input ──▸ Update ──▸ Render ──▸ ⏳\n    ▲                             │\n    └─────────────────────────────┘"}),
            ("create_file", {"path": "snake.py", "content": '#!/usr/bin/env python3\n"""Terminal Snake Game — built by Om."""\nimport curses\nimport random\nfrom collections import deque\n\ndef main(stdscr):\n    curses.curs_set(0)\n    stdscr.nodelay(True)\n    stdscr.timeout(100)\n    curses.start_color()\n    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)\n    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)\n    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)\n    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)\n\n    sh, sw = stdscr.getmaxyx()\n    bh, bw = min(sh - 4, 20), min(sw - 4, 50)\n    oy, ox = (sh - bh) // 2, (sw - bw) // 2\n\n    snake = deque()\n    sy, sx = bh // 2, bw // 4\n    for i in range(4):\n        snake.appendleft((sy, sx - i))\n    direction = (0, 1)\n    score = 0\n    speed = 100\n\n    def place_food():\n        while True:\n            fy, fx = random.randint(1, bh-2), random.randint(1, bw-2)\n            if (fy, fx) not in snake:\n                return (fy, fx)\n    food = place_food()\n\n    while True:\n        stdscr.erase()\n        for x in range(bw):\n            stdscr.addch(oy, ox+x, curses.ACS_BLOCK, curses.color_pair(4))\n            stdscr.addch(oy+bh-1, ox+x, curses.ACS_BLOCK, curses.color_pair(4))\n        for y in range(bh):\n            stdscr.addch(oy+y, ox, curses.ACS_BLOCK, curses.color_pair(4))\n            stdscr.addch(oy+y, ox+bw-1, curses.ACS_BLOCK, curses.color_pair(4))\n\n        stdscr.addstr(oy+food[0], ox+food[1], "◆", curses.color_pair(2))\n        for i, (sy, sx) in enumerate(snake):\n            stdscr.addstr(oy+sy, ox+sx, "▸" if i==0 else "●", curses.color_pair(1))\n\n        hud = f" Score: {score}  |  Arrows: move  |  q: quit "\n        stdscr.addstr(oy+bh+1, max(0,(sw-len(hud))//2), hud, curses.color_pair(3))\n        stdscr.refresh()\n\n        key = stdscr.getch()\n        if key == ord("q"): break\n        elif key == curses.KEY_UP and direction != (1,0): direction = (-1,0)\n        elif key == curses.KEY_DOWN and direction != (-1,0): direction = (1,0)\n        elif key == curses.KEY_LEFT and direction != (0,1): direction = (0,-1)\n        elif key == curses.KEY_RIGHT and direction != (0,-1): direction = (0,1)\n\n        ny, nx = snake[0][0]+direction[0], snake[0][1]+direction[1]\n        if ny<=0 or ny>=bh-1 or nx<=0 or nx>=bw-1 or (ny,nx) in snake:\n            break\n        snake.appendleft((ny, nx))\n        if (ny, nx) == food:\n            score += 10\n            food = place_food()\n            speed = max(50, speed-2)\n            stdscr.timeout(speed)\n        else:\n            snake.pop()\n\n    stdscr.nodelay(False)\n    stdscr.timeout(-1)\n    msg = f"  GAME OVER!  Score: {score}  Press any key  "\n    stdscr.addstr(sh//2, max(0,(sw-len(msg))//2), msg, curses.color_pair(2)|curses.A_BOLD)\n    stdscr.refresh()\n    stdscr.getch()\n\nif __name__ == "__main__":\n    curses.wrapper(main)\n'}),
            ("run_command", {"command": "python3 -c \"import curses; print('curses: OK')\" && python3 -c \"exec(open('snake.py').read().split('if __name__')[0]); print('Syntax: OK')\""}),
            ("text", "I've built a complete terminal Snake game!\n\n**Features:** color display, collision detection, progressive speed, score tracking.\n\n**Play it:**\n```\ncd ~/.workspace/projects/demo-snake\npython3 snake.py\n```\nArrow keys to move, eat ◆ to grow, don't hit walls or yourself. Press q to quit."),
        ],
    },
    "api": {
        "steps": [
            ("think", {"thought": "Building a REST API with FastAPI.\n\nComponents:\n1. FastAPI app with CRUD endpoints for tasks\n2. Pydantic models (TaskCreate, TaskUpdate, Task)\n3. In-memory dict storage (zero dependencies)\n4. Status enum (pending/in_progress/done)\n5. Proper HTTP codes, filtering, timestamps\n6. Auto-generated Swagger docs at /docs"}),
            ("architect", {"title": "TODO REST API", "content": "FastAPI + Pydantic + uvicorn.\n\nEndpoints:\n  GET    /tasks          — List (filter by ?status=)\n  POST   /tasks          — Create\n  GET    /tasks/{id}     — Read\n  PUT    /tasks/{id}     — Update\n  DELETE /tasks/{id}     — Delete\n\nModels: Task(id, title, description, status, created_at, updated_at)", "diagram": "  Client                  Server\n    │  POST /tasks          │\n    │──────────────────────▸│ Validate → Store\n    │◂── 201 {task}         │\n    │  GET /tasks?status=   │\n    │──────────────────────▸│ Filter → Return\n    │◂── 200 [tasks]        │\n    │  /docs = Swagger UI   │"}),
            ("create_file", {"path": "api.py", "content": '#!/usr/bin/env python3\n"""TODO REST API — built by Om."""\nfrom fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel, Field\nfrom datetime import datetime\nfrom enum import Enum\nfrom typing import Optional\nimport uuid, uvicorn\n\napp = FastAPI(title="Om TODO API", version="1.0.0")\n\nclass Status(str, Enum):\n    pending = "pending"\n    in_progress = "in_progress"\n    done = "done"\n\nclass TaskCreate(BaseModel):\n    title: str = Field(min_length=1, max_length=200)\n    description: str = ""\n    status: Status = Status.pending\n\nclass TaskUpdate(BaseModel):\n    title: Optional[str] = Field(None, min_length=1, max_length=200)\n    description: Optional[str] = None\n    status: Optional[Status] = None\n\nclass Task(BaseModel):\n    id: str\n    title: str\n    description: str\n    status: Status\n    created_at: datetime\n    updated_at: datetime\n\ntasks: dict[str, Task] = {}\n\n@app.get("/tasks", response_model=list[Task])\ndef list_tasks(status: Optional[Status] = None):\n    result = list(tasks.values())\n    if status:\n        result = [t for t in result if t.status == status]\n    return sorted(result, key=lambda t: t.created_at, reverse=True)\n\n@app.post("/tasks", response_model=Task, status_code=201)\ndef create_task(data: TaskCreate):\n    now = datetime.utcnow()\n    task = Task(id=str(uuid.uuid4())[:8], title=data.title, description=data.description,\n                status=data.status, created_at=now, updated_at=now)\n    tasks[task.id] = task\n    return task\n\n@app.get("/tasks/{task_id}", response_model=Task)\ndef get_task(task_id: str):\n    if task_id not in tasks: raise HTTPException(404, "Task not found")\n    return tasks[task_id]\n\n@app.put("/tasks/{task_id}", response_model=Task)\ndef update_task(task_id: str, data: TaskUpdate):\n    if task_id not in tasks: raise HTTPException(404, "Task not found")\n    task = tasks[task_id]\n    for k, v in data.model_dump(exclude_unset=True).items(): setattr(task, k, v)\n    task.updated_at = datetime.utcnow()\n    return task\n\n@app.delete("/tasks/{task_id}", status_code=204)\ndef delete_task(task_id: str):\n    if task_id not in tasks: raise HTTPException(404, "Task not found")\n    del tasks[task_id]\n\nif __name__ == "__main__":\n    uvicorn.run(app, host="0.0.0.0", port=8000)\n'}),
            ("run_command", {"command": "pip install fastapi uvicorn -q 2>&1 | tail -1 && python3 -c \"import api; print('API loads: OK')\""}),
            ("text", "REST API is ready!\n\n**Endpoints:** Full CRUD for tasks with filtering, validation, timestamps.\n**Swagger docs** auto-generated at `/docs`.\n\n**Run it:**\n```\ncd ~/.workspace/projects/demo-api\npython3 api.py\n```\nThen open http://localhost:8000/docs"),
        ],
    },
}

def run_demo_scenario(key: str):
    scenario = DEMO_SCENARIOS.get(key)
    if not scenario:
        console.print(f"[yellow]Try: {', '.join(DEMO_SCENARIOS.keys())}[/]")
        return
    state.active_project = f"demo-{key}"
    state.project_path
    console.print(f"\n  [green]✓[/] Created project [cyan]demo-{key}[/]\n")
    time.sleep(0.3)
    for stype, data in scenario["steps"]:
        console.print(f"\n  [bold blue]🔧 {stype}[/]")
        time.sleep(0.2)
        if stype in TOOL_DISPATCH:
            TOOL_DISPATCH[stype](data)
        elif stype == "text":
            console.print()
            type_text(data, speed=0.006)
        time.sleep(0.3)
    console.print()

def run_demo_turn(user_input: str):
    lower = user_input.lower()
    if any(w in lower for w in ("snake", "game", "play")):
        state.mode = "game"
        console.print(f"  [green]✓[/] Switched to 🎮 [cyan]Game Development[/]\n")
        run_demo_scenario("snake")
    elif any(w in lower for w in ("api", "rest", "backend", "server", "todo")):
        state.mode = "web"
        console.print(f"  [green]✓[/] Switched to 🌐 [cyan]Full-Stack Web[/]\n")
        run_demo_scenario("api")
    else:
        console.print()
        type_text(f"""Great idea! In live mode I would plan, build, and test it end-to-end.

To see a full demo, try:
  "Build a Snake game"   (game dev)
  "Build a REST API"     (web dev)

To unlock the full agent with a FREE API key:

  Option 1 — Google Gemini (recommended, powerful, free):
    1. Go to aistudio.google.com → Get API key
    2. export GEMINI_API_KEY=your-key
    3. om

  Option 2 — Groq (fast, free):
    1. Go to console.groq.com → API Keys
    2. export GROQ_API_KEY=your-key
    3. om""", speed=0.006)


# ── Session persistence ───────────────────────────────────────────────────────

def save_session(name: str = ""):
    tag = name or datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SESSIONS_DIR / f"{tag}.json"
    data = {"project": state.active_project, "mode": state.mode,
            "messages": state.messages, "saved_at": datetime.now().isoformat()}
    path.write_text(json.dumps(data, default=str), encoding="utf-8")
    console.print(f"  [green]✓[/] Session saved: [cyan]{tag}[/]")

def load_session(name: str) -> bool:
    path = SESSIONS_DIR / f"{name}.json"
    if not path.exists():
        console.print(f"  [red]Session not found: {name}[/]")
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    state.active_project = data.get("project", "default")
    state.mode = data.get("mode", "architect")
    state.messages = data.get("messages", [])
    console.print(f"  [green]✓[/] Loaded [cyan]{name}[/]")
    return True

def list_sessions():
    files = sorted(SESSIONS_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        console.print("  [dim]No saved sessions.[/]")
        return
    for f in files[:20]:
        d = json.loads(f.read_text(encoding="utf-8"))
        console.print(f"  [cyan]{f.stem}[/] — {d.get('project')}, {d.get('mode')}, {d.get('saved_at','?')[:16]}")


# ── Slash commands ────────────────────────────────────────────────────────────

def handle_command(raw: str):
    parts = raw.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/exit":
        console.print(f"\n[dim]Projects at {ROOT_DIR}[/]")
        sys.exit(0)
    elif cmd == "/help":
        show_help()
    elif cmd == "/new":
        name = arg or Prompt.ask("  Project name")
        state.active_project = re.sub(r"[^\w\-.]", "_", name)
        state.messages = []
        state.project_path
        console.print(f"  [green]✓[/] Created [cyan]{state.active_project}[/] at {state.project_path}")
    elif cmd == "/projects":
        dirs = sorted([d for d in ROOT_DIR.iterdir() if d.is_dir()])
        for d in dirs:
            marker = " [green]◀[/]" if d.name == state.active_project else ""
            fc = sum(1 for _ in d.rglob("*") if _.is_file())
            console.print(f"  📁 [cyan]{d.name}[/] ({fc} files){marker}")
    elif cmd == "/switch":
        if arg and (ROOT_DIR / arg).is_dir():
            state.active_project = arg
            state.messages = []
            console.print(f"  [green]✓[/] Switched to [cyan]{arg}[/]")
        else:
            console.print(f"  [red]Project not found: {arg}[/]" if arg else "  [yellow]/switch <name>[/]")
    elif cmd == "/files":
        console.print(Panel(tool_list_directory(), title=f"[cyan]{state.active_project}[/]", border_style="dim"))
    elif cmd == "/mode":
        if arg in MODES:
            state.mode = arg
            console.print(f"  [green]✓[/] {MODES[arg]['icon']} [cyan]{MODES[arg]['label']}[/]")
        else:
            for k, v in MODES.items():
                m = " [green]◀[/]" if k == state.mode else ""
                console.print(f"    {v['icon']} [cyan]{k}[/] — {v['label']}{m}")
    elif cmd == "/clear":
        state.messages = []
        console.print("  [yellow]Cleared.[/]")
    elif cmd == "/save":
        save_session(arg)
    elif cmd == "/load":
        if arg:
            load_session(arg)
        else:
            list_sessions()
    elif cmd == "/sessions":
        list_sessions()
    elif cmd == "/provider":
        show_provider_info()
    else:
        console.print(f"  [yellow]Unknown: {cmd}. /help[/]")


def show_help():
    t = Table(show_header=False, box=None, padding=(0, 2))
    t.add_column(style="cyan bold"); t.add_column(style="dim")
    t.add_row("/new <name>", "Create a new project")
    t.add_row("/projects", "List all projects")
    t.add_row("/switch <name>", "Switch active project")
    t.add_row("/files", "Show project file tree")
    t.add_row("/mode <mode>", "Switch mode (game, ai, web, mobile, systems, data, devops, architect)")
    t.add_row("/clear", "Clear conversation history")
    t.add_row("/save [name]", "Save session")
    t.add_row("/load [name]", "Load session (no arg = list)")
    t.add_row("/provider", "Show AI provider info & setup")
    t.add_row("/help", "Show this help")
    t.add_row("/exit", "Quit")
    console.print(Panel(t, title="[bold]Commands[/]", border_style="dim"))


def show_provider_info():
    t = Table(title="AI Providers", show_lines=True)
    t.add_column("Provider", style="cyan bold")
    t.add_column("Model")
    t.add_column("Cost")
    t.add_column("Env Variable")
    t.add_column("Status")

    providers = [
        ("Gemini", "gemini-2.5-flash", "FREE (15 RPM)", "GEMINI_API_KEY", "gemini"),
        ("Groq", "llama-3.3-70b", "FREE (30 RPM)", "GROQ_API_KEY", "groq"),
        ("Claude", "claude-sonnet-4-6", "Paid ($3/$15 per 1M)", "ANTHROPIC_API_KEY", "claude"),
    ]
    for name, model, cost, env, prov in providers:
        status = "[green bold]● ACTIVE[/]" if PROVIDER == prov else ("[dim]not configured[/]" if not os.environ.get(env) else "[yellow]available[/]")
        t.add_row(name, model, cost, env, status)

    console.print(t)
    console.print("\n[dim]Get free keys:[/]")
    console.print("  Gemini: [cyan]aistudio.google.com[/] → Get API key")
    console.print("  Groq:   [cyan]console.groq.com[/] → API Keys")
    console.print("\n[dim]Force a provider:[/] [cyan]export CREATOR_PROVIDER=gemini|groq|claude[/]")


# ── Welcome ───────────────────────────────────────────────────────────────────

BANNER = r"""
       ___           ___
      /\  \         /\__\          ╭──────────────────────────╮
     /::\  \       /::|  |         │   ॐ   Om — the Creator   │
    /:/\:\  \     /:|:|  |         ╰──────────────────────────╯
   /:/  \:\  \   /:/|:|__|__
  /:/__/ \:\__\ /:/ |::::\__\        Solution architect &
  \:\  \ /:/  / \/__/~~/:/  /        builder for any domain
   \:\  /:/  /        /:/  /
    \:\/:/  /        /:/  /              ⚡ Multi-provider
     \::/  /        /:/  /              🎮 Multi-domain
      \/__/         \/__/               🛠️  Multi-platform
"""

def print_welcome():
    console.print(f"[bold cyan]{BANNER}[/]")

    prov_colors = {"claude": "green", "gemini": "blue", "groq": "magenta", "demo": "yellow"}
    pc = prov_colors.get(PROVIDER, "white")
    engine_label = f"{PROVIDER.upper()} ({MODEL})" if PROVIDER != "demo" else "DEMO"

    extra = ""
    if DEMO_MODE:
        extra = '\n[yellow bold]⚡ DEMO MODE[/] [dim]— type /provider to see how to get a FREE API key[/]'
    elif PROVIDER in ("gemini", "groq"):
        extra = f'\n[green bold]✓ FREE tier active[/] [dim]— {PROVIDER.title()} with tool calling[/]'

    console.print(Panel(
        "[bold]Solution architect & builder for any domain.[/]\n\n"
        f"[dim]Engine:[/] [{pc} bold]{engine_label}[/]    "
        f"[dim]Mode:[/] {MODES[state.mode]['icon']} [cyan]{MODES[state.mode]['label']}[/]    "
        f"[dim]Project:[/] [cyan]{state.active_project}[/]\n"
        f"[dim]Workspace:[/] {ROOT_DIR}"
        f"{extra}\n\n"
        "[dim]Type[/] [cyan]/help[/] [dim]for commands, or describe what you want to build.[/]",
        border_style="blue", padding=(0, 2),
    ))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print_welcome()

    while True:
        mode_info = MODES[state.mode]
        prompt_str = f"\n{mode_info['icon']} [bold green]{state.active_project}[/bold green] [dim]>[/dim]"
        try:
            user_input = Prompt.ask(prompt_str).strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[dim]Goodbye! Projects at {ROOT_DIR}[/]")
            break
        if not user_input:
            continue
        if user_input.startswith("/"):
            handle_command(user_input)
            continue

        if DEMO_MODE:
            run_demo_turn(user_input)
            continue

        state.messages.append({"role": "user", "content": user_input})
        console.print()
        try:
            state.messages = run_turn(state.messages)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
            if state.messages and state.messages[-1].get("role") == "user":
                state.messages.pop()


if __name__ == "__main__":
    main()
