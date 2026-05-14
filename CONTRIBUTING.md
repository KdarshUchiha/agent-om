# Contributing to CreatorAgent

Thanks for your interest in contributing! 🎉

## 🐛 Reporting Issues

Open an [issue](https://github.com/YOUR_USERNAME/creatoragent/issues) with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your platform (OS, Python version, provider)

## 🚀 Submitting Pull Requests

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test your changes:
   ```bash
   pip install -e ".[all]"
   creatoragent --demo  # smoke test
   ```
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

## 💡 Ideas for Contributions

- **New providers**: Add support for OpenAI, Mistral, Cohere, Ollama, etc.
- **New domain modes**: Embedded, robotics, blockchain, etc.
- **New tools**: Image generation, audio processing, browser automation, etc.
- **UI improvements**: TUI dashboard, themes, widgets
- **Examples**: More demo scenarios in `DEMO_SCENARIOS`
- **Tests**: Unit tests, integration tests, CI improvements
- **Docs**: Tutorials, video guides, architecture docs

## 🧪 Code Style

- Use type hints where helpful
- Keep functions focused and small
- Match the existing code style
- No need for extensive comments — let the code speak

## 📦 Architecture Quick Tour

```
creatoragent/
├── creatoragent/agent.py       # Main entry point + all logic
│   ├── detect_provider()        # Auto-detect AI provider from env
│   ├── MODES                    # Domain mode definitions
│   ├── TOOLS / OPENAI_TOOLS     # Tool schemas
│   ├── tool_*()                 # Tool implementations
│   ├── run_turn_claude()        # Claude provider loop
│   ├── run_turn_gemini()        # Gemini provider loop
│   ├── run_turn_groq()          # Groq provider loop
│   └── DEMO_SCENARIOS           # Demo mode pre-scripted demos
├── build_scripts/               # Per-platform build scripts
└── .github/workflows/release.yml # Auto-build pipeline
```

## 📝 License

By contributing, you agree your contributions will be licensed under MIT.
