import ast
from pathlib import Path

from app.workspace.constants import IGNORE_DIRS


class ReferenceVisitor(ast.NodeVisitor):
    def __init__(self, file):
        self.file = file
        self.references = {}

    def visit_Name(self, node):

        self.references.setdefault(node.id, []).append(
            {
                "file": self.file,
                "line": node.lineno,
                "type": "name",
            }
        )

        self.generic_visit(node)

    def visit_Attribute(self, node):

        self.references.setdefault(node.attr, []).append(
            {
                "file": self.file,
                "line": node.lineno,
                "type": "attribute",
            }
        )

        self.generic_visit(node)

    def visit_Import(self, node):

        for alias in node.names:
            self.references.setdefault(alias.name, []).append(
                {
                    "file": self.file,
                    "line": node.lineno,
                    "type": "import",
                }
            )

        self.generic_visit(node)

    def visit_ImportFrom(self, node):

        for alias in node.names:
            self.references.setdefault(alias.name, []).append(
                {
                    "file": self.file,
                    "line": node.lineno,
                    "type": "import",
                }
            )

        self.generic_visit(node)


class ReferenceIndex:
    def build(self, workspace):

        root = Path(workspace)

        index = {}

        for file in root.rglob("*.py"):
            if any(part in IGNORE_DIRS for part in file.parts):
                continue

            relative = str(file.relative_to(root))

            source = file.read_text(encoding="utf-8")

            tree = ast.parse(source)

            visitor = ReferenceVisitor(relative)

            visitor.visit(tree)

            for symbol, refs in visitor.references.items():
                index.setdefault(symbol, []).extend(refs)

        return index

    def update_file(
        self,
        cache,
        path,
        workspace=".",
    ):

        root = Path(workspace)
        file = Path(path)

        if not file.is_absolute():
            file = root / file

        relative = str(file.relative_to(root))

        self.remove_file(cache, relative)

        source = file.read_text(encoding="utf-8")

        tree = ast.parse(source)

        visitor = ReferenceVisitor(relative)

        visitor.visit(tree)

        for symbol, refs in visitor.references.items():
            cache.setdefault(symbol, []).extend(refs)

    def remove_file(self, cache, path):

        for refs in cache.values():
            refs[:] = [r for r in refs if r["file"] != path]


reference_index = ReferenceIndex()
