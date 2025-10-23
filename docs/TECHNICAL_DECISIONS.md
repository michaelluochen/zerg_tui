# ZTC Technical Decisions & Research

**Document Version**: 1.0
**Date**: October 21-23, 2025
**Status**: Foundation Phase
**Purpose**: Technical architecture decisions and research findings

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Research Methodology](#research-methodology)
3. [TUI Framework Decision](#tui-framework-decision)
4. [Streaming Architecture](#streaming-architecture)
5. [PTY Management](#pty-management)
6. [Approval Workflow Design](#approval-workflow-design)
7. [Remote Workspace Strategy](#remote-workspace-strategy)
8. [Model-Rendered UI Protocol](#model-rendered-ui-protocol)
9. [Session Multiplexing](#session-multiplexing)
10. [Security & Sandboxing](#security--sandboxing)
11. [Distribution Strategy](#distribution-strategy)
12. [References](#references)

---

## Executive Summary

After comprehensive research into TUI frameworks, terminal-based AI assistants, streaming protocols, and related technologies, we have made the following core technical decisions for ZTC.

### Key Decisions

| Decision Area | Choice | Rationale |
|---------------|--------|-----------|
| **TUI Framework** | Textual (Python) | v4.0.0 designed for LLM streaming; same language as agent; proven with Elia |
| **Streaming Protocol** | WebSocket | Bidirectional, low-latency, handles both streaming and controls |
| **PTY Management** | Python `ptyprocess` + `pexpect` | Native Python support, simple integration with Textual |
| **Approval Pattern** | Multi-level with Plan Mode | Inspired by Cline/Claude Code; balance safety and speed |
| **Remote Strategy** | VS Code Remote Server pattern | Thin client UI, backend server on remote, SSH tunnel |
| **UI Protocol** | Event-driven JSON over WebSocket | Versioned schema, additive-only evolution |
| **Distribution** | PyPI + PyInstaller + Docker | Multi-platform binaries + containerized option |

---

## Research Methodology

### Research Scope

We conducted deep technical research across six key areas:

1. **TUI Frameworks** (Bubble Tea, Textual, Ink, Ratatui)
2. **Terminal-Based AI Tools** (Aider, GitHub Copilot CLI, Warp, Cline, Cursor)
3. **Streaming Protocols** (WebSocket, SSE, gRPC)
4. **PTY & Process Management**
5. **Remote Development Patterns** (VS Code Remote, Telepresence, DevPod)
6. **Model-Rendered UI Protocols** (Jupyter widgets, LSP, MCP)

### Information Sources

- **Official Documentation**: 50+ framework and protocol docs
- **Open Source Projects**: 30+ relevant repositories analyzed
- **Production Examples**: Elia, Aider, OpenCode, GitHub Copilot CLI
- **Specifications**: WebSocket RFC, LSP spec, terminal control sequences

---

## TUI Framework Decision

### Framework Comparison Matrix

| Framework | Stars | Language | Startup | Distribution | LLM Streaming | Ecosystem |
|-----------|-------|----------|---------|--------------|---------------|-----------|
| **Textual** ⭐ | 31.7k | Python | ~300ms | PyInstaller | **v4.0.0 Built-in** | Excellent |
| Bubble Tea | 35.9k | Go | Instant | Static binary | Custom needed | Excellent |
| Ink | 32.4k | TypeScript | ~200ms | pkg/ncc | Custom needed | Strong |
| Ratatui | 15.5k | Rust | Instant | Static binary | Custom needed | Growing |

### Decision: Textual (Python) ⭐

#### Critical Advantages

**1. v4.0.0 "The Streaming Release" (2025)**
- Literally designed for LLM integration
- `Markdown.append()` method specifically for streaming LLM responses
- Asyncio-native for non-blocking operations
- Built for AI chat applications

**2. Proven AI Copilot Implementation**
- **Elia**: Production ChatGPT/Claude terminal client using Textual
- Demonstrates exact use case (streaming, chat interface, markdown rendering)
- Reference implementation we can learn from

**3. Language Alignment**
- Same language as Zerg agent (Python)
- No IPC bridge required (WebSocket in same runtime)
- Simpler architecture, faster iteration
- Shared dependencies (Pydantic, asyncio, etc.)

**4. Rich Widget Library**
```python
from textual.widgets import (
    Markdown,      # For agent responses
    TextArea,      # For user input
    DataTable,     # For structured data
    Tree,          # For file navigation
    ProgressBar,   # For long operations
    RichLog,       # For execution logs
)
```

**5. Dual Deployment Option**
- Runs in terminal (primary)
- **Textual Web**: Deploy same app in browser (future option)

**6. Developer Experience**
- CSS-like styling (TCSS)
- React-inspired reactive patterns with `@reactive` decorator
- Excellent documentation + Real Python tutorials
- Active professional backing (Textualize)

#### Trade-offs Accepted

| Trade-off | Impact | Why Acceptable |
|-----------|--------|----------------|
| Slower startup (~300ms) | User waits briefly | Long-running app, amortized over session |
| Larger binaries (~60MB) | Download size | One-time cost, Docker solves this |
| Python runtime required | Installation complexity | PyInstaller bundles runtime |

#### Why Not Other Frameworks?

**Bubble Tea (Go) - Strong Second Choice**
- ✅ OpenCode proves viability (AI copilot with 75+ LLM providers)
- ✅ Static binary distribution (5-15MB)
- ❌ Requires Go ↔ Python bridge (gRPC/WebSocket)
- ❌ No built-in streaming markdown widget
- ❌ Slower development velocity for Python team

**Ink (TypeScript)**
- ❌ No specific LLM streaming features
- ❌ Node.js dependency adds complexity
- ❌ Packaging challenges (platform-specific)

**Ratatui (Rust)**
- ❌ Requires Rust expertise
- ❌ Smaller ecosystem than Textual/Bubble Tea
- ❌ No AI copilot reference implementations

---

## Streaming Architecture

### Protocol Comparison

| Protocol | Direction | Complexity | Latency | Use Case |
|----------|-----------|------------|---------|----------|
| **WebSocket** ⭐ | Bidirectional | Medium | Low | Interactive agents |
| SSE | Server→Client | Low | Low | Read-only streams |
| gRPC | Bidirectional | High | Low | Backend services |

### Decision: WebSocket

#### Rationale

**1. Bidirectional Requirements**
```
Agent → TUI: Stream responses, send diffs, request approvals
TUI → Agent: Send prompts, approvals, interrupts, cancellations
```
Single connection handles both flows.

**2. Low Latency**
- Real-time feedback critical for UX
- WebSocket minimizes round-trip time (no HTTP overhead)
- Long-lived connection reduces handshake costs

**3. Simplicity for Use Case**
- Native TUI app (not browser-constrained)
- Python `websockets` library is excellent
- Textual async workers integrate seamlessly

**4. Protocol Flexibility**
- Can send streaming text chunks AND structured events
- Single connection, multiple event types
- Easy to add new event types

### Architecture Diagram

```
┌─────────────────┐                    ┌──────────────────┐
│   Textual TUI   │◄──── WebSocket ────┤   Zerg Agent     │
│   (Frontend)    │   (bidirectional)  │   (Backend)      │
└─────────────────┘                    └──────────────────┘
         │                                       │
         │ User Input (approve/reject)           │ LLM Streaming
         │ Interrupt signals                     │ Structured events
         └───────────────────────────────────────┘
```

### Event Types Over WebSocket

#### Agent → TUI: Streaming Text
```json
{
  "type": "text_chunk",
  "content": "Hello",
  "delta": " World"
}
```

#### Agent → TUI: Show Diff
```json
{
  "type": "show_diff",
  "file": "main.py",
  "diff": "unified diff string",
  "syntax": "python",
  "action_id": "uuid"
}
```

#### TUI → Agent: Approval
```json
{
  "type": "approval_response",
  "approved": true,
  "action_id": "abc123"
}
```

#### TUI → Agent: Interrupt
```json
{
  "type": "interrupt",
  "reason": "user_cancel"
}
```

### Backpressure & Flow Control

**Implementation Strategy:**
- **Bounded queues**: Max 1000 events in memory
- **Asyncio flow control**: Native in Python WebSocket libraries
- **Ring buffer**: Limit chat history to 10,000 messages
- **Monitoring**: Warn if queue approaching limit

**Handling Overwhelming Output:**
```python
async def handle_stream(websocket):
    queue = asyncio.Queue(maxsize=1000)

    async for event in websocket:
        try:
            await queue.put(event, timeout=1.0)
        except asyncio.TimeoutError:
            logger.warning("Queue full, dropping old messages")
            # Drop oldest message
            await queue.get()
            await queue.put(event)
```

---

## PTY Management

### Library Selection

#### Evaluated Options
- **Python stdlib `pty`**: Basic PTY support (Unix only)
- **`ptyprocess`**: Cross-platform abstraction
- **`pexpect`**: Higher-level automation (uses `ptyprocess`)

### Decision: `ptyprocess` + `pexpect`

#### Why This Combination?

**`ptyprocess` for low-level PTY:**
- Cross-platform (Unix, limited Windows via ConPTY)
- Clean API for spawning processes with PTYs
- Handles SIGWINCH (window resize)
- Direct control over file descriptors

**`pexpect` for interactive automation:**
- Built on `ptyprocess`
- Pattern matching for command output
- Timeout handling
- Useful for test runners and verification

#### Example Implementation

```python
import ptyprocess
from textual.widgets import RichLog

class ExecutionPane(Widget):
    """Pane for running commands with PTY."""

    def __init__(self):
        super().__init__()
        self.log_widget = RichLog()
        self.process = None

    async def run_command(self, cmd: str):
        """Run command in PTY and stream output."""
        # Spawn process with PTY
        self.process = ptyprocess.PtyProcessUnicode.spawn(
            ['/bin/bash', '-c', cmd],
            cwd=self.workspace_dir,
            env={"TERM": "xterm-256color"}
        )

        # Set PTY size
        self.process.setwinsize(24, 80)

        # Async read loop
        while self.process.isalive():
            try:
                output = await self._read_async()
                self.log_widget.write(output)
            except EOFError:
                break

        # Get exit status
        exit_code = self.process.wait()
        return exit_code

    async def _read_async(self):
        """Non-blocking read from PTY."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.process.read,
            1024
        )
```

### PTY Pane Architecture

```
┌────────────────────────────────────────────────────┐
│  Chat Pane (Agent Streaming)                       │
├────────────────────────────────────────────────────┤
│  Review Pane (Diff Display)       │ Files Pane     │
├────────────────────────────────────────────────────┤
│  Execution Pane (PTY - tests/logs) │ Status Bar    │
└────────────────────────────────────────────────────┘
```

**PTY Usage:**
- ✅ Execution Pane: Run verification commands (pytest, linters)
- ✅ Optional Editor Pane: Embed vim/nano if requested
- ❌ Not Used For: Agent communication (use WebSocket)

### Process Lifecycle Management

**Best Practices:**

1. **Spawning**
   ```python
   process = ptyprocess.PtyProcessUnicode.spawn(
       ['/bin/bash', '-c', cmd],
       cwd=workspace_dir,
       env={
           "TERM": "xterm-256color",
           "COLORTERM": "truecolor",
           "COLUMNS": "80",
           "LINES": "24"
       }
   )
   ```

2. **Signal Handling**
   - **SIGWINCH**: Forward to PTY on terminal resize
   - **SIGTERM**: Graceful shutdown, send SIGHUP to children
   - **SIGINT**: Send Ctrl+C to process

3. **Output Handling**
   - Read in async loop (non-blocking)
   - Parse ANSI sequences (Textual handles this)
   - Buffer with ring buffer (bounded memory)

4. **Cleanup**
   ```python
   def cleanup(self):
       if self.process and self.process.isalive():
           self.process.terminate()
           self.process.wait(timeout=5)
           if self.process.isalive():
               self.process.kill()
   ```

5. **Security**
   - Validate commands before execution
   - Run with least privilege
   - Sandbox untrusted code in containers

---

## Approval Workflow Design

### Research Findings

**Industry Standard Pattern:**
1. **Plan Mode**: Read-only exploration
2. **Review Phase**: Present plan to user
3. **Approval Gate**: Explicit consent
4. **Execute Mode**: Apply changes
5. **Verification**: Show results, allow rollback

### Approval Granularity Comparison

| Tool | Granularity | Speed | Safety |
|------|-------------|-------|--------|
| **Cline** | Plan vs. Act mode | Slow | High |
| **GitHub Copilot CLI** | Per-tool, per-session | Medium | High |
| **Roo Cline** | Auto-approve categories | Fast | Medium |
| **Cursor YOLO** | No approvals | Fastest | Low |

### ZTC Approval System

#### Level 1: Session Trust (One-Time)

```
┌─────────────────────────────────────────┐
│  ZTC needs permission to:               │
│  • Read files in /workspace/project     │
│  • Modify files                         │
│  • Execute commands                     │
│                                         │
│  [Trust Directory] [Cancel]             │
└─────────────────────────────────────────┘
```

**Purpose**: One-time security check per workspace

#### Level 2: Plan Approval (Per-Task)

```
Agent proposes:
┌─────────────────────────────────────────┐
│  PLAN: Fix authentication bug           │
│  ────────────────────────────────────   │
│  1. Update auth.py: Add token refresh   │
│  2. Add tests in test_auth.py           │
│  3. Run pytest                          │
│  4. Update docs/auth.md                 │
│                                         │
│  Estimated changes: 4 files, ~50 lines  │
│                                         │
│  [Approve Plan] [Modify] [Reject]       │
└─────────────────────────────────────────┘
```

**Purpose**: User understands and approves strategy

#### Level 3: Review Changes (Pre-Apply)

```
┌─────────────────────────────────────────┐
│  FILE: auth.py                          │
│  ────────────────────────────────────   │
│  @@ -45,7 +45,12 @@                     │
│  -    return token                      │
│  +    if is_expired(token):             │
│  +        token = refresh_token()       │
│  +    return token                      │
│                                         │
│  [Accept All] [Accept File] [Reject]    │
└─────────────────────────────────────────┘
```

**Purpose**: Review actual code changes before applying

#### Level 4: Dangerous Operations (Explicit Confirm)

```
┌─────────────────────────────────────────┐
│  ⚠️  DANGEROUS OPERATION                 │
│  ────────────────────────────────────   │
│  About to DELETE: old_migration.sql     │
│                                         │
│  This action cannot be undone.          │
│                                         │
│  Type "delete" to confirm: _____        │
│                                         │
│  [Cancel]                               │
└─────────────────────────────────────────┘
```

**Purpose**: Prevent accidental destructive actions

### Workflow Modes

#### Default Mode (Supervised)
- Plan approval required ✓
- File-by-file review for edits ✓
- Explicit confirmation for dangerous ops ✓
- **Best for**: Production work

#### Batch Mode
```bash
ztc --batch
```
- Plan approval required ✓
- Accept all changes at once ✓
- Review later in git ✓
- **Best for**: Prototyping

#### YOLO Mode (Optional)
```bash
ztc --yolo
```
- Plan approval only ✓
- Auto-approve all file changes ✓
- Still block dangerous operations ✓
- **Best for**: Trusted tasks, experienced users

### Git Integration (Auto-Safety Net)

**Automatic Commit After Each Change Group:**
```bash
git commit -m "ZTC: Fix authentication bug - Updated auth.py token refresh

Co-Authored-By: Zerg <noreply@zerg.ai>"
```

**Easy Rollback:**
```bash
# Review last change
git diff HEAD~1

# Undo last ZTC commit
git reset --hard HEAD~1
```

**Branch Isolation:**
- Create feature branch automatically
- User merges when ready
- No risk to main branch

---

## Remote Workspace Strategy

### Pattern: VS Code Remote Server

**Architecture:**

```
┌─────────────────────┐           ┌─────────────────────┐
│   ZTC Client        │           │   ZTC Server        │
│   (Local Machine)   │◄── SSH ───┤   (Remote Machine)  │
│                     │   Tunnel  │                     │
│  • Textual TUI      │           │  • Zerg Agent       │
│  • User interaction │           │  • File operations  │
│  • Display/rendering│           │  • Code execution   │
└─────────────────────┘           └─────────────────────┘
```

### How It Works

**1. Server Installation:**
```bash
# On remote machine
ztc-server install

# Sets up systemd service
sudo systemctl enable ztc-server
sudo systemctl start ztc-server
```

**2. Client Connection:**
```bash
# On local machine
ztc connect user@remote.host:/path/to/workspace
```

- Establishes SSH tunnel
- WebSocket over SSH for communication
- TUI runs locally, agent runs remotely

**3. File Operations:**
- Client sends commands (read, write, search)
- Server executes on remote filesystem
- Results streamed back to client

**4. Execution:**
- Tests/builds run on remote machine
- Output streamed to local TUI
- Interactive PTY sessions tunneled

### Connection Methods

#### 1. Direct SSH (Preferred)
```bash
ztc connect ssh://user@host:22/workspace
```
- Direct SSH connection
- End-to-end encrypted
- No firewall changes needed

#### 2. Reverse Tunnel (Behind Firewall)
```bash
# On remote (behind firewall)
ztc-server expose --token <auth_token>

# On local
ztc connect tunnel://remote-id
```
- Remote initiates outbound connection
- Local connects via relay
- Works behind corporate firewalls

### Session Persistence (tmux-style)

```bash
# Start session
ztc connect user@remote:/workspace

# Detach (Ctrl+B, D)
# Session continues running on remote

# Reattach later (even from different machine)
ztc attach user@remote
```

**Implementation:**
- Server maintains session state
- Multiple clients can attach to same session
- Sessions survive network disconnects

### File Synchronization

**Approach: Event-Based Watching**

```
Remote Server (inotify/fsevents)
    ↓ File change detected
WebSocket Event to Client
    ↓
Client updates local cache/view
```

**No Full Sync:**
- Files stay on remote (VS Code pattern)
- Client caches metadata (file tree, git status)
- Content fetched on-demand

### Security

**SSH Key-Based Auth:**
- Use existing SSH keys
- No password storage
- Respects SSH config (~/.ssh/config)

**Tunnel Encryption:**
- WebSocket over SSH (double encryption)
- AES-256 for tunnel layer

**Permissions:**
- Server respects Unix permissions
- Runs as SSH user (no privilege escalation)

---

## Model-Rendered UI Protocol

### Design Philosophy

**Backend-Driven UI:**
- Agent declares **what** to show, not **how** to render
- TUI interprets intent and renders appropriately
- Similar to Jupyter widgets, LSP partial results

**Declarative, Not Imperative:**
```python
# ✅ Good: Declarative
{"type": "show_diff", "file": "main.py", "diff": "..."}

# ❌ Bad: Imperative
{"type": "move_cursor", "x": 10, "y": 5}
{"type": "draw_text", "text": "diff", "color": "red"}
```

### Event Schema (v0.1.0)

**Event Structure:**
```json
{
  "schema_version": "0.1.0",
  "event_id": "uuid",
  "timestamp": "2025-10-21T12:00:00Z",
  "type": "event_name",
  "payload": { ... }
}
```

### Core Event Types

#### 1. Text Streaming (Agent → TUI)
```json
{
  "type": "text_chunk",
  "payload": {
    "stream_id": "chat_1",
    "delta": " World",
    "content": "Hello World",
    "done": false
  }
}
```

#### 2. Show Diff (Agent → TUI)
```json
{
  "type": "show_diff",
  "payload": {
    "file": "src/main.py",
    "diff": "unified diff string",
    "syntax": "python",
    "action_id": "uuid"
  }
}
```

#### 3. Request Approval (Agent → TUI)
```json
{
  "type": "request_approval",
  "payload": {
    "action_id": "uuid",
    "action": "write_file",
    "description": "Update authentication logic",
    "details": {
      "file": "auth.py",
      "lines_changed": 12
    },
    "level": "normal"
  }
}
```

#### 4. Display Logs (Agent → TUI)
```json
{
  "type": "display_logs",
  "payload": {
    "source": "pytest",
    "logs": "===== test session starts =====\n...",
    "status": "running",
    "progress": 0.5
  }
}
```

#### 5. Approval Response (TUI → Agent)
```json
{
  "type": "approval_response",
  "payload": {
    "action_id": "uuid",
    "approved": true,
    "modifications": null
  }
}
```

#### 6. User Message (TUI → Agent)
```json
{
  "type": "user_message",
  "payload": {
    "content": "Fix the authentication bug",
    "context": {
      "files": ["auth.py"],
      "cursor_position": {"line": 45, "col": 10}
    }
  }
}
```

### Protocol Versioning

**Version Negotiation (Handshake):**
```json
// Client → Server
{
  "type": "handshake",
  "payload": {
    "client_version": "0.1.0",
    "supported_versions": ["0.1.0", "0.2.0"],
    "capabilities": ["diff_view", "approval_flow"]
  }
}

// Server → Client
{
  "type": "handshake_ack",
  "payload": {
    "server_version": "0.1.5",
    "negotiated_version": "0.1.0",
    "capabilities": ["streaming", "pty", "remote"]
  }
}
```

**Evolution Rules:**
1. Never remove/rename existing event types or fields
2. Always add new optional fields
3. Deprecate old fields but keep for compatibility
4. Major version bump for breaking changes
5. Minor version bump for new optional features

---

## Session Multiplexing

### Design: Tabbed Sessions

**Architecture:**

```
┌─────────────────────────────────────────────────────┐
│ [Session 1: Auth Fix] [Session 2: API Refactor] [+] │ ← Tab Bar
├─────────────────────────────────────────────────────┤
│                                                     │
│         Active Session Panes (Layout per session)   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Session Isolation

Each session has:
- Separate WebSocket connection to agent
- Independent workspace context (branch, files)
- Own chat history
- Isolated pane layout

### Implementation

```python
@dataclass
class Session:
    session_id: str
    workspace: Path
    branch: str
    agent_connection: WebSocket
    layout: PaneLayout
    chat_history: List[Message]
    state: SessionState  # planning, executing, idle

class ZTC(App):
    sessions: List[Session]
    active_session: Session

    async def create_session(self, workspace: Path, branch: str):
        session = Session(
            session_id=uuid4(),
            workspace=workspace,
            branch=branch,
            agent_connection=await connect_agent(workspace),
            layout=PaneLayout.default(),
            chat_history=[],
            state=SessionState.IDLE
        )
        self.sessions.append(session)
        self.active_session = session

    def switch_session(self, session_id: str):
        self.active_session = self.get_session(session_id)
        self.refresh_layout()
```

### Session Management

```bash
# Create new session: Ctrl+T
# Switch sessions: Ctrl+1, Ctrl+2, ...
# Cycle forward: Ctrl+Tab
# Cycle backward: Ctrl+Shift+Tab
# Close session: Ctrl+W (with confirmation)
# List sessions: Ctrl+L
```

### Session Comparison View

```
┌─────────────────────────────────────────────────────┐
│ [Compare] Session 1 vs Session 2                    │
├──────────────────────────┬──────────────────────────┤
│  Approach A (Caching)    │  Approach B (Lazy Load)  │
│  ────────────────────    │  ────────────────────    │
│  + cache.py (new)        │  + loader.py (new)       │
│  ~ main.py (12 lines)    │  ~ main.py (8 lines)     │
│                          │                          │
│  Performance: +15%       │  Performance: +8%        │
│  Complexity: Medium      │  Complexity: Low         │
│                          │                          │
│  [Merge This] [Cancel]   │  [Merge This] [Cancel]   │
└──────────────────────────┴──────────────────────────┘
```

---

## Security & Sandboxing

### Threat Model

**Primary Risks:**
1. Untrusted code execution from LLM-generated code
2. File system access (accidental deletion, data leakage)
3. Network access (data exfiltration)
4. Resource exhaustion (infinite loops, memory bombs)
5. Command injection via unsanitized inputs

### Defense Layers

#### Layer 1: Human Approval
- No code execution without explicit approval
- Review all changes before application
- Dangerous operations require typed confirmation

#### Layer 2: Git Safety Net
- All changes committed automatically
- Easy rollback with `git reset`
- Branch isolation

#### Layer 3: Process Sandboxing

**Docker Container for Untrusted Code:**
```python
import docker

def run_sandboxed(command: str, workspace: Path):
    client = docker.from_env()

    container = client.containers.run(
        image="python:3.11-slim",
        command=command,
        volumes={
            str(workspace): {
                'bind': '/workspace',
                'mode': 'ro'  # Read-only
            }
        },
        working_dir='/workspace',
        network_mode='none',  # No network
        mem_limit='512m',     # Memory limit
        cpu_quota=50000,      # CPU limit
        pids_limit=50,        # Process limit
        user='nobody',        # Non-root
        remove=True,          # Auto-remove
        timeout=60            # 60s timeout
    )

    return container
```

#### Layer 4: Command Validation

```python
ALLOWED_COMMANDS = {
    'pytest': ['pytest', 'python', '-m', 'pytest'],
    'ruff': ['ruff', 'check'],
    'mypy': ['mypy'],
}

BLOCKED_PATTERNS = [
    'rm -rf /',
    'dd if=',
    'mkfs',
    ':(){:|:&};:',  # Fork bomb
    'curl', 'wget',  # Network tools
]

def validate_command(cmd: str) -> bool:
    for pattern in BLOCKED_PATTERNS:
        if pattern in cmd:
            raise SecurityError(f"Blocked: {pattern}")

    for allowed in ALLOWED_COMMANDS.values():
        if cmd.startswith(tuple(allowed)):
            return True

    return False  # Require approval
```

#### Layer 5: Filesystem Permissions

```python
def validate_path(path: Path, workspace: Path) -> bool:
    abs_path = path.resolve()
    abs_workspace = workspace.resolve()

    try:
        abs_path.relative_to(abs_workspace)
        return True
    except ValueError:
        raise SecurityError(
            f"Path {path} outside workspace {workspace}"
        )
```

### Audit Logging

```json
{
  "timestamp": "2025-10-21T12:00:00Z",
  "session_id": "session_1",
  "action": "write_file",
  "details": {
    "file": "auth.py",
    "lines_changed": 12,
    "approved_by": "user"
  },
  "outcome": "success"
}
```

**Log Location**: `~/.ztc/audit.log` (redact sensitive paths)

---

## Distribution Strategy

### Multi-Platform Approach

| Platform | Method | Size | Ease of Install |
|----------|--------|------|-----------------|
| **PyPI** | `pip install ztc` | N/A | ⭐⭐⭐⭐⭐ |
| **PyInstaller** | Single binary | ~60MB | ⭐⭐⭐⭐ |
| **Docker** | Container image | ~200MB | ⭐⭐⭐⭐ |
| **Homebrew** | `brew install ztc` | N/A | ⭐⭐⭐⭐⭐ |

### Primary Distribution: PyPI + PyInstaller

#### 1. PyPI (Python Users)
```bash
pip install ztc
ztc --version
```

**Advantages:**
- ✅ Familiar to Python developers
- ✅ Easy updates
- ✅ Automatic dependency resolution

#### 2. PyInstaller (Native Binaries)
```bash
# Build single-file executable
pyinstaller --onefile --name ztc \
  --add-data "textual:textual" \
  --hidden-import ptyprocess \
  ztc/main.py

# Output: dist/ztc (~60-80MB)
```

**Platform-Specific Builds:**
- macOS: `ztc-macos-arm64`, `ztc-macos-x64`
- Linux: `ztc-linux-x64`
- Windows: `ztc-windows.exe`

#### 3. Docker (Optional)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install .

ENTRYPOINT ["ztc"]
```

```bash
docker run -it -v $(pwd):/workspace ztc
```

### Update Mechanism

```python
def check_for_updates():
    current_version = "0.1.0"
    response = requests.get(
        "https://api.github.com/repos/zerg/ztc/releases/latest"
    )
    latest_version = response.json()["tag_name"]

    if latest_version > current_version:
        print(f"New version available: {latest_version}")
        print("Update with: pip install --upgrade ztc")
```

**Frequency**: Check on startup (max once per day)

---

## References

### Key Open Source Projects

- **Elia** (Textual + LLM): https://github.com/darrenburns/elia
- **Aider** (Terminal AI): https://github.com/Aider-AI/aider
- **OpenCode** (Go AI Copilot): https://github.com/opencode-ai/opencode
- **lazygit** (Git TUI): https://github.com/jesseduffield/lazygit

### Documentation

- **Textual**: https://textual.textualize.io/
- **WebSocket RFC**: https://datatracker.ietf.org/doc/html/rfc6455
- **LSP Spec**: https://microsoft.github.io/language-server-protocol/
- **VS Code Remote**: https://code.visualstudio.com/docs/remote/ssh

---

**Last Updated**: October 23, 2025
**Next Review**: After M0 completion
