from pathlib import Path

from app.workspace.languages import iter_source_files


class FileState:
    def scan(self, workspace):

        root = Path(workspace)
        result = {}

        for f in iter_source_files(workspace):

            result[str(f.relative_to(root))] = f.stat().st_mtime_ns

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
