# ZTC Testing Guide

This directory contains the test suite for ZTC (Zerg Terminal Client).

## Table of Contents
- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Mock Server](#mock-server)
- [Coverage](#coverage)
- [Best Practices](#best-practices)

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=ztc --cov-report=html

# Run only unit tests (fast)
pytest tests/unit

# Run only integration tests
pytest tests/integration

# Run a specific test file
pytest tests/unit/test_client.py

# Run tests matching a pattern
pytest -k "test_connect"
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared pytest fixtures
├── unit/                    # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_client.py       # ZergClient tests (23 tests)
│   └── test_widgets.py      # Widget tests (27 tests)
├── integration/             # Integration tests (with mock server)
│   ├── __init__.py
│   └── test_full_flow.py    # End-to-end flow tests (8 tests)
└── fixtures/                # Test fixtures and utilities
    ├── __init__.py
    └── mock_server.py       # Mock Zerg Socket.IO server
```

### Test Categories

Tests are organized by scope and marked with pytest markers:

- **Unit tests** (`@pytest.mark.unit`): Fast, isolated tests of individual components
  - No external dependencies
  - Use mocks for Socket.IO, file system, etc.
  - Run in < 100ms each
  - **23 tests** in test_client.py, **27 tests** in test_widgets.py

- **Integration tests** (`@pytest.mark.integration`): Tests with mock server
  - Use `MockZergServer` for realistic Socket.IO interactions
  - Test full client/server communication
  - May take 1-5 seconds
  - **8 tests** in test_full_flow.py

- **Slow tests** (`@pytest.mark.slow`): Tests that take > 1 second
  - Usually integration tests or stress tests
  - Run separately in CI with `pytest -m slow`

## Running Tests

### Basic Commands

```bash
# All tests with default settings (includes coverage)
pytest

# Specific test directory
pytest tests/unit
pytest tests/integration

# Specific test file
pytest tests/unit/test_client.py

# Specific test class
pytest tests/unit/test_client.py::TestZergClientConnection

# Specific test function
pytest tests/unit/test_client.py::TestZergClientConnection::test_successful_connection

# Filter by marker
pytest -m unit              # Only unit tests
pytest -m integration       # Only integration tests
pytest -m "not slow"        # Skip slow tests
```

### Coverage Options

```bash
# Run with coverage (default in pyproject.toml)
pytest

# Coverage with HTML report
pytest --cov=ztc --cov-report=html
# Then open htmlcov/index.html in browser

# Coverage with terminal report
pytest --cov=ztc --cov-report=term-missing

# No coverage (faster for development)
pytest --no-cov
```

### Debugging Tests

```bash
# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Enter debugger on failure
pytest --pdb

# Verbose output
pytest -v

# Very verbose (show test output)
pytest -vv

# Run only last failed tests
pytest --lf

# See which tests will run without running them
pytest --collect-only
```

## Writing Tests

### Using Fixtures

The test suite provides several shared fixtures (see `conftest.py`):

#### mock_event_callback

A mock function for event callbacks.

```python
def test_event_handling(mock_event_callback):
    """Use in tests that need to verify callbacks."""
    client = ZergClient(url, event_callback=mock_event_callback)
    # ... trigger events ...
    mock_event_callback.assert_called_once_with('event_type', {'data': 'value'})
```

#### zerg_client

A ZergClient with mocked Socket.IO connection - ready for testing without a real server.

```python
@pytest.mark.asyncio
async def test_client_method(zerg_client):
    """Socket.IO methods are already mocked."""
    await zerg_client.connect()
    zerg_client.sio.connect.assert_called_once()
```

#### mock_zerg_client

Fully mocked ZergClient for TUI testing (all methods are AsyncMock).

```python
@pytest.mark.asyncio
async def test_tui_component(mock_zerg_client):
    """All client methods are mocked."""
    app = ZergTerminalClient()
    app.client = mock_zerg_client
    app.client.connected = True
    # Test TUI without real Socket.IO
```

#### ztc_app

A ZergTerminalClient app instance ready for testing.

```python
@pytest.mark.asyncio
async def test_app_startup(ztc_app):
    """Test app using run_test() for headless testing."""
    async with ztc_app.run_test() as pilot:
        assert ztc_app.query_one("#chat-pane") is not None
```

### Writing Unit Tests

Unit tests should be fast and isolated:

```python
import pytest
from unittest.mock import Mock, AsyncMock
from ztc.client import ZergClient

class TestZergClientConnection:
    """Group related tests in a class."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_successful_connection(self, zerg_client):
        """Test successful connection to Zerg service."""
        # Setup
        zerg_client.sio.connect = AsyncMock()

        # Execute
        await zerg_client.connect()

        # Verify
        zerg_client.sio.connect.assert_called_once_with("http://localhost:3333")
```

**Unit Test Patterns:**
- Use fixtures from `conftest.py`
- Mock all external dependencies
- Test one component at a time
- Fast execution (< 100ms)
- No real network I/O

### Writing Integration Tests

Integration tests use the mock server:

```python
import pytest
from tests.fixtures.mock_server import MockZergServer
from ztc.client import ZergClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_connection_flow(mock_server):
    """Test complete connection and initialization flow."""
    # mock_server fixture starts server automatically

    # Create real client pointing to mock server
    client = ZergClient("http://localhost:3334")

    # Test full interaction
    await client.connect()
    await client.initialize_zerg()
    await client.zerg_command("test command")

    # Verify behavior
    assert client.connected

    # Cleanup
    await client.disconnect()
```

**Integration Test Patterns:**
- Use `mock_server` fixture (auto-starts/stops)
- Test multiple components together
- Verify Socket.IO protocol
- Test realistic workflows
- May be slower (1-5 seconds)

### Async Test Patterns

All async tests must be marked with `@pytest.mark.asyncio`:

```python
import pytest

# Auto-mode is configured in pyproject.toml
@pytest.mark.asyncio
async def test_async_function():
    """Test any async function."""
    result = await some_async_operation()
    assert result is not None

# Async fixtures
@pytest.fixture
async def async_resource():
    """Async setup and teardown."""
    resource = await create_resource()
    yield resource
    await resource.close()
```

### Mocking Socket.IO

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_event_emission(zerg_client):
    """Test that client emits correct events."""
    # Mock the emit method
    zerg_client.sio.emit = AsyncMock()

    # Trigger action that emits event
    await zerg_client.zerg_command("test command")

    # Verify emission
    zerg_client.sio.emit.assert_called_once_with(
        'zerg_command',
        {'command': 'test command'}
    )
```

### Testing Textual Widgets

Use Textual's `run_test()` for headless TUI testing:

```python
from ztc.app import ZergTerminalClient

@pytest.mark.asyncio
async def test_widget_composition():
    """Test widget layout and composition."""
    app = ZergTerminalClient()

    async with app.run_test() as pilot:
        # Query widgets
        chat_pane = app.query_one("#chat-pane")
        assert chat_pane is not None

        # Interact with widgets
        input_widget = app.query_one("#chat-input")
        input_widget.value = "test message"
        await pilot.press("enter")

        # Wait for async processing
        await pilot.pause(0.1)
```

## Mock Server

### Overview

The `MockZergServer` class provides a realistic Socket.IO server for integration testing:

```python
from tests.fixtures.mock_server import MockZergServer

# Create and start server
server = MockZergServer(port=3334)  # Port 3334 avoids conflict with real Zerg
await server.start()

# Server is now listening on http://localhost:3334

# Clean up
await server.stop()
```

### Supported Events

The mock server handles these Socket.IO events:

**From Client:**
- `connect` - Client connection
- `disconnect` - Client disconnection
- `initialize_zerg` - Agent initialization
- `zerg_command` - Command execution
- `request_zerg_update` - State update request
- `upload_file` - File upload
- `request_file_download` - File download request
- `fetch_zerg_commands` - Command list request

**To Client:**
- `stdout` - Standard output
- `zerg_output` - Agent output messages
- `zerg_update` - Full agent state
- `download_file_response` - File download response

### Using with Fixtures

The `mock_server` fixture handles startup/shutdown automatically:

```python
@pytest.fixture
async def mock_server():
    """Provide a mock server for tests."""
    server = MockZergServer(port=3334)
    await server.start()
    await asyncio.sleep(0.2)  # Let server start
    yield server
    await server.stop()

# Use in tests
@pytest.mark.integration
async def test_with_server(mock_server):
    """mock_server is started and will auto-cleanup."""
    client = ZergClient("http://localhost:3334")
    await client.connect()
    # ... test logic ...
    await client.disconnect()
```

### Mock Server Features

- **Realistic responses**: Simulates actual Zerg behavior
- **File storage**: Stores uploaded files in memory
- **Client tracking**: Tracks connected clients
- **Simulated delays**: Adds realistic 50-100ms delays
- **Logging**: Logs all events for debugging
- **Clean lifecycle**: Proper startup/shutdown

### Testing Commands

To test specific Zerg commands in integration tests:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_help_command(mock_server):
    """Test the help command."""
    events_received = []

    def callback(event_type, data):
        events_received.append((event_type, data))

    client = ZergClient("http://localhost:3334", event_callback=callback)
    await client.connect()

    # Send help command
    await client.zerg_command("help")
    await asyncio.sleep(0.2)

    # Verify response
    output_events = [e for e in events_received if e[0] == "zerg_output"]
    assert len(output_events) > 0

    await client.disconnect()
```

**Common commands to test:**
- `help` - List all commands
- `list_actions` - List available actions
- `observe_environment` - Get environment state
- Custom commands your Zerg instance supports

**Note:** The mock server in `tests/fixtures/mock_server.py` provides basic responses. For testing actual command logic, you may need to enhance the mock server or test against a real Zerg instance.

## Coverage

### Current Coverage

**Overall: 72.54%**
- `ztc/__init__.py`: 100.00%
- `ztc/client.py`: 70.74%
- `ztc/main.py`: 73.91%

### Coverage Configuration

Coverage is configured in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["ztc"]
omit = ["tests/*", ".venv/*", "*/site-packages/*"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
]
precision = 2
```

### Viewing Coverage

```bash
# Terminal report (shows missing lines)
pytest --cov=ztc --cov-report=term-missing

# HTML report (interactive, recommended)
pytest --cov=ztc --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Both reports
pytest --cov=ztc --cov-report=term-missing --cov-report=html

# XML report (for CI/Codecov)
pytest --cov=ztc --cov-report=xml
```

### Coverage Goals

- **Target**: 80%+ overall coverage
- **Minimum**: 70% per file
- **Branch coverage**: Enabled (tests conditional paths)
- **Focus areas**: Error handling, edge cases

### Improving Coverage

To find untested code:

```bash
# Generate HTML report
pytest --cov=ztc --cov-report=html

# Open report and look for:
# - Red lines (not executed)
# - Yellow lines (partially covered branches)
# - Coverage % by file
```

Common untested areas:
- Error handling paths (raise exceptions)
- Edge cases (empty inputs, None values)
- Cleanup code (finally blocks)
- Logging statements

## Best Practices

### Test Naming Conventions

Follow pytest conventions:

- **Test files**: `test_*.py` (e.g., `test_client.py`)
- **Test classes**: `Test*` (e.g., `class TestZergClient:`)
- **Test functions**: `test_*` (e.g., `def test_connection():`)

Be descriptive - test names should explain what they test:

```python
# Good
def test_client_connect_handles_connection_error()

# Bad
def test_connect()
```

### Test Organization

Organize tests in classes by component or feature:

```python
class TestZergClientConnection:
    """Group all connection-related tests."""

    def test_successful_connection(self):
        """Test the happy path."""
        pass

    def test_connection_timeout(self):
        """Test timeout handling."""
        pass

    def test_connection_refused(self):
        """Test refused connection."""
        pass
```

### Arrange-Act-Assert Pattern

Structure tests clearly:

```python
@pytest.mark.asyncio
async def test_send_command(zerg_client):
    """Test sending a command to Zerg."""
    # Arrange - Set up test dependencies
    zerg_client.sio.emit = AsyncMock()
    command = "write hello world"

    # Act - Execute the code under test
    await zerg_client.zerg_command(command)

    # Assert - Verify expected outcomes
    zerg_client.sio.emit.assert_called_once_with(
        'zerg_command',
        {'command': command}
    )
```

### Assertions

Use specific, descriptive assertions:

```python
# Good - specific assertions
assert result == expected_value
assert result is not None
assert len(items) == 5
assert 'key' in dictionary

# Good - mock assertions
mock_func.assert_called_once()
mock_func.assert_called_with(arg1, arg2)
mock_func.assert_not_called()
assert mock_func.call_count == 3

# Good - error messages
assert result == expected, f"Expected {expected}, got {result}"

# Avoid - too generic
assert result  # What are we checking?
```

### Fixtures Best Practices

**Use fixtures for**:
- Common setup code
- Resource management (connection, files)
- Test data
- Mocks and stubs

**Good fixture**:
```python
@pytest.fixture
async def connected_client():
    """Provide a connected ZergClient."""
    client = ZergClient("http://localhost:3334")
    await client.connect()
    yield client
    # Cleanup
    await client.disconnect()

# Use in test
async def test_with_connected_client(connected_client):
    assert connected_client.connected is True
```

**Fixture scopes**:
- `function` (default) - New instance per test
- `class` - Shared within test class
- `module` - Shared within module
- `session` - Shared across all tests

### Parameterized Tests

Test multiple inputs with one test function:

```python
@pytest.mark.parametrize("event_type,expected_style", [
    ("zerg_output", "green"),
    ("zerg_error", "bold red"),
    ("zerg_warning", "bold yellow"),
])
def test_event_styling(event_type, expected_style):
    """Test that different event types have correct styling."""
    # Test with each parameter combination
    assert get_style(event_type) == expected_style
```

### Test Isolation

**Each test should be independent:**

```python
# Good - Independent
def test_channel_enable():
    client = ZergClient("http://localhost:3333")
    client.enable_channel('stdout')
    assert client.channels['stdout'] is True

def test_channel_disable():
    client = ZergClient("http://localhost:3333")  # Fresh client
    client.disable_channel('stdout')
    assert client.channels['stdout'] is False

# Bad - Tests depend on execution order
channel_client = ZergClient("http://localhost:3333")

def test_enable():
    channel_client.enable_channel('stdout')  # Shared state!
    assert channel_client.channels['stdout'] is True

def test_disable():
    channel_client.disable_channel('stdout')  # Depends on test_enable
    assert channel_client.channels['stdout'] is False
```

## Debugging Tips

### 1. Use Print Debugging

```bash
# See print statements in tests
pytest -s tests/unit/test_client.py

# Your test
def test_something():
    print(f"Debug: value is {value}")  # Will show with -s flag
    assert value == expected
```

### 2. Use Breakpoints

```python
def test_complex_logic():
    result = complex_calculation()

    import pdb; pdb.set_trace()  # Drop into debugger

    assert result == expected
```

Or use pytest's built-in debugger:

```bash
# Drop into pdb on first failure
pytest --pdb

# Drop into pdb on first failure, then exit
pytest --pdb -x
```

### 3. Inspect Failures

```bash
# Show local variables on failure
pytest -l

# Show full diff for assertion errors
pytest -vv

# Show captured output on failure
pytest --tb=short
pytest --tb=long
```

### 4. Run Specific Tests

```bash
# Run just the failing test
pytest tests/unit/test_client.py::TestZergClientConnection::test_connect

# Run last failed tests
pytest --lf

# Run failed tests first, then others
pytest --ff
```

### 5. Check Test Collection

```bash
# See what tests will run
pytest --collect-only

# See tests matching a pattern
pytest --collect-only -k "connection"
```

## CI Integration

Tests run automatically in GitHub Actions on:
- Push to `main` or `develop`
- Pull requests
- Manual workflow dispatch

### CI Workflow

```yaml
# .github/workflows/tests.yml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - name: Run unit tests
        run: pytest tests/unit --cov=ztc

      - name: Run integration tests
        run: pytest tests/integration --cov=ztc --cov-append
```

### CI Best Practices

- Run unit tests first (fast feedback)
- Run integration tests separately
- Generate coverage reports (XML for Codecov)
- Cache dependencies for speed
- Fail if coverage drops below threshold
- Run linters (ruff, black, mypy) in separate job

## Test Maintenance

### When Adding New Features

1. **Write tests first** (TDD approach):
   ```bash
   # Create test file
   touch tests/unit/test_new_feature.py

   # Write failing test
   # Implement feature
   # Test passes
   ```

2. **Update existing tests** if behavior changes

3. **Add integration tests** for new workflows

4. **Update coverage targets** if needed

### Keeping Tests Fast

- Use `@pytest.mark.slow` for slow tests
- Mock external dependencies
- Avoid `time.sleep()` (use `asyncio.sleep(0)`)
- Run slow tests separately in CI

### Refactoring Tests

When tests become complex:
- Extract common setup to fixtures
- Create helper functions for assertions
- Split large test classes
- Add docstrings explaining "why"

## Common Issues

### Tests Hang

**Symptom**: Test runs forever, no output

**Causes**:
- Waiting for Socket.IO event that never arrives
- Missing `await` on async function
- Deadlock in async code

**Fix**:
- Add timeout: `pytest --timeout=10`
- Check for missing `await`
- Add `await asyncio.sleep(0)` to yield control

### Mock Not Working

**Symptom**: Real code executes instead of mock

**Causes**:
- Mock applied too late
- Mocking wrong object
- Mock not in scope

**Fix**:
```python
# Use patch decorator
@patch('ztc.client.socketio.AsyncClient')
def test_with_patch(mock_sio):
    # Mock is applied before test runs
    pass

# Or patch as context manager
def test_with_context():
    with patch('ztc.client.socketio.AsyncClient') as mock_sio:
        # Mock active only in this block
        pass
```

### Fixture Not Found

**Symptom**: `fixture 'xyz' not found`

**Causes**:
- Fixture in wrong file
- Typo in fixture name
- Missing import

**Fix**:
- Check `conftest.py` for shared fixtures
- Check spelling
- Run `pytest --fixtures` to see available fixtures

### Async Warnings

**Symptom**: `RuntimeWarning: coroutine was never awaited`

**Cause**: Missing `await` keyword

**Fix**:
```python
# Bad
def test_async_without_await():
    result = async_function()  # Returns coroutine, not result

# Good
async def test_async_with_await():
    result = await async_function()  # Actually executes
```

---

## Test Coverage Summary

**Current Status**: 55 passed, 1 skipped | Coverage: 72.54%

### Test Files
- `tests/unit/test_client.py`: 23 tests, 289 lines
- `tests/unit/test_widgets.py`: 27 tests, 223 lines
- `tests/integration/test_full_flow.py`: 8 tests, 165 lines
- `tests/fixtures/mock_server.py`: Mock server, 206 lines
- `tests/conftest.py`: Shared fixtures, 55 lines

**Total**: 58 tests, ~940 lines of test code

### Next Testing Goals

1. Increase coverage to 80%+
2. Add property-based tests (hypothesis)
3. Add visual regression tests for TUI
4. Add performance benchmarks
5. Test error recovery paths
6. Test connection reconnection logic

---

For questions or issues with testing, please open an issue on GitHub or consult the [main README](../README.md).
