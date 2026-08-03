from pathlib import Path

from app.workspace.languages import iter_source_files
from app.workspace.parser import parse_source_file


class DependencyGraph:
    def build(self, workspace: str):

        root = Path(workspace)

        graph = {}
        reverse = {}

        for file in iter_source_files(workspace):

            relative = str(file.relative_to(root))

            parsed = parse_source_file(str(file))

            graph[relative] = parsed["imports"]

            for imp in parsed["imports"]:
                reverse.setdefault(imp, []).append(relative)

        return {
            "imports": graph,
            "reverse": reverse,
        }


dependency_graph = DependencyGraph()
