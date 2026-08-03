from pathlib import Path

from app.workspace.cache import WorkspaceCache, workspace_cache


class WorkspaceRegistry:
    def __init__(self):
        self._projects = {"default": workspace_cache}

    def register(self, project_id, workspace):
        if not project_id or not project_id.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Project ID may contain only letters, numbers, '-' and '_'")

        path = Path(workspace).expanduser().resolve()

        if not path.is_dir():
            raise ValueError("Workspace path must be an existing directory")

        cache = WorkspaceCache()
        cache.load(str(path))
        self._projects[project_id] = cache

        return self.describe(project_id)

    def get(self, project_id="default"):
        try:
            return self._projects[project_id]
        except KeyError as error:
            raise KeyError(f"Workspace project '{project_id}' was not found") from error

    def describe(self, project_id):
        cache = self.get(project_id)

        return {
            "project_id": project_id,
            "workspace": cache.workspace,
            "symbols": len(cache.symbols()),
        }

    def list(self):
        return [self.describe(project_id) for project_id in sorted(self._projects)]


workspace_registry = WorkspaceRegistry()
