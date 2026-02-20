"""Unit tests for mpy analysis executable line detection.

These tests verify that get_executable_lines() correctly identifies
all executable lines including function/class entry points and first
lines of function bodies. Only requires mpy-cross (installed as a
dependency), no micropython binary needed.
"""

import os
import tempfile

import pytest

from mpy_coverage.mpy_analysis import get_executable_lines


@pytest.fixture
def tmp_py_file():
    """Create a temporary .py file, yield its path, clean up after."""
    files = []

    def _make(content):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=tempfile.gettempdir()
        )
        f.write(content)
        f.close()
        files.append(f.name)
        return f.name

    yield _make

    for path in files:
        if os.path.exists(path):
            os.unlink(path)


class TestDefAndClassLines:
    """Verify def/class statement lines are included in executable set."""

    def test_simple_functions(self, tmp_py_file):
        path = tmp_py_file(
            "def add(a, b):\n"  # line 1 — def
            "    return a + b\n"  # line 2 — body
            "\n"
            "def subtract(a, b):\n"  # line 4 — def
            "    return a - b\n"  # line 5 — body
        )
        result = get_executable_lines([path])
        lines = result[path]
        assert 1 in lines, "def add() line missing"
        assert 2 in lines, "return a + b line missing"
        assert 4 in lines, "def subtract() line missing"
        assert 5 in lines, "return a - b line missing"
        assert len(lines) == 4

    def test_class_with_methods(self, tmp_py_file):
        path = tmp_py_file(
            "class Calc:\n"  # line 1 — class
            "    def add(self, a, b):\n"  # line 2 — def
            "        return a + b\n"  # line 3 — body
            "\n"
            "    def sub(self, a, b):\n"  # line 5 — def
            "        return a - b\n"  # line 6 — body
        )
        result = get_executable_lines([path])
        lines = result[path]
        assert 1 in lines, "class Calc line missing"
        assert 2 in lines, "def add() line missing"
        assert 3 in lines, "return a + b line missing"
        assert 5 in lines, "def sub() line missing"
        assert 6 in lines, "return a - b line missing"

    def test_nested_functions(self, tmp_py_file):
        path = tmp_py_file(
            "def outer():\n"  # line 1 — def
            "    x = 1\n"  # line 2 — body
            "    def inner():\n"  # line 3 — def
            "        return x\n"  # line 4 — body
            "    return inner()\n"  # line 5 — body
        )
        result = get_executable_lines([path])
        lines = result[path]
        assert 1 in lines, "def outer() line missing"
        assert 2 in lines, "x = 1 line missing"
        assert 3 in lines, "def inner() line missing"
        assert 4 in lines, "return x line missing"
        assert 5 in lines, "return inner() line missing"


class TestFunctionBodyFirstLine:
    """Verify first line of function bodies is not dropped (bc_increment=0 bug)."""

    def test_single_line_function(self, tmp_py_file):
        path = tmp_py_file("def f():\n    return 42\n")
        result = get_executable_lines([path])
        lines = result[path]
        assert 2 in lines, "first (only) line of function body missing"

    def test_multiline_function(self, tmp_py_file):
        path = tmp_py_file(
            "def f(x):\n"
            "    a = x + 1\n"  # line 2 — first body line
            "    b = a * 2\n"  # line 3
            "    return b\n"  # line 4
        )
        result = get_executable_lines([path])
        lines = result[path]
        assert 2 in lines, "first line of function body missing"
        assert 3 in lines
        assert 4 in lines

    def test_module_level_and_function(self, tmp_py_file):
        """Module-level code and function body lines all present."""
        path = tmp_py_file(
            "X = 1\n"  # line 1 — module level
            "Y = 2\n"  # line 2 — module level
            "\n"
            "def f():\n"  # line 4 — def
            "    return X + Y\n"  # line 5 — first body line
        )
        result = get_executable_lines([path])
        lines = result[path]
        assert 1 in lines, "module-level X = 1 missing"
        assert 2 in lines, "module-level Y = 2 missing"
        assert 4 in lines, "def f() missing"
        assert 5 in lines, "first line of f() body missing"
