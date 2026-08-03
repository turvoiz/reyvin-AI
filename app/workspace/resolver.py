import ast
from pathlib import Path

from app.workspace.constants import IGNORE_DIRS
from app.workspace.symbols import build_symbol_index


class SymbolResolver(ast.NodeVisitor):
    def __init__(self, file, classes):
        self.file = file
        self.classes = classes
        self.instances = {}

    def visit_Assign(self, node):

        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            class_name = node.value.func.id

            if class_name in self.classes:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.instances[target.id] = {
                            "type": "instance",
                            "class": class_name,
                            "file": self.file,
                            "line": node.lineno,
                        }

        self.generic_visit(node)


class ResolverIndex:
    def build(self, workspace):

        root = Path(workspace)

        symbols = build_symbol_index(workspace)

        classes = {
            name for name, symbol in symbols.items() if symbol["type"] == "class"
        }

        index = {}

        for file in root.rglob("*.py"):
            if any(part in IGNORE_DIRS for part in file.parts):
                continue

            relative = str(file.relative_to(root))

            source = file.read_text(encoding="utf-8")

            tree = ast.parse(source)

            visitor = SymbolResolver(relative, classes)

            visitor.visit(tree)

            index.update(visitor.instances)

        return index


resolver_index = ResolverIndex()
