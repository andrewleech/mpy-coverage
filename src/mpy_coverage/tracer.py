# MicroPython settrace-based code coverage tracer

import sys
import json

_executed = {}
_executable = {}
_include = None
_exclude = None
_collect_executable = False
_seen_codes = set()


def _should_trace(filename):
    if "mpy_coverage" in filename:
        return False
    if _include is not None:
        if not any(pattern in filename for pattern in _include):
            return False
    if _exclude is not None:
        if any(pattern in filename for pattern in _exclude):
            return False
    return True


def _local_trace(frame, event, arg):
    if event == "line":
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        if filename not in _executed:
            _executed[filename] = set()
        _executed[filename].add(lineno)
    return _local_trace


def _global_trace(frame, event, arg):
    if event == "call":
        filename = frame.f_code.co_filename
        if not _should_trace(filename):
            return None

        if _collect_executable:
            code_id = id(frame.f_code)
            if code_id not in _seen_codes:
                _seen_codes.add(code_id)
                if filename not in _executable:
                    _executable[filename] = set()
                try:
                    for start, end, line_no in frame.f_code.co_lines():
                        if line_no > 0:
                            _executable[filename].add(line_no)
                except (AttributeError, TypeError):
                    pass

        return _local_trace
    return None


def start(include=None, exclude=None, collect_executable=False):
    global _include, _exclude, _collect_executable
    _executed.clear()
    _executable.clear()
    _seen_codes.clear()
    _include = include
    _exclude = exclude
    _collect_executable = collect_executable
    sys.settrace(_global_trace)


def stop():
    sys.settrace(None)


def get_data():
    data = {"executed": {}}
    for filename, lines in _executed.items():
        data["executed"][filename] = sorted(list(lines))
    if _collect_executable:
        data["executable"] = {}
        for filename, lines in _executable.items():
            data["executable"][filename] = sorted(list(lines))
    return data


def export_json(path=None):
    data = get_data()
    json_str = json.dumps(data)
    if path is None:
        print("---MPY_COV_START---")
        print(json_str)
        print("---MPY_COV_END---")
    else:
        with open(path, "w") as f:
            f.write(json_str)
            f.write("\n")


class coverage:
    def __init__(self, include=None, exclude=None, collect_executable=False):
        self.include = include
        self.exclude = exclude
        self.collect_executable = collect_executable

    def __enter__(self):
        start(self.include, self.exclude, self.collect_executable)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        stop()
