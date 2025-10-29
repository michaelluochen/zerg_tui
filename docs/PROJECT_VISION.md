# ZTC Project Vision & Specification

> **Note**: For installation and usage instructions, see [README.md](../README.md). This document covers the project vision, architecture, and design decisions.

**Project**: Zerg Terminal Client (ZTC)
**Date**: October 20, 2025
**Status**: Foundation Phase (M0)
**Version**: 1.0

---

## Table of Contents

1. [Purpose & Vision](#purpose--vision)
2. [Scope](#scope)
3. [Core UX Principles](#core-ux-principles)
4. [Architecture Overview](#architecture-overview)
5. [User Flows](#user-flows)
6. [Principles & Differentiators](#principles--differentiators)
7. [Open Questions](#open-questions)

---

## Purpose & Vision

Build a **terminal-native client for Zerg** — a focused, keyboard-first TUI experience that brings the Zerg agent's real-time copilot capabilities into the terminal. Think Claude Code-like flow, but shaped by what terminals are uniquely good at: composable views, fast iteration, and low-latency feedback.

### What ZTC Is

- A **single TUI application** (not a CLI tool or command zoo)
- Encapsulates Zerg's planning, editing, review, and verification loops
- Clean, pane-based interface with tmux-like flexibility
- Purpose-built for developers who live in the terminal

### What ZTC Is Not

- Not a command-line utility with subcommands
- Not a full IDE replacement
- Not a web interface masquerading as a terminal app

---

## Scope

### Core Features

#### 1. Agent Chat Pane
- **Live streaming** responses with structured actions from Zerg agent
- **Real-time feedback** with low-latency token streaming
- **Message history** with searchable conversation log
- **Context-aware** prompts with file/code references

#### 2. Change Review Pane
- **Readable diffs** presented as syntax-highlighted patches
- **Approve/Reject controls** with file-level or hunk-level granularity
- **Side-by-side comparison** for reviewing proposed changes
- **Git integration** showing working tree status

#### 3. Execution/Logs Pane
- **Non-blocking execution** of verification steps (tests, linters)
- **Streaming output** from long-running commands
- **Clear status signals** (running, passed, failed)
- **ANSI color support** for terminal output

#### 4. Workspace View
- **File/folder navigation** at a glance
- **Git status indicators** for modified files
- **Quick file access** with fuzzy search
- **Project structure** visualization

#### 5. Layout Manager
- **tmux-like splits** (vertical/horizontal)
- **Resizable panes** with keyboard shortcuts
- **Tabbed views** for multiple sessions
- **Preset layouts** (Chat-centric, Review-centric, Logs-centric)
- **Persistent configuration** saved per workspace

#### 6. Session Multiplexing
- **Multiple agent contexts** in parallel (e.g., separate tasks/branches)
- **Session switching** with Ctrl+1-9, Ctrl+Tab
- **Session comparison** view for evaluating different approaches
- **Independent state** per session (workspace, branch, history)

#### 7. Remote Contexts
- **Attach to remote workspaces** via SSH
- **Streaming agent output** from remote to local terminal
- **Remote file operations** (read, write, diff)
- **Session persistence** across network disconnects (tmux-style)

#### 8. Model-Rendered UI
- **Agent-declared UI elements** (e.g., "show diff", "await approval")
- **Consistent rendering** by the TUI client
- **Extensible protocol** for future UI components
- **Backward compatible** event schema

#### 9. Auditability
- **Local activity log** of plans, approvals, and outcomes
- **Human-readable format** (not just JSON dumps)
- **Privacy-aware** redaction of sensitive paths
- **Queryable history** for debugging and review

---

## Core UX Principles

### 1. Terminal-Native Experience

**Pane Manager**
- Flexible, tmux-like layout system
- Vertical/horizontal splits with keyboard control
- Resizable panes (Ctrl+Arrow keys)
- Quick preset switching:
  - **Chat-centric**: Large chat pane, small side panels
  - **Review-centric**: Large diff view, chat on side
  - **Logs-centric**: Large execution pane, minimal chat

**Keyboard-First**
- All actions accessible via keyboard shortcuts
- No mouse required (but mouse supported for convenience)
- Vim-style navigation where appropriate
- Clear visual feedback for all actions

### 2. Agent-First Flow

```
User describes task
    ↓
Agent proposes plan (read-only exploration)
    ↓
TUI presents plan clearly in Review Pane
    ↓
User explicitly approves
    ↓
Changes applied (with git auto-commit)
    ↓
Verification runs (streaming to Execution Pane)
    ↓
Results clearly indicated (✓ or ✗)
```

### 3. Non-Blocking Execution

- **Long-running tasks** stream output without freezing UI
- **Parallel operations** supported (e.g., test while reviewing diff)
- **Cancellable** operations with Ctrl+C or Escape
- **Background jobs** continue even when switching sessions

### 4. Editor Compatibility

- **Terminal editor support** (vim, nano) in dedicated pane
- **External editor** option to jump out seamlessly
- **No IDE required** — ZTC respects existing workflows
- **File watching** detects external edits and refreshes UI

---

## Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    ZTC TUI Client                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Pane Manager (Layout System)                      │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │ │
│  │  │  Chat    │  │  Review  │  │  Execution/Logs  │ │ │
│  │  │  Pane    │  │  Pane    │  │  Pane            │ │ │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────┐  │ │
│  │  │  Workspace/File Tree Pane                    │  │ │
│  │  └──────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────┘ │
│                           ⬇️ WebSocket                   │
└─────────────────────────────────────────────────────────┘
                           ⬇️
┌─────────────────────────────────────────────────────────┐
│                    Zerg Agent (Backend)                 │
│  • Planning & strategy                                  │
│  • Code generation & editing                            │
│  • Patch creation & application                         │
│  • Verification orchestration (tests, linters)          │
│  • Git operations & commit management                   │
│  • Context gathering (codebase, docs, errors)           │
└─────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. ZTC TUI Application
- **Cross-platform** terminal application (macOS, Linux, Windows)
- **Textual framework** for rendering and layout management
- **Async event loop** for responsive UI
- **State management** for sessions, config, and history

#### 2. Zerg Agent
- **Planning engine** for task decomposition
- **Code editor** with patch generation
- **Verification runner** for tests and checks
- **Git orchestrator** for commits and branches
- **Context provider** for relevant code/docs

#### 3. Streaming Channel
- **WebSocket connection** for bidirectional communication
- **Low-latency streaming** for real-time token delivery
- **Event-driven** for structured actions (diffs, approvals, logs)
- **Reconnection handling** for network resilience

#### 4. Model-Rendered UI Protocol (v0)
- **Minimal event schema** where agent expresses intent
- **UI declarations**: `show_diff`, `request_approval`, `display_logs`
- **TUI interpretation** renders appropriate widgets
- **Versioned protocol** for backward compatibility

#### 5. PTY/Process Bridge
- **Terminal emulation** for running local/remote processes
- **Shell support** (bash, zsh, fish)
- **Editor embedding** (vim, nano) in dedicated pane
- **Test runner** integration (pytest, jest, etc.)

### Data Flow

```
User Input (keyboard/mouse)
    ↓
TUI Event Handler
    ↓
WebSocket Message to Agent
    ↓
Agent Processing (LLM, tools, git)
    ↓
WebSocket Stream to TUI (tokens, events)
    ↓
TUI Widget Updates (reactive)
    ↓
Screen Refresh (diff, logs, status)
```

---

## User Flows

### Flow 1: Guided Fix

**Scenario**: User wants to fix a bug in their codebase

```
1. User launches ZTC in project directory
   $ ztc

2. User describes issue in chat pane
   > "Fix the authentication timeout bug in auth.py"

3. Agent analyzes codebase and proposes plan
   PLAN:
   - Update auth.py: Add token refresh logic
   - Add tests in test_auth.py for refresh flow
   - Run pytest to verify fix
   - Update docs/auth.md with new behavior

4. ZTC opens review pane with proposed changes
   [Review Pane shows diff]
   auth.py:
   @@ -45,7 +45,12 @@
   -    return token
   +    if is_expired(token):
   +        token = refresh_token()
   +    return token

   [Approve] [Modify] [Reject]

5. User approves changes
   User presses Enter on [Approve]

6. Agent applies changes and runs verification
   [Execution Pane streams output]
   Running: pytest tests/test_auth.py
   ===== test session starts =====
   collected 12 items
   tests/test_auth.py ............ [100%]
   ===== 12 passed in 2.34s =====

7. Changes committed to git
   [Git status updated]
   ✓ Committed: "Fix auth token refresh logic"

8. User reviews final state
   All tests passed ✓
   Files modified: auth.py (+5 lines), test_auth.py (+15 lines)
```

**Duration**: ~2-3 minutes for simple bug fix

---

### Flow 2: Parallel Task Exploration

**Scenario**: User wants to try two different approaches

```
1. User creates first session
   Ctrl+T (new tab)
   Session 1: "Try fixing with caching"

2. Agent proposes caching solution in Session 1
   [Review shows cache implementation]

3. User creates second session without closing first
   Ctrl+T (new tab)
   Session 2: "Try fixing with lazy loading"

4. Agent proposes lazy loading in Session 2
   [Review shows lazy loading implementation]

5. User switches between sessions to compare
   Ctrl+1: View caching approach
   Ctrl+2: View lazy loading approach

6. User opens comparison view
   Ctrl+Shift+C (compare sessions)
   [Split screen shows both diffs side-by-side]

   Session 1 (Caching)       │  Session 2 (Lazy Loading)
   ─────────────────────────┼──────────────────────────
   + cache.py (new)          │  + loader.py (new)
   ~ main.py (12 lines)      │  ~ main.py (8 lines)
   Performance: +15%         │  Performance: +8%
   Complexity: Medium        │  Complexity: Low

7. User selects preferred approach
   [Merge This] on Session 2

8. Session 2 changes merged, Session 1 discarded
```

**Duration**: ~10-15 minutes for exploration and decision

---

### Flow 3: Remote Workspace

**Scenario**: User needs to work on remote server

```
1. User connects to remote workspace
   $ ztc connect user@dev-server.com:/workspace/api

2. ZTC establishes SSH tunnel
   Connecting to dev-server.com...
   SSH tunnel established ✓
   Agent running on remote ✓

3. User works normally with remote context
   > "Add rate limiting to API endpoints"

4. Agent operates on remote filesystem
   [Diffs show remote file changes]
   Remote: /workspace/api/middleware/rate_limit.py

5. Verification runs on remote machine
   [Logs stream from remote]
   Remote: Running pytest on dev-server.com
   [test output streams to local TUI]

6. Changes applied and committed remotely
   Remote git commit: "Add rate limiting middleware"

7. User detaches session
   Ctrl+B, D (tmux-style detach)
   Session saved on remote ✓

8. User reattaches later (even from different machine)
   $ ztc attach user@dev-server.com
   Session restored ✓
```

**Duration**: Same as local workflow (network latency minimal)

---

## Principles & Differentiators

### Core Principles

1. **Terminal-Native, Not Bolted-On**
   - Purpose-built TUI, not a CLI wrapped in ncurses
   - Leverages terminal strengths: composability, speed, keyboard control
   - Respects terminal conventions (ANSI colors, Ctrl+C, etc.)

2. **Supervised Control**
   - No file writes without explicit user approval
   - Multi-level approval system (session, plan, change, dangerous ops)
   - Git safety net with auto-commits for easy rollback
   - Audit log for all actions

3. **Session Multiplexing**
   - Embrace terminals' strength in running multiple tasks
   - Compare approaches side-by-side
   - Switch contexts instantly
   - Independent state per session

4. **Remote-First**
   - Local and remote workspaces treated as first-class
   - Unified UX regardless of location
   - Session persistence across network issues
   - SSH tunnel for secure communication

5. **Model-Rendered UI**
   - Keep client simple and focused on presentation
   - Agent declares what to show, TUI handles how
   - Extensible protocol for future features
   - Backward compatible for older clients

### Key Differentiators

**vs. Aider (Terminal AI Assistant)**
- ZTC: Multi-pane TUI with parallel sessions
- Aider: Single-thread terminal output
- ZTC: Session multiplexing for exploring alternatives
- Aider: Linear conversation only

**vs. GitHub Copilot CLI**
- ZTC: Rich TUI with structured workflows
- Copilot CLI: Command output only
- ZTC: Change review with diff viewer
- Copilot CLI: Accept/reject at command level

**vs. Cursor/Cline (IDE Extensions)**
- ZTC: Terminal-native, no IDE required
- IDE Extensions: Tied to specific editor
- ZTC: Remote workspace support built-in
- IDE Extensions: Depends on IDE's remote capabilities

**vs. Claude Code (Desktop App)**
- ZTC: Runs in terminal (tmux, SSH, etc.)
- Claude Code: Separate desktop application
- ZTC: Session multiplexing with tabs
- Claude Code: Single session focus

---

## Open Questions

### Framework & Technology

**Q1: Editor Embedding vs. External Hand-off?**
- **Option A**: Embed vim/nano in PTY pane (full integration)
- **Option B**: External editor only (simpler, respect user config)
- **Option C**: Hybrid (quick edits in TUI, complex in external)
- **Decision Timeline**: M1 implementation
- **Current Thinking**: Start with B, add A in M2 if requested

**Q2: Local Model Support?**
- **Question**: Should we support local LLMs (Ollama, llama.cpp)?
- **Options**: Cloud-only vs. hybrid (cloud + local)
- **Decision Timeline**: M1 planning
- **Considerations**: Latency, context limits, model quality
- **Current Thinking**: Cloud-only for M1, add local in M2

### User Experience

**Q3: Approval Granularity?**
- **Current Design**: Multi-level (session, plan, changes, dangerous ops)
- **Question**: Is this too much friction?
- **Options**: Add "trust mode" per project or agent action type
- **Decision Timeline**: M1 after user testing
- **Current Thinking**: Keep strict for M1, add trust modes based on feedback

**Q4: Preset Layouts?**
- **Question**: What preset layouts should we ship?
- **Proposed**:
  - Chat-centric: Large chat, small side panels
  - Review-centric: Large diff view, small chat
  - Logs-centric: Large execution, minimal others
  - Balanced: Equal distribution
- **Decision Timeline**: M1 design
- **Current Thinking**: Ship 3-4 presets, allow custom layouts

### Infrastructure

**Q5: Session Persistence Strategy?**
- **Question**: How to persist sessions across restarts?
- **Options**:
  - A) SQLite database (like Elia)
  - B) YAML/TOML files in `~/.ztc/sessions/`
  - C) JSON files per session
- **Decision Timeline**: M1 implementation
- **Current Thinking**: Option A (SQLite) for queryability

**Q6: Audit Log Format?**
- **Question**: How detailed should audit logs be?
- **Considerations**: Privacy, debuggability, size
- **Proposed Format**:
  ```json
  {
    "timestamp": "2025-10-23T12:00:00Z",
    "session_id": "abc123",
    "action": "write_file",
    "details": {"file": "~/project/auth.py", "lines": 12},
    "outcome": "success"
  }
  ```
- **Decision Timeline**: M1 implementation
- **Current Thinking**: JSON lines format, rotated daily

### Distribution

**Q7: Primary Distribution Method?**
- **Options**:
  - PyPI (pip install)
  - PyInstaller binaries
  - Docker images
  - Homebrew/APT packages
- **Decision Timeline**: M3 planning
- **Current Thinking**: All of the above, but prioritize PyPI + binaries

**Q8: Auto-Update Mechanism?**
- **Question**: Should ZTC check for updates?
- **Options**:
  - A) No auto-update (manual pip upgrade)
  - B) Check on startup, notify user
  - C) Auto-download and prompt to restart
- **Decision Timeline**: M3 implementation
- **Current Thinking**: Option B (check + notify)

---

## Success Metrics

### User Experience Metrics

- **Time to first interaction**: < 5 seconds from launch
- **Response latency**: < 100ms for UI actions
- **Streaming delay**: < 50ms token appearance
- **Session switch time**: < 200ms

### Adoption Metrics

- **GitHub stars**: 1k+ in first month (if open source)
- **Active users**: 100+ weekly active users by M2
- **Session duration**: 30+ minutes average
- **Return rate**: 60%+ weekly return rate

### Quality Metrics

- **Uptime**: 99.9% for agent backend
- **Error rate**: < 1% of operations
- **Test coverage**: 80%+ for core components
- **Security audit**: Pass before v1.0 release

---

## Timeline & Phases

### Phase 1: Foundation (M0) - Weeks 1-3
- [x] Project setup and documentation
- [x] Textual skeleton with basic layout
- [ ] WebSocket client/server
- [ ] Streaming chat pane
- [ ] Basic event schema

### Phase 2: Core Features (M1) - Weeks 4-8
- [ ] Plan/review/approve workflow
- [ ] Diff viewer widget
- [ ] PTY execution pane
- [ ] File tree navigation
- [ ] Git integration

### Phase 3: Multiplexing & Remote (M2) - Weeks 9-13
- [ ] Session tabs
- [ ] Session comparison
- [ ] Remote workspace support
- [ ] SSH tunneling

### Phase 4: Polish & Distribution (M3) - Weeks 14-16
- [ ] PyPI packaging
- [ ] Binary builds
- [ ] Documentation
- [ ] Security audit

**Total Duration**: ~4 months to v1.0

---

**Last Updated**: October 23, 2025
**Next Review**: After M0 completion
