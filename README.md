# ZTC - Zerg Terminal Client

A terminal-native client for the Zerg AI agent. Built with Python and [Textual](https://textual.textualize.io/), ZTC brings Zerg's real-time copilot capabilities into a keyboard-first, pane-based terminal UI.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [TUI Layout](#tui-layout)
  - [Commands](#commands)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
  - [Event Routing](#event-routing)
- [Example Session](#example-session)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
  - [Setup](#setup)
  - [Running Tests](#running-tests)
  - [Project Structure](#project-structure)
  - [Code Quality](#code-quality)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Before running ZTC, ensure you have:

### 1. Zerg Service Running

The Zerg backend service must be running on `localhost:3333`:

```bash
# In a separate terminal
cd /path/to/zerg
poetry run python zerg/service/launcher.py -c -r -v
```

Verify it's running:
```bash
lsof -i :3333
```

### 2. Python 3.10+

```bash
python --version  # Should be 3.10 or higher
```

### 3. Environment Variables

Set your OpenAI API key (or other LLM provider):

```bash
export OPENAI_API_KEY="your-key-here"

# Make it permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export OPENAI_API_KEY="your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/zerg/zerg-tui.git
cd zerg-tui

# Install with uv (recommended)
uv pip install -e .

# Or install dev dependencies for development
uv pip install -e ".[dev]"
```

### Verify Installation

```bash
ztc --version
ztc --help
```

## Quick Start

```bash
# Launch ZTC
ztc

# With custom workspace
ztc --workspace /path/to/project

# With debug mode
ztc --debug
```

The TUI will start, connect to the Zerg service, and initialize the agent automatically.

## Usage

### TUI Layout

ZTC uses a multi-pane layout optimized for agent workflows:

```
┌─────────────────────────────────────────────────┐
│ ZTC - Zerg Terminal Client                     │
├─────────────────────────┬───────────────────────┤
│ CHAT PANE (60%)         │ REVIEW PANE (60%)     │
│                         │                       │
│ Agent communication     │ Diffs and changes     │
│ appears here            │ appear here           │
│                         ├───────────────────────┤
│                         │ EXECUTION PANE (40%)  │
│                         │                       │
│ [Input box]             │ Logs and output       │
│                         │ appear here           │
├─────────────────────────┴───────────────────────┤
│ ^q Quit  ^t New Session  ^l List Sessions       │
└─────────────────────────────────────────────────┘
```

**Panes:**
- **Chat Pane** (left, 60%): Agent messages, reasoning, errors, warnings
- **Review Pane** (top-right, 60%): Diffs and code changes
- **Execution Pane** (bottom-right, 40%): stdout, stderr, test output

### Commands

Type in the chat input box at the bottom of the Chat pane. ZTC supports two types of commands:

#### Client-Side Commands (Handled by ZTC)

These commands are intercepted by ZTC and don't reach the Zerg service:

```
init      # Re-initialize the Zerg agent
update    # Request full agent state update
```

#### Zerg Service Commands (Sent to Agent)

All other input is sent directly to the Zerg service. The Zerg service interprets these as commands or prompts:

**Information Commands:**
```
help                  # List all available Zerg commands
list_actions          # Show available actions in environment
list_specs            # List all specifications
list_tests            # List all tests
observe_environment   # Get current environment state
```

**Natural Language Prompts:**

Type any message directly - the Zerg agent will interpret it as a prompt:
```
What files are in the current directory?
Explain what this code does
Show me the current state
```

**Note:** Available commands depend on your Zerg service configuration. Type `help` to see all commands available in your instance.

For a complete command reference, see [docs/COMMANDS.md](docs/COMMANDS.md).

### Keyboard Shortcuts

- `Ctrl+Q`: Quit ZTC
- `Ctrl+T`: New session (coming soon)
- `Ctrl+L`: List sessions (coming soon)
- `Ctrl+C`: Cancel current operation (coming soon)

### Event Routing

Events from the Zerg service are automatically routed to the appropriate pane:

**Chat Pane:**
- `zerg_output` - Agent output messages (green)
- `zerg_reasoning` - Agent reasoning steps (yellow italic)
- `zerg_error` - Errors (bold red)
- `zerg_warning` - Warnings (bold yellow)
- `zerg_tests` - Test results (magenta)
- `zerg_evals` - Evaluation results (blue)

**Execution Pane:**
- `stdout` - Standard output (white)
- `stderr` - Standard error (red)
- `zerg_stdout` - Zerg-specific stdout
- `zerg_stderr` - Zerg-specific stderr

**Review Pane:**
- Code diffs and patches (coming soon)
- File changes (coming soon)

## Example Session

Here's what a typical ZTC session looks like:

```
1. Start ZTC:
   $ ztc

2. Connection establishes automatically:

   Chat Pane:
   [SYSTEM] Connecting to http://localhost:3333...
   [SYSTEM] Connected to Zerg service
   [SYSTEM] Connected successfully!
   [SYSTEM] Initializing Zerg agent...
   [OUTPUT] Hello, I'm Zerg ...
   [OUTPUT] zerrrrgg now online ...
   [SYSTEM] Ready! Type a command or message below.

   Execution Pane:
   zerg service connected
   workspace change detected: created
   zerg initialized and updated

3. Try the help command:
   You: help

   Chat Pane:
   [OUTPUT] Available commands:
   [OUTPUT] help, list_actions, list_specs, list_tests, exec, observe_environment...

4. Query the environment:
   You: observe_environment

   Execution Pane:
   workspace change detected: modified

   Chat Pane:
   [OUTPUT] Current environment state: /tmp/zerg/agent_workspace_...

5. Send a natural language prompt:
   You: What files are in the current directory?

   Chat Pane:
   [OUTPUT] Let me check the current directory...
   [REASONING] Using file system observation...
   [OUTPUT] The workspace contains: ...
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (**required**)
- `ZTC_DEBUG` - Enable debug logging (optional, set to `1` or `true`)
- `ZTC_HOST` - Zerg service host (default: `localhost`)
- `ZTC_PORT` - Zerg service port (default: `3333`)

### CLI Options

```bash
ztc --help

Options:
  -w, --workspace PATH  Workspace directory (default: current directory)
  --batch               Enable batch mode (accept all changes at once)
  --yolo                YOLO mode (auto-approve file changes) - USE WITH CAUTION
  --debug               Enable debug mode
  --version             Show version and exit
  --help                Show help message
```

### Project Settings

Create a `.ztcrc` file in your project directory (coming soon):

```json
{
  "auto_approve": false,
  "workspace": ".",
  "ignored_paths": [".git", "node_modules", ".venv"],
  "zerg_url": "http://localhost:3333"
}
```

## Troubleshooting

### "Connection error" or "Failed to connect"

**Cause**: Zerg service is not running or not reachable

**Fix**:
```bash
# Check if Zerg is running
lsof -i :3333

# If not running, start it
cd /path/to/zerg
poetry run python zerg/service/launcher.py -c -r -v

# Check service logs for errors
```

### "Not connected to Zerg service!"

**Cause**: Connection worker failed during initialization

**Fix**:
```bash
# Run with debug mode to see detailed logs
ztc --debug

# Check if firewall is blocking port 3333
# Check if Zerg service started successfully
```

### Import errors or Module not found

**Cause**: Dependencies not installed correctly

**Fix**:
```bash
# Reinstall package and dependencies
uv pip install -e .

# Or force reinstall
uv pip install -e . --reinstall

# Verify installation
python -c "from ztc.app import ZergTerminalClient; print('✓ Imports work')"
```

### TUI rendering issues

**Cause**: Terminal doesn't support required features

**Fix**:
- Ensure your terminal supports 256 colors
- Try resizing terminal window
- Use a modern terminal (iTerm2, Alacritty, Windows Terminal)
- Update Textual: `uv pip install --upgrade textual`

### "Address already in use" (for developers running mock server)

**Cause**: Mock server port 3334 is in use

**Fix**:
```bash
# Kill process on port 3334
lsof -i :3334
kill -9 <PID>

# Or use a different port in tests
```

### "Unknown command" in Execution Pane

**Cause**: Command sent to Zerg service is not recognized

**What's happening:**
- ZTC sends all input (except `init`/`update`) to the Zerg service
- The Zerg service tries to interpret it as a command
- If not recognized, it logs "Unknown command: <text>"

**Fix**:
1. **Use valid Zerg commands** - Type `help` to see available commands
2. **Check command spelling** - Commands are case-sensitive
3. **For natural language prompts** - The Zerg service should handle them, but behavior depends on configuration
4. **Try known working commands**: `help`, `list_actions`, `observe_environment`

**Example**:
```
✗ Wrong: "write a function"     → "Unknown command: write"
✓ Right: "help"                  → Shows command list
✓ Right: "list_actions"          → Shows available actions
✓ Right: "observe_environment"   → Shows environment state
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/zerg/zerg-tui.git
cd zerg-tui

# Install with dev dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run only unit tests (fast)
pytest tests/unit

# Run only integration tests
pytest tests/integration

# Run with HTML coverage report
pytest --cov=ztc --cov-report=html
open htmlcov/index.html
```

See [tests/README.md](tests/README.md) for comprehensive testing documentation.

### Project Structure

```
zerg-tui/
├── .github/
│   └── workflows/
│       └── tests.yml        # CI/CD configuration
├── docs/
│   └── PROJECT_VISION.md    # Full project specification and roadmap
├── tests/
│   ├── unit/                # Unit tests (fast, isolated)
│   ├── integration/         # Integration tests (with mock server)
│   ├── fixtures/            # Test utilities and mock server
│   └── conftest.py          # Shared pytest fixtures
├── ztc/
│   ├── __init__.py          # Package metadata
│   ├── client.py            # Zerg Socket.IO client
│   └── main.py              # TUI application and widgets
├── pyproject.toml           # Project configuration
├── uv.lock                  # Package lock file
└── README.md                # This file
```

### Code Quality

```bash
# Run linter
ruff check ztc tests

# Auto-fix linting issues
ruff check --fix ztc tests

# Format code with black
black ztc tests

# Type checking with mypy
mypy ztc

# Run all quality checks
ruff check ztc tests && black --check ztc tests && mypy ztc
```

### Making Changes

1. Create a feature branch
2. Make your changes
3. Write tests for new functionality
4. Ensure all tests pass: `pytest`
5. Run linters and formatters
6. Commit and create a pull request

## Features

### Current Features

- **Interactive chat** with Zerg agent
- **Real-time streaming** responses with token-by-token display
- **Multi-pane TUI** layout with terminal-native UI
- **Socket.IO communication** with event-driven architecture
- **Event routing** to appropriate panes (chat, review, execution)
- **Color-coded output** for different event types
- **Async architecture** for responsive UI
- **Keyboard shortcuts** for all actions

### In Development

Per the [project vision](docs/PROJECT_VISION.md), upcoming features include:

- **Diff viewer** - Syntax-highlighted code diffs in Review pane
- **Approval workflow** - Approve/reject changes with keyboard controls
- **Session multiplexing** - Multiple agent sessions in tabs (like tmux)
- **Remote workspaces** - Work on remote servers via SSH
- **Session persistence** - Save and restore conversation history
- **Git integration** - Visual git status and commit management
- **File browser** - Navigate project files in a dedicated pane

See [docs/PROJECT_VISION.md](docs/PROJECT_VISION.md) for the complete roadmap and architecture details.

## Contributing

We welcome contributions! Here's how to get started:

### Reporting Issues

- Check [existing issues](https://github.com/zerg/zerg-tui/issues) first
- Provide clear steps to reproduce
- Include error messages and logs (with `--debug` flag)
- Specify your OS, Python version, and terminal emulator

### Contributing Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Write tests for new features
4. Ensure all tests pass: `pytest`
5. Run linters: `ruff check .` and `black .`
6. Commit with clear messages
7. Push and create a pull request

### Development Guidelines

- Follow existing code style (enforced by black and ruff)
- Write tests for all new functionality
- Maintain or improve test coverage (target: 80%+)
- Update documentation as needed
- Keep commits atomic and well-described

### First-Time Contributors

Good first issues:
- Add new keyboard shortcuts
- Improve error messages
- Add more test cases
- Improve documentation
- Fix typos or formatting

## License

MIT - See [LICENSE](LICENSE) file for details.

---

**Project Status**: Alpha (Phase 1 - Foundation)
**Version**: 0.1.0
**Python**: 3.10+
**Framework**: Textual

For detailed architecture and design decisions, see [docs/PROJECT_VISION.md](docs/PROJECT_VISION.md).
