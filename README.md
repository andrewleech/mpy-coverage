# mpy-coverage

Code coverage for MicroPython. Lightweight on-device tracer using `sys.settrace`, with host-side reporting via coverage.py.

The tracer runs on the MicroPython target (unix port or real hardware with settrace enabled), collects executed line data, and exports it as JSON. The host-side tooling then merges multiple runs and generates reports using coverage.py's reporting engine.

## Install

```bash
pip install mpy-coverage
```

This pulls in `coverage` and `mpy-cross` automatically.

Dev setup:
```bash
git clone git@github.com:andrewleech/mpy-coverage.git
cd mpy-coverage
uv sync
```

## Getting started

You need a micropython binary with settrace support. The quickest way is the unix coverage variant:
```bash
cd ports/unix && make submodules && make VARIANT=coverage
```

Say you have a module `myapp.py` and a test script `test_myapp.py` that exercises it:

```python
# test_myapp.py
import myapp
myapp.run()
```

Collect coverage and generate a report:
```bash
mpy-coverage run test_myapp.py --include myapp --show-missing
mpy-coverage report --show-missing
```

That's it. The run command executes `test_myapp.py` under micropython with the tracer active, saves a JSON data file to `.mpy_coverage/`, and the report command reads it and prints a coverage summary.

For an HTML report instead:
```bash
mpy-coverage report --format html --output-dir htmlcov
```

If you have multiple test files, run each one separately then generate a single merged report:
```bash
mpy-coverage run tests/test_network.py --include myapp
mpy-coverage run tests/test_storage.py --include myapp
mpy-coverage report --show-missing
```

## Prerequisites

For unix-port testing you need a micropython coverage build:
```bash
cd ports/unix && make submodules && make VARIANT=coverage
```

Hardware targets need firmware built with `MICROPY_PY_SYS_SETTRACE=1`.

## Usage

Each test run stores a timestamped JSON file, the report command merges all collected data.

```bash
mpy-coverage run test_foo.py --include myapp
mpy-coverage run test_bar.py --include myapp
mpy-coverage report --method auto --show-missing
```

micropython binary is auto-detected from PATH or `ports/unix/build-coverage/micropython` relative to CWD. Override with `--micropython`. Also works as `python -m mpy_coverage`.

### Hardware

```bash
# deploys tracer to device automatically, runs test, collects data
mpy-coverage run test_foo.py --device /dev/serial/by-id/usb-... --include myapp

# skip deploy if mpy_coverage.py is already on device
mpy-coverage run test_foo.py --device /dev/serial/by-id/usb-... --no-deploy --include myapp
```

### Multi-pass

Run tests separately, accumulate data, generate one merged report:
```bash
mpy-coverage run tests/test_network.py --include myapp
mpy-coverage run tests/test_storage.py --include myapp
mpy-coverage run tests/test_ui.py --include myapp
mpy-coverage report --show-missing --format html --output-dir htmlcov
```

Data stored in `.mpy_coverage/` by default, override with `--data-dir`.

Other subcommands: `mpy-coverage list` and `mpy-coverage clean`.

## Branch coverage

Collect arc (branch) data during runs and generate branch-aware reports:

```bash
mpy-coverage run test_myapp.py --include myapp --branch
mpy-coverage report --show-missing --branch
```

The `--branch` flag on `run` enables arc collection in the tracer. The `--branch` flag on `report` activates branch columns (Branch, BrPart) in the output. If `--branch` is passed to `report` but no arc data is present, it falls back to line-only mode with a warning.

## Test map

Show which tests cover which application files:

```bash
mpy-coverage run tests/test_a.py --include myapp
mpy-coverage run tests/test_b.py --include myapp
mpy-coverage test-map
```

Output:
```
app_file    , test
myapp.py    , test_a
myapp.py    , test_b
helpers.py  , test_a
```

For per-line detail:
```bash
mpy-coverage test-map --line-detail
```

Output:
```
app_file    , line, test
myapp.py    , 1   , test_a
myapp.py    , 1   , test_b
myapp.py    , 5   , test_a
```

Test names are extracted from `_metadata.test_script` in the JSON (set automatically by the CLI), with a filename-based fallback for older data files.

## Tracer API

For direct use without the CLI wrapper. This runs on the MicroPython device, not the host.

```python
import mpy_coverage

mpy_coverage.start(include=['myapp'], collect_executable=True)
import myapp
myapp.main()
mpy_coverage.stop()
mpy_coverage.export_json('coverage.json')  # to file
mpy_coverage.export_json()                 # to stdout with delimiters
```

With branch coverage and test metadata:
```python
mpy_coverage.start(include=['myapp'], collect_arcs=True, test_script='test_myapp')
```

Context manager form:
```python
with mpy_coverage.coverage(include=['mymod'], collect_executable=True):
    import mymod
    mymod.run()
```

Filtering is substring matching on filenames. The tracer always excludes itself.

Then on the host:
```bash
python -m mpy_coverage.report coverage.json --method co_lines --show-missing
```

## Executable line detection

Three methods for determining which lines are executable:

| Method | Runs on | Notes |
|--------|---------|-------|
| `co_lines` | Device | No host tools needed, but only sees lines in functions that were actually called |
| `ast` | Host (CPython) | Sees all code, may disagree with MicroPython's grammar on edge cases |
| `mpy` | Host (mpy-cross) | Most accurate -- reflects actual MicroPython bytecode, sees all code |

`--method auto` (default) uses `mpy`.

## JSON format

```json
{
  "_metadata": {"test_script": "test_myapp"},
  "executed": {"filename.py": [1, 3, 5, 7]},
  "executable": {"filename.py": [1, 2, 3, 5, 6, 7, 10]},
  "arcs": {"filename.py": [[-1, 1], [1, 3], [3, 5], [5, -1]]}
}
```

- `executable` key only present when `collect_executable=True`
- `arcs` key only present when `collect_arcs=True` (or `--branch` on CLI)
- `_metadata` key only present when `test_script` is set (automatic via CLI)

## Limitations

- settrace adds significant runtime overhead, not suitable for timing-sensitive code
- `co_lines` method only reports executable lines for functions that were entered, uncalled functions are invisible rather than showing 0%
- native/viper functions are not traced by settrace
- large `_executed` dicts may hit memory limits on constrained devices
- report integration overrides `Coverage._get_file_reporter()` which is a private API and may change across coverage.py versions
