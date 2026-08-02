import json
from pathlib import Path


class WorkspaceSnapshot:
    FILE = Path(".workspace_snapshot.json")

    VERSION = 1

    def save(self, data):

        payload = {
            "version": self.VERSION,
            "data": data,
        }

        self.FILE.write_text(json.dumps(payload, indent=2))

    def load(self):

        if not self.FILE.exists():
            return None

        payload = json.loads(self.FILE.read_text())

        if payload.get("version") != self.VERSION:
            return None

        return payload["data"]


workspace_snapshot = WorkspaceSnapshot()
