from pathlib import Path

from app.workspace.constants import IGNORE_DIRS


SUPPORTED_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx"}
PYTHON_SUFFIXES = {".py"}


def is_supported_source(path: Path):
    return path.suffix.lower() in SUPPORTED_SUFFIXES


def iter_source_files(workspace: str):
    root = Path(workspace)

    for path in root.rglob("*"):
        if not path.is_file() or not is_supported_source(path):
            continue

        if any(part in IGNORE_DIRS for part in path.parts):
            continue

        yield path
