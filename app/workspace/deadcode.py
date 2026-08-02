import ast
from pathlib import Path

from app.workspace.constants import IGNORE_DEADCODE


class DeadCodeAnalyzer:
    def _is_endpoint(self, path, line):

        tree = ast.parse(Path(path).read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if not hasattr(node, "decorator_list"):
                continue

            if getattr(node, "lineno", None) != line:
                continue

            for dec in node.decorator_list:
                if (
                    isinstance(dec, ast.Call)
                    and isinstance(dec.func, ast.Attribute)
                    and dec.func.attr
                    in (
                        "get",
                        "post",
                        "put",
                        "delete",
                        "patch",
                    )
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

            dead.append(
                {
                    "symbol": name,
                    "file": path,
                    "line": info["start_line"],
                }
            )

        return sorted(dead, key=lambda x: x["symbol"])


deadcode_analyzer = DeadCodeAnalyzer()
