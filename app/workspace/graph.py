from pathlib import Path

from app.workspace.constants import IGNORE_DIRS
from app.workspace.parser import parse_python_file


class DependencyGraph:
    def build(self, workspace: str):

        root = Path(workspace)

        graph = {}
        reverse = {}

        for file in root.rglob("*.py"):
            if any(part in IGNORE_DIRS for part in file.parts):
                continue

            relative = str(file.relative_to(root))

            parsed = parse_python_file(str(file))

            graph[relative] = parsed["imports"]

            for imp in parsed["imports"]:
                reverse.setdefault(imp, []).append(relative)

        return {
            "imports": graph,
            "reverse": reverse,
        }


dependency_graph = DependencyGraph()
