# 🤖 CreatorAgent

> **God-tier AI solution architect & builder.** Build AAA games, agentic AI systems, full-stack apps, mobile apps, infrastructure — any domain, any platform.

Multi-provider LLM agent CLI that works with **free** AI providers (Gemini, Groq) or paid (Claude). No API key needed for demo mode.

```
   ____                _              _                    _
  / ___|_ __ ___  __ _| |_ ___  _ __/ \   __ _  ___ _ __ | |_
 | |   | '__/ _ \/ _` | __/ _ \| '__/ _ \ / _` |/ _ \ '_ \| __|
 | |___| | |  __/ (_| | || (_) | | / ___ \ (_| |  __/ | | | |_
  \____|_|  \___|\__,_|\__\___/|_|/_/   \_\__, |\___|_| |_|\__|
                                           |___/
```

## ⚡ Install

### 🐍 Via pip (any platform with Python 3.10+)

```bash
# Free providers (Gemini + Groq)
pip install "creatoragent[gemini,groq] @ git+https://github.com/YOUR_USERNAME/creatoragent.git"

# Or with all providers including Claude
pip install "creatoragent[all] @ git+https://github.com/YOUR_USERNAME/creatoragent.git"
```

### 📥 Via native binary (no Python needed)

Grab the right one from the [Releases](https://github.com/YOUR_USERNAME/creatoragent/releases/latest) page:

| Platform | File |
|---|---|
| 🐧 **Linux** | `creatoragent-linux-x64.tar.gz` or `creatoragent_1.0.0_amd64.deb` |
| 🪟 **Windows** | `creatoragent.exe` or `creatoragent-windows-x64.zip` |
| 🍎 **macOS (Apple Silicon)** | `CreatorAgent-1.0.0-arm64.dmg` |
| 🍎 **macOS (Intel)** | `CreatorAgent-1.0.0-x86_64.dmg` |

Quick install snippets:
```bash
# Linux
curl -L https://github.com/YOUR_USERNAME/creatoragent/releases/latest/download/creatoragent-linux-x64.tar.gz | tar -xz
sudo mv creatoragent /usr/local/bin/

# macOS (Apple Silicon)
curl -LO https://github.com/YOUR_USERNAME/creatoragent/releases/latest/download/CreatorAgent-1.0.0-arm64.dmg
open CreatorAgent-1.0.0-arm64.dmg

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/YOUR_USERNAME/creatoragent/releases/latest/download/creatoragent.exe" -OutFile creatoragent.exe
```

## 🚀 Quick Start

```bash
# Demo mode (no API key needed)
creatoragent --demo

# With FREE Gemini API (recommended)
export GEMINI_API_KEY=your-key   # get from aistudio.google.com
creatoragent

# With FREE Groq API (super fast)
export GROQ_API_KEY=your-key     # get from console.groq.com
creatoragent

# With Claude API (paid, most capable)
export ANTHROPIC_API_KEY=your-key
creatoragent
```

Once running, just describe what you want:
```
🏗️ default > Build a multiplayer Snake game with WebSockets

💭 Planning... [architecture breakdown]
📐 System Design [diagram]
🔧 create_file server.py
🔧 create_file static/index.html
🔧 run_command python3 -c "import server; print('OK')"
✅ Done! Run: python3 server.py
```

## ✨ Features

### 🎯 8 Domain Modes
The agent specializes its expertise based on your task:

| Mode | Specialization |
|---|---|
| 🏗️ **Architect** | System design, trade-offs, ADRs, scalability patterns |
| 🎮 **Game** | ECS, game loops, rendering, UE5/Unity/Godot, multiplayer |
| 🧠 **AI/ML** | Transformers, RAG, agents, MLOps, fine-tuning |
| 🌐 **Web** | React/Next.js, FastAPI, databases, auth, deployment |
| 📱 **Mobile** | Flutter, React Native, SwiftUI, Jetpack Compose |
| ⚙️ **Systems** | Rust, C++, concurrency, embedded, performance |
| 📊 **Data** | Spark, Kafka, warehouses, pipelines, streaming |
| 🔧 **DevOps** | K8s, Terraform, CI/CD, observability, SRE |

Switch modes with `/mode game`, `/mode ai`, etc.

### 🔧 8 Powerful Tools
The agent autonomously uses these tools to build:
- **create_file** — write complete production-quality files
- **read_file** — understand existing code
- **edit_file** — surgical find-and-replace edits
- **run_command** — execute shell commands, install packages, run tests
- **list_directory** — browse the project tree
- **search_files** — regex search across files
- **think** — plan before acting on complex tasks
- **architect** — output design diagrams and component breakdowns

### 🤖 3 AI Providers

| Provider | Model | Cost | Free Tier | Best For |
|---|---|---|---|---|
| **Gemini** | gemini-2.5-flash | **FREE** | 15 RPM, 1M TPM | Daily use, recommended |
| **Groq** | llama-3.3-70b | **FREE** | 30 RPM | Speed-critical workflows |
| **Claude** | claude-sonnet-4-6 | Paid | — | Highest quality |

## 📋 Commands

```
/new <name>      Create a new project
/projects        List all projects
/switch <name>   Switch active project
/files           Show project file tree
/mode <mode>     Switch domain mode
/clear           Clear conversation history
/save [name]     Save conversation session
/load [name]     Load a saved session (no arg = list)
/provider        Show AI provider info & setup
/help            Show all commands
/exit            Quit
```

## 🌟 Examples

### Build a complete REST API
```
🌐 web > Create a FastAPI backend for a todo app with PostgreSQL,
        JWT auth, and Docker setup
```

### Build a 2D platformer
```
🎮 game > Build a 2D platformer with Pygame including character physics,
        enemies, levels, and collectibles
```

### Build an AI agent
```
🧠 ai > Create a RAG-based chatbot using LangChain that ingests PDFs
       and answers questions with citations
```

### Build a microservice
```
🏗️ architect > Design and implement an event-driven order processing
              service with Kafka, Redis cache, and PostgreSQL
```

## 🔐 Environment Variables

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (free) |
| `GROQ_API_KEY` | Groq API key (free) |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key (paid) |
| `CREATOR_PROVIDER` | Force a provider: `gemini`, `groq`, or `claude` |
| `CREATOR_MODEL` | Override the model (e.g. `gemini-2.5-pro`) |
| `CREATOR_DEMO` | Set to `1` to force demo mode |

## 🛠️ Build From Source

```bash
git clone https://github.com/YOUR_USERNAME/creatoragent.git
cd creatoragent
pip install -e ".[all]"
creatoragent
```

For native binaries, see [BUILD.md](BUILD.md).

## 🤝 Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📜 License

MIT — see [LICENSE](LICENSE).

## 🙏 Acknowledgments

Built with [Rich](https://github.com/Textualize/rich) for the beautiful terminal UI, and powered by [Anthropic Claude](https://anthropic.com), [Google Gemini](https://ai.google.dev), and [Groq](https://groq.com).

---

**⭐ If this tool helps you, give it a star!**
