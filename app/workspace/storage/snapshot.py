import json
from pathlib import Path


class WorkspaceSnapshot:
    FILE_NAME = ".workspace_snapshot.json"

    VERSION = 2

    def path(self, workspace):
        return Path(workspace) / self.FILE_NAME

    def save(self, data, workspace):

        payload = {
            "version": self.VERSION,
            "data": data,
        }

        self.path(workspace).write_text(json.dumps(payload, indent=2))

    def load(self, workspace):

        path = self.path(workspace)

        if not path.exists():
            return None

        payload = json.loads(path.read_text())

        if payload.get("version") != self.VERSION:
            return None

        return payload["data"]


workspace_snapshot = WorkspaceSnapshot()
