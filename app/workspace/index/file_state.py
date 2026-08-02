from pathlib import Path

IGNORE = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}


class FileState:
    def scan(self, workspace):

        result = {}

        for f in Path(workspace).rglob("*.py"):
            if any(part in IGNORE for part in f.parts):
                continue

            result[str(f)] = f.stat().st_mtime_ns

        return result

    def changed(self, old_state, workspace):

        new_state = self.scan(workspace)

        changed = []

        for file, mtime in new_state.items():
            if old_state.get(file) != mtime:
                changed.append(file)

        removed = [file for file in old_state if file not in new_state]

        return {
            "changed": sorted(changed),
            "removed": sorted(removed),
            "state": new_state,
        }


file_state = FileState()
