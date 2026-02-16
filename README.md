# mpy-coverage

Split-architecture code coverage for MicroPython: a lightweight on-device tracer paired with host-side reporting via coverage.py.

## Installation

```bash
pip install mpy-coverage
```

Or for development:
```bash
git clone git@github.com:andrewleech/mpy-coverage.git
cd mpy-coverage
pip install -e .
```

## Prerequisites

**MicroPython binary** (for unix-port testing):
```bash
cd ports/unix && make submodules && make VARIANT=coverage
```

**mpy-cross** (for the `mpy` analysis method):
```bash
cd mpy-cross && make
```

**Hardware targets:** firmware must be built with `MICROPY_PY_SYS_SETTRACE=1`.

## Quick Start (CLI)

Each test run stores a timestamped JSON file; the report command merges all collected data.

```bash
# Collect coverage for individual tests
mpy-coverage run test_foo.py --include myapp
mpy-coverage run test_bar.py --include myapp

# Generate merged report
mpy-coverage report --method auto --show-missing

# List collected data files
mpy-coverage list

# Remove collected data
mpy-coverage clean
```

The micropython binary is auto-detected from PATH or `ports/unix/build-coverage/micropython` relative to CWD. Override with `--micropython`.

Also runnable as `python -m mpy_coverage`.

### Hardware targets

```bash
# Auto-deploys tracer to device, runs test, collects data
mpy-coverage run test_foo.py \
    --device /dev/serial/by-id/usb-... \
    --include myapp

# Skip auto-deploy if mpy_coverage.py is already on device
mpy-coverage run test_foo.py \
    --device /dev/serial/by-id/usb-... \
    --no-deploy --include myapp
```

### Multi-pass workflow

```bash
mpy-coverage run tests/test_network.py --include myapp
mpy-coverage run tests/test_storage.py --include myapp
mpy-coverage run tests/test_ui.py --include myapp

# Report merges all .json files from the data directory
mpy-coverage report --show-missing --format html --output-dir htmlcov
```

Data files are stored in `.mpy_coverage/` by default (override with `--data-dir`).

## Manual API

For direct control over the tracer without the CLI wrapper:

```python
# On MicroPython (unix coverage variant or settrace-enabled firmware)
import mpy_coverage

mpy_coverage.start(include=['myapp'], collect_executable=True)
import myapp
myapp.main()
mpy_coverage.stop()
mpy_coverage.export_json('coverage.json')
```

```bash
# On host
python -m mpy_coverage.report coverage.json --method co_lines --show-missing
```

## Executable Line Detection Methods

| Method | Where | Pros | Cons |
|--------|-------|------|------|
| `co_lines` | On-device | No host tools needed, exact MicroPython view | Only sees called functions |
| `ast` | Host CPython | Sees all code, matches coverage.py conventions | May differ from MicroPython's view |
| `mpy` | Host via mpy-cross | Exact MicroPython bytecode view, sees all code | Requires mpy-cross binary |

Use `--method auto` (default) which uses `mpy` — the most accurate method for MicroPython since it reflects the actual bytecode the VM executes.

## On-Device Tracer API

```python
import mpy_coverage

# Functional API
mpy_coverage.start(include=['mymod'], exclude=['test_'], collect_executable=False)
# ... run code ...
mpy_coverage.stop()
data = mpy_coverage.get_data()
mpy_coverage.export_json('out.json')    # to file
mpy_coverage.export_json()              # to stdout with serial delimiters

# Context manager
with mpy_coverage.coverage(include=['mymod'], collect_executable=True):
    import mymod
    mymod.run()
```

Filtering uses substring matching on filenames. `mpy_coverage` itself is always excluded.

## JSON Data Format

```json
{
  "executed": {
    "filename.py": [1, 3, 5, 7]
  },
  "executable": {
    "filename.py": [1, 2, 3, 5, 6, 7, 10]
  }
}
```

`executable` is only present when `collect_executable=True` was used.

## Limitations

- **settrace overhead:** tracing adds significant runtime cost; not suitable for timing-sensitive code
- **co_lines incompleteness:** only reports executable lines for functions that were entered; uncalled functions are invisible rather than showing 0%
- **bytecode only:** native/viper functions are not traced by settrace
- **memory on constrained devices:** large `_executed` dicts may hit memory limits on small targets
- **coverage.py private API:** the report integration overrides `Coverage._get_file_reporter()` which may change across coverage.py versions
