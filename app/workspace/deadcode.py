import ast
from pathlib import Path

from app.workspace.constants import IGNORE_DEADCODE


class DeadCodeAnalyzer:

    def _is_endpoint(self, file, line):

        tree = ast.parse(Path(file).read_text())

        for node in ast.walk(tree):

            if not isinstance(node, ast.FunctionDef):
                continue

            if node.lineno != line:
                continue

            for dec in node.decorator_list:

                if isinstance(dec, ast.Call):

                    if isinstance(dec.func, ast.Attribute):

                        if dec.func.attr in (
                            "get",
                            "post",
                            "put",
                            "delete",
                            "patch",
                        ):
                            return True

        return False

    def analyze(self, symbols, reverse_graph):

        dead = []

        for name, info in symbols.items():

            if info["type"] not in ("function", "method"):
                continue

            short = name.split(".")[-1]

            if short in IGNORE_DEADCODE:
                continue

            if short.startswith("visit_"):
                continue

            if reverse_graph.get(name):
                continue

            path = info["file"]

            if self._is_endpoint(path, info["start_line"]):
                continue

            dead.append({
                "symbol": name,
                "file": path,
                "line": info["start_line"],
            })

        return sorted(dead, key=lambda x: x["symbol"])


deadcode_analyzer = DeadCodeAnalyzer()
