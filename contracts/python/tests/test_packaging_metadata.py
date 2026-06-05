"""Packaging-metadata guards for ``weaver_contracts`` (issue #85).

Keeps ``requires-python``, the trove ``classifiers``, and the supported-version
story in lockstep so the package can't claim a Python it doesn't test (or test a
Python it doesn't declare). Also asserts the library stays runtime-dependency
free, per the dependency policy in ``CONTRIBUTING.md``.
"""

import pathlib

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

PYPROJECT = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
PROJECT = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]

# The CPython minors the package promises to support. Keep in sync with the
# `python-tests` matrix in .github/workflows/ci.yml.
SUPPORTED_MINORS = (10, 11, 12, 13, 14)

_PY3_PREFIX = "Programming Language :: Python :: 3."


def _classifier_minors() -> set[int]:
    """Minor versions declared via ``Programming Language :: Python :: 3.X`` classifiers."""
    minors = set()
    for classifier in PROJECT["classifiers"]:
        if classifier.startswith(_PY3_PREFIX):
            tail = classifier[len(_PY3_PREFIX):]
            if tail.isdigit():
                minors.add(int(tail))
    return minors


def test_requires_python_floor_matches_lowest_supported() -> None:
    assert PROJECT["requires-python"] == f">=3.{min(SUPPORTED_MINORS)}"


def test_requires_python_has_no_upper_cap() -> None:
    # Library dependency policy: lower bound only, never a cap.
    assert "<" not in PROJECT["requires-python"]


def test_classifiers_cover_exactly_supported_minors() -> None:
    assert _classifier_minors() == set(SUPPORTED_MINORS)


def test_library_has_no_runtime_dependencies() -> None:
    # weaver_contracts is stdlib-only at runtime (CONTRIBUTING.md policy).
    assert PROJECT["dependencies"] == []
