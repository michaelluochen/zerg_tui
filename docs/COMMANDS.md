# ZTC Command Reference

Complete reference for commands available in the Zerg Terminal Client.

## Command Types

ZTC handles commands in two ways:

### Client-Side Commands

These commands are intercepted and handled directly by ZTC, never reaching the Zerg service:

| Command | Description |
|---------|-------------|
| `init` | Re-initialize the Zerg agent connection |
| `update` | Request full agent state update |

### Server-Side Commands

All other input is sent to the Zerg service via the `zerg_command` Socket.IO event. The Zerg service interprets these commands based on its configuration.

## Available Zerg Service Commands

These commands are handled by the Zerg service. Availability depends on your Zerg configuration.

### Information & Query Commands

| Command | Description | Example Output |
|---------|-------------|----------------|
| `help` | List all available commands | Command list with descriptions |
| `help <command>` | Get help for specific command | Detailed command help |
| `list_actions` | Show available actions | List of actions in environment |
| `list_specs` | List all specifications | Specification list |
| `list_tests` | List all tests | Test list |
| `observe_environment` | Get current environment state | Environment observation |

### Execution Commands

| Command | Description |
|---------|-------------|
| `exec "<prompt>"` | Execute natural language prompt with AI |
| `execute_zerg` | Execute all specs and tests |
| `execute_specs` | Execute all specifications |
| `execute_tests` | Execute all tests |
| `execute_spec <idx>` | Execute specific spec by index |
| `execute_test <idx>` | Execute specific test by index |

### Specification Management

| Command | Description |
|---------|-------------|
| `add_spec <description> <preconditions> <postconditions>` | Add new specification |
| `update_spec <spec_id> [params...]` | Update existing specification |
| `remove_spec <idx>` | Remove specification by index |
| `run_spec <idx>` | Run spec without iteration |

### Test Management

| Command | Description |
|---------|-------------|
| `update_test <test_id> [params...]` | Update existing test |
| `run_test <idx>` | Run test without iteration |

### Memory & World Model

| Command | Description |
|---------|-------------|
| `memorize <memory>` | Add information to agent memory |
| `remember <query>` | Query agent memory |
| `predict_action <action>` | Predict world state after action |
| `update_world <observation>` | Update world model with observation |

### Environment Commands

| Command | Description |
|---------|-------------|
| `run_processes` | Run all environmental processes |
| `add_url <url>` | Add URL to workspace |

### Program Management

| Command | Description |
|---------|-------------|
| `load_programs <yaml_path>` | Load programs from YAML file |

## Command Examples

### Getting Started

**1. See what commands are available:**
```
help
```

**2. List available actions:**
```
list_actions
```

**3. Observe the environment:**
```
observe_environment
```

### Working with Specs and Tests

**List specifications:**
```
list_specs
```

**Add a new specification:**
```
add_spec "Function should return even numbers" "input is list" "output contains only even numbers"
```

**Execute all specs:**
```
execute_specs
```

### Using Natural Language (exec)

**Ask a question:**
```
exec "What files are in the current directory?"
```

**Request code generation:**
```
exec "Write a function that calculates fibonacci numbers"
```

**Get explanations:**
```
exec "Explain what the main.py file does"
```

### Memory Operations

**Add to memory:**
```
memorize "The user prefers async/await patterns"
```

**Query memory:**
```
remember "user preferences"
```

## How Commands Are Processed

### Flow Diagram

```
User types in ZTC input box
        ↓
┌───────────────────────┐
│  Is it "init"?        │  YES → client.initialize_zerg()
└───────────────────────┘
        ↓ NO
┌───────────────────────┐
│  Is it "update"?      │  YES → client.update_zerg()
└───────────────────────┘
        ↓ NO
┌───────────────────────┐
│  Send to Zerg service │ → emit('zerg_command', {command: "..."})
└───────────────────────┘
        ↓
Zerg service interprets command
        ↓
┌───────────────────────────────────┐
│  Is it a recognized Zerg command? │
└───────────────────────────────────┘
        ↓ YES                    ↓ NO
   Execute command          Log: "Unknown command"
        ↓                         ↓
   Return response          Return to stdout
        ↓                         ↓
   Events emitted           User sees error
        ↓
ZTC displays in appropriate pane
```

### Event Routing

**After a command is processed, events are routed to panes:**

| Event Type | Pane | Color |
|------------|------|-------|
| `zerg_output` | Chat | Green |
| `zerg_reasoning` | Chat | Yellow Italic |
| `zerg_error` | Chat | Bold Red |
| `zerg_warning` | Chat | Bold Yellow |
| `stdout` | Execution | White |
| `stderr` | Execution | Red |

## Common Patterns

### Quick Status Check

```
1. help              # See what's available
2. list_actions      # Check actions
3. observe_environment  # Check environment
```

### AI-Powered Workflow

```
1. exec "Analyze the current codebase"
2. exec "Suggest improvements"
3. exec "Write tests for main.py"
```

### Spec-Driven Development

```
1. add_spec "..." "..." "..."    # Define specification
2. execute_spec 0                # Run the spec
3. list_tests                    # See generated tests
4. execute_test 0                # Run a test
```

## Troubleshooting

### "Unknown command: <text>"

**Problem**: Zerg service doesn't recognize the command

**Solutions**:
1. Type `help` to see available commands
2. Check spelling (commands are case-sensitive)
3. Verify Zerg service is properly configured
4. Try simpler commands first: `help`, `list_actions`

### No response to command

**Problem**: Command sent but no output appears

**Solutions**:
1. Check Execution Pane for stdout/stderr
2. Some commands produce no output
3. Wait a moment - some commands are async
4. Type `update` to force a state refresh

### Command works in reference client but not ZTC

**Problem**: Command format difference

**Solution**:
- Reference client may have different parsing
- ZTC sends commands exactly as typed
- Verify command syntax is correct for Zerg service version

## Advanced Usage

### Chaining Commands

Commands execute sequentially. You can send multiple commands by typing them one at a time:

```
1. list_specs
   (wait for response)
2. execute_spec 0
   (wait for execution)
3. list_tests
```

### Using exec for Complex Tasks

The `exec` command passes the entire prompt to the LLM:

```
exec "Read the main.py file, understand what it does, and write comprehensive unit tests for all functions"
```

### Checking Agent State

```
update              # Request full state update
observe_environment # Get environment observation
list_actions        # See what actions are available
```

## Command Development

### Testing Commands

When developing new Zerg commands, test them using:

1. **ZTC directly** - Type command in chat
2. **Integration tests** - Use `MockZergServer` to simulate
3. **Reference client** - Compare behavior with reference implementation

### Adding Custom Commands

To add custom commands to ZTC:

1. **Client-side** (handled by ZTC):
   - Edit `ztc/main.py` `send_command()` method
   - Add new `if` condition for your command
   - Implement handler

2. **Server-side** (handled by Zerg service):
   - Implement in Zerg service
   - ZTC will automatically support it
   - No changes needed to ZTC client

## Command Reference by Category

### Essential Commands
- `help` - Start here
- `list_actions` - See what's possible
- `observe_environment` - Check state

### Development Commands
- `list_specs`, `list_tests` - View specifications/tests
- `execute_specs`, `execute_tests` - Run verification
- `add_spec`, `update_spec` - Manage specifications

### AI Commands
- `exec "<prompt>"` - Natural language tasks
- `memorize`, `remember` - Memory operations

### State Management
- `init` (ZTC) - Reinitialize agent
- `update` (ZTC) - Force state refresh
- `update_world` - Update world model

---

**For usage guide, see [README.md](../README.md)**
**For architecture details, see [PROJECT_VISION.md](PROJECT_VISION.md)**
