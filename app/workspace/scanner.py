from pathlib import Path
from app.workspace.constants import IGNORE_DIRS

def scan_workspace(workspace: str):
    root = Path(workspace)

    files = []

    for path in root.rglob("*"):

        if not path.is_file():
            continue

        if any(part in IGNORE_DIRS for part in path.parts):
            continue

        files.append(str(path.relative_to(root)))

    return sorted(files)
