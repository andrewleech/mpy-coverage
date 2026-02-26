"""MicroPython code coverage toolchain."""

from mpy_coverage._version import __version__  # noqa: F401


def __getattr__(name):
    if name in ("merge_coverage_data", "run_report"):
        from mpy_coverage.report import merge_coverage_data, run_report

        return {"merge_coverage_data": merge_coverage_data, "run_report": run_report}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["merge_coverage_data", "run_report", "__version__"]
