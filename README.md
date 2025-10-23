# ZTC - Zerg Terminal Client

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A terminal-native client for the Zerg AI agent with real-time copilot capabilities. ZTC brings Claude Code-like flow into the terminal with composable views, fast iteration, and keyboard-first interaction.

![ZTC Demo](docs/demo.gif)
<!-- Add screenshot/demo when available -->

## 🎯 Vision

ZTC is not a CLI tool or command zoo—it's a single TUI application that encapsulates Zerg's planning, editing, review, and verification loops behind a clean, pane-based interface. Think tmux meets AI agent, purpose-built for developers who live in the terminal.

## ✨ Features

- **🗨️ Agent Chat Pane** - Live streaming responses with structured actions
- **📝 Change Review Pane** - Readable diffs with approve/reject controls
- **🔧 Execution/Logs Pane** - Real-time verification output (tests, linters)
- **📁 Workspace View** - File/folder navigation at a glance
- **🎨 Flexible Layout** - tmux-like splits and customizable pane arrangements
- **🔀 Session Multiplexing** - Run multiple agent contexts in parallel
- **🌐 Remote Contexts** - Attach to remote workspaces via SSH
- **✅ Supervised Control** - Multi-level approval system (no writes without consent)
- **📋 Audit Log** - Human-readable activity log of all changes

## 🚀 Quick Start

### Installation

#### Via uv (Recommended)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/zerg/zerg-tui.git
cd zerg-tui

# Install dependencies
uv sync

# Run ZTC
uv run ztc
```

#### Via pip
```bash
pip install ztc
ztc
```

#### Via PyInstaller Binary
```bash
# Download for your platform
curl -LO https://github.com/zerg/ztc/releases/latest/download/ztc-macos-arm64

# Make executable and run
chmod +x ztc-macos-arm64
./ztc-macos-arm64
```

### Basic Usage

```bash
# Launch ZTC in current directory
ztc

# Specify workspace
ztc -w /path/to/project

# Enable batch mode (faster for prototyping)
ztc --batch

# YOLO mode (auto-approve file changes)
ztc --yolo

# Connect to remote workspace
ztc connect user@remote.host:/workspace
```

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Q` | Quit |
| `Ctrl+T` | New Session |
| `Ctrl+L` | List Sessions |
| `Ctrl+1-9` | Switch to session N |
| `Ctrl+Tab` | Cycle sessions forward |
| `Ctrl+Shift+Tab` | Cycle sessions backward |
| `Ctrl+W` | Close current session |
| `Escape` | Cancel/Go back |

## 🏗️ Architecture

ZTC is built with [Textual](https://textual.textualize.io/) and follows Elia's proven architecture for terminal LLM interfaces:

```
┌─────────────────────────────────────────────────────────┐
│  ZTC Client (Textual TUI)                               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Chat Pane   │  │ Review Pane  │  │ Execution Pane │ │
│  │ (Streaming) │  │ (Diffs)      │  │ (Logs/Tests)   │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ⬇️ WebSocket
┌─────────────────────────────────────────────────────────┐
│  Zerg Agent (Backend)                                    │
│  • Planning & Code Generation                            │
│  • Patch Creation & Verification                         │
│  • Git Operations                                        │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

- **Framework**: Textual (Python)
- **Streaming**: WebSocket for bidirectional agent ↔ TUI communication
- **PTY Management**: ptyprocess + pexpect
- **Git Integration**: GitPython
- **Persistence**: SQLite (sessions) + aiosqlite (async)
- **Distribution**: PyInstaller + Docker

## 📖 Workflow

### 1. Guided Fix
```
User: "Fix the authentication bug"
  ⬇️
Agent proposes plan
  ⬇️
User reviews in Review Pane
  ⬇️
User approves changes
  ⬇️
Verification runs (tests stream to Execution Pane)
  ⬇️
Changes committed to git
```

### 2. Parallel Exploration
```
Session 1: Try approach A (caching)
Session 2: Try approach B (lazy loading)
  ⬇️
Compare diffs side-by-side
  ⬇️
Merge preferred approach
```

### 3. Remote Development
```
Local Terminal
  ⬇️ SSH Tunnel
Remote Workspace
  ⬇️
Same review/approval UX
  ⬇️
Changes applied remotely
```

## 🔒 Security

ZTC implements multiple security layers:

1. **Human Approval** - No file writes without explicit consent
2. **Git Safety Net** - All changes auto-committed for easy rollback
3. **Process Sandboxing** - Docker containers for untrusted code execution
4. **Command Validation** - Allowlist approach for safe operations
5. **Workspace Isolation** - Cannot access outside approved directories
6. **Audit Logging** - All actions logged to `~/.ztc/audit.log`

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/zerg/zerg-tui.git
cd zerg-tui

# Install dependencies including dev tools
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy ztc/
```

### Project Structure

```
zerg-tui/
├── ztc/                    # Main application code
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── server.py          # Agent server (remote)
│   ├── screens/           # Textual screens
│   ├── widgets/           # Custom widgets
│   └── models/            # Data models
├── docs/                  # Documentation
│   ├── PROJECT_VISION.md
│   └── TECHNICAL_DECISIONS.md
├── tests/                 # Test suite
├── pyproject.toml        # Project config
└── README.md
```

## 📚 Documentation

- [Project Vision](docs/PROJECT_VISION.md) - Project vision, scope, and user flows
- [Technical Decisions](docs/TECHNICAL_DECISIONS.md) - Architecture and research decisions
- [Contributing Guide](CONTRIBUTING.md) - How to contribute (coming soon)
- [API Reference](docs/api.md) - API documentation (coming soon)

## 🗺️ Roadmap

### Phase 1: Foundation (M0) - ✅ Current
- [x] Textual app skeleton with basic layout
- [ ] WebSocket client/server communication
- [ ] Streaming chat pane
- [ ] Event schema (v0.1.0)
- [ ] Basic approval dialog

### Phase 2: Core Features (M1)
- [ ] Plan mode and review UI
- [ ] Diff view widget with syntax highlighting
- [ ] PTY execution pane
- [ ] File tree navigation
- [ ] Git integration (auto-commit)
- [ ] Multi-level approval system
- [ ] Session persistence

### Phase 3: Multiplexing & Remote (M2)
- [ ] Tabbed session UI
- [ ] Session comparison view
- [ ] Remote server component
- [ ] SSH tunnel integration
- [ ] Remote file operations

### Phase 4: Polish & Distribution (M3)
- [ ] PyPI package
- [ ] PyInstaller binaries
- [ ] Docker image
- [ ] Comprehensive documentation
- [ ] Security audit

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Textual](https://textual.textualize.io/) - Amazing terminal UI framework
- [Elia](https://github.com/darrenburns/elia) - Inspiration for LLM streaming patterns
- [Aider](https://aider.chat/) - Terminal AI pair programming reference
- [Bubble Tea](https://github.com/charmbracelet/bubbletea) - Go TUI framework inspiration

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/zerg/zerg-tui/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zerg/zerg-tui/discussions)
- **Website**: https://zerg.ai
- **Email**: team@zerg.ai

---

**Status**: 🚧 Alpha - Under active development

Built with ❤️ by the Zerg Team
